"""Ilustrações geradas por IA, com o estilo fixo de cada canal.

Motores (na ordem de `ilustracoes.motores` em geral.yaml):
- flux:       Flux schnell rodando no Workers AI do seu Cloudflare, pelo worker do escritório.
              Grátis dentro da cota diária (10.000 neurons ≈ 150 imagens/dia).
- higgsfield: pago (pré-pago em dólar). Precisa dos segredos HF_API_KEY_ID e HF_API_KEY_SECRET.
Quando todos falham ou passam do teto, devolve None e o motor usa imagens livres (Wikimedia/Openverse).
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from pathlib import Path

import requests
import yaml

from .comum import RAIZ, log

GASTOS = RAIZ / "canais" / "gastos-imagens.json"
_trava = threading.Lock()


def _geral() -> dict:
    return yaml.safe_load((RAIZ / "pipeline" / "config" / "geral.yaml").read_text(encoding="utf-8"))


def _ler_gastos() -> dict:
    return json.loads(GASTOS.read_text(encoding="utf-8")) if GASTOS.exists() else {}


def _registrar(motor: str, periodo: str, campo: str, valor: float) -> None:
    with _trava:
        g = _ler_gastos()
        m = g.setdefault(motor, {}).setdefault(periodo, {"imagens": 0, campo: 0})
        m["imagens"] += 1
        m[campo] = round(m.get(campo, 0) + valor, 3)
        GASTOS.write_text(json.dumps(g, indent=2), encoding="utf-8")


class _Flux:
    nome = "flux"

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.url = cfg.get("url", "").rstrip("/") + "/api/imagem"
        pat = os.environ.get("GH_PAT", "")
        self.chave = os.environ.get("PAINEL_KEY") or (
            hashlib.sha256((pat + "painel").encode()).hexdigest()[:24] if pat else "")
        self.ativo = bool(self.chave and cfg.get("url"))
        self.modelos = list(cfg.get("modelos", ["klein", "schnell"]))
        self.motivo = "" if self.ativo else "sem GH_PAT/endereço do worker"

    def _hoje(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")   # a cota do Cloudflare vira à meia-noite UTC

    def cabe(self) -> bool:
        usado = _ler_gastos().get("flux", {}).get(self._hoje(), {}).get("neurons", 0)
        return usado + self.cfg["neurons_por_imagem"].get(self.modelos[0], 175) <= self.cfg["teto_diario_neurons"]

    def gerar(self, prompt: str, destino: Path) -> bool:
        for tentativa in range(3):
            modelo = self.modelos[0]
            r = requests.post(self.url, headers={"x-chave": self.chave},
                              json={"prompt": prompt, "passos": self.cfg.get("passos", 4), "modelo": modelo,
                                    "largura": self.cfg.get("largura", 896), "altura": self.cfg.get("altura", 512)},
                              timeout=120)
            if r.status_code == 200 and r.headers.get("content-type", "").startswith("image/"):
                destino.write_bytes(r.content)
                _registrar("flux", self._hoje(), "neurons", self.cfg["neurons_por_imagem"].get(modelo, 175))
                return True
            if r.status_code == 502 and len(self.modelos) > 1 and tentativa == 0 and "4006" not in r.text:
                log.warning("Flux %s falhou (%s) — usando o próximo modelo", modelo, r.text[:120])
                self.modelos.pop(0)
                continue
            if r.status_code == 429:
                log.warning("Flux: cota grátis do dia acabou (%s)", r.text[:120])
                self.ativo = False
                return False
            if r.status_code in (401, 403, 404):
                log.warning("Flux recusou (%s) — o worker precisa ser reinstalado?", r.status_code)
                self.ativo = False
                return False
            log.warning("Flux falhou (%s): %s", r.status_code, r.text[:160])
            time.sleep(3 * (tentativa + 1))
        return False


class _Higgsfield:
    nome = "higgsfield"
    BASE = "https://api.higgsfield.ai"

    def __init__(self, cfg: dict):
        self.cfg = cfg
        i, s = os.environ.get("HF_API_KEY_ID"), os.environ.get("HF_API_KEY_SECRET")
        self.cab = {"Authorization": f"Key {i}:{s}", "Content-Type": "application/json"} if i and s else None
        self.ativo = bool(cfg.get("ligado")) and self.cab is not None
        self.motivo = "" if self.ativo else "sem chave"

    def cabe(self) -> bool:
        mes = _ler_gastos().get("higgsfield", {}).get(date.today().strftime("%Y-%m"), {})
        return mes.get("usd", 0) + self.cfg["custo_estimado_por_imagem_usd"] <= self.cfg["teto_mensal_usd"]

    def gerar(self, prompt: str, destino: Path) -> bool:
        corpo = {"prompt": prompt, **(self.cfg.get("parametros_extra") or {})}
        r = requests.post(f"{self.BASE}/{self.cfg['modelo']}", headers=self.cab, json=corpo, timeout=60)
        if r.status_code in (401, 402, 403):
            log.warning("Higgsfield recusou (%s) — sem saldo ou chave inválida", r.status_code)
            self.ativo = False
            return False
        r.raise_for_status()
        status_url = r.json()["status_url"]
        for _ in range(120):
            time.sleep(3)
            s = requests.get(status_url, headers=self.cab, timeout=30).json()
            if s.get("status") == "completed":
                destino.write_bytes(requests.get(s["images"][0]["url"], timeout=120).content)
                _registrar("higgsfield", date.today().strftime("%Y-%m"), "usd", self.cfg["custo_estimado_por_imagem_usd"])
                return True
            if s.get("status") in ("failed", "nsfw", "canceled"):
                return False
        return False


class Ilustrador:
    def __init__(self, pasta: Path, cfg_canal: dict):
        geral = _geral()
        conf = geral.get("ilustracoes", {})
        img = cfg_canal.get("imagens") or {}
        self.estilo = img.get("estilo_ilustracao", "")
        self.extra = conf.get("sufixo_prompt", "")
        self.pasta = pasta / "ilustracoes"
        self.pasta.mkdir(parents=True, exist_ok=True)
        self.max_video = conf.get("max_por_video", 150)
        self.gerados = 0
        disponiveis = {"flux": lambda: _Flux(conf.get("flux", {})),
                       "higgsfield": lambda: _Higgsfield(geral.get("higgsfield", {}))}
        fontes = img.get("fontes", [])
        self.motores = [disponiveis[m]() for m in conf.get("motores", ["flux"]) if m in disponiveis and m in fontes]
        for m in self.motores:
            if not m.ativo:
                log.info("ilustrações: %s desligado (%s)", m.nome, m.motivo)
        self.ativo = any(m.ativo for m in self.motores)
        if not self.ativo:
            log.info("nenhum gerador de ilustração disponível — usando imagens livres")

    def _prompt(self, descricao: str) -> str:
        return f"{descricao.strip().rstrip('.')}. {self.extra} Style: {self.estilo}".replace("  ", " ")

    def _destino(self, descricao: str) -> Path:
        return self.pasta / (hashlib.sha1(self._prompt(descricao).encode()).hexdigest()[:16] + ".img")

    def gerar(self, descricao: str) -> Path | None:
        destino = self._destino(descricao)
        if destino.exists():
            return destino
        if not self.ativo or self.gerados >= self.max_video:
            return None
        for m in self.motores:
            if not m.ativo:
                continue
            if not m.cabe():
                log.warning("ilustrações: teto do %s atingido", m.nome)
                m.ativo = False
                continue
            try:
                if m.gerar(self._prompt(descricao), destino):
                    with _trava:
                        self.gerados += 1
                    return destino
            except Exception as e:
                log.warning("%s falhou: %s", m.nome, e)
        self.ativo = any(m.ativo for m in self.motores)
        return None

    def pre_gerar(self, descricoes: list[str], paralelo: int = 4) -> None:
        """Gera tudo de uma vez, em paralelo, antes de montar o vídeo."""
        unicas = list(dict.fromkeys(d for d in descricoes if d))
        if not (self.ativo and unicas):
            return
        log.info("gerando %d ilustrações…", len(unicas))
        with ThreadPoolExecutor(paralelo) as ex:
            list(ex.map(self.gerar, unicas))
        log.info("ilustrações prontas: %d geradas (%d pedidas)", self.gerados, len(unicas))
