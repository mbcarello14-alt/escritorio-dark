"""Ilustrações geradas no Higgsfield (API), com estilo fixo por canal e teto de gasto mensal.

Precisa dos segredos HF_API_KEY_ID e HF_API_KEY_SECRET (console.higgsfield.ai).
Sem saldo, sem chave ou acima do teto, devolve None e o motor usa imagens grátis.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import date
from pathlib import Path

import requests
import yaml

from .comum import RAIZ, log

BASE = "https://api.higgsfield.ai"
GASTOS = RAIZ / "canais" / "gastos-higgsfield.json"


def _geral() -> dict:
    return yaml.safe_load((RAIZ / "pipeline" / "config" / "geral.yaml").read_text(encoding="utf-8"))["higgsfield"]


def _ler_gastos() -> dict:
    return json.loads(GASTOS.read_text(encoding="utf-8")) if GASTOS.exists() else {}


def _registrar(qtd: int, custo: float) -> None:
    g = _ler_gastos()
    mes = date.today().strftime("%Y-%m")
    m = g.setdefault(mes, {"imagens": 0, "usd_estimado": 0.0})
    m["imagens"] += qtd
    m["usd_estimado"] = round(m["usd_estimado"] + custo, 2)
    GASTOS.write_text(json.dumps(g, indent=2), encoding="utf-8")


class Ilustrador:
    def __init__(self, pasta: Path, cfg_canal: dict):
        self.cfg = _geral()
        self.estilo = (cfg_canal.get("imagens") or {}).get("estilo_ilustracao", "")
        self.pasta = pasta / "ilustracoes"
        self.pasta.mkdir(parents=True, exist_ok=True)
        self.gerados = 0
        chave_id, chave_seg = os.environ.get("HF_API_KEY_ID"), os.environ.get("HF_API_KEY_SECRET")
        self.cabecalho = {"Authorization": f"Key {chave_id}:{chave_seg}", "Content-Type": "application/json"} \
            if chave_id and chave_seg else None
        self.ativo = bool(self.cfg.get("ligado")) and self.cabecalho is not None and \
            "higgsfield" in (cfg_canal.get("imagens") or {}).get("fontes", [])
        if not self.ativo:
            log.info("Higgsfield desligado ou sem chave — usando imagens grátis")

    def _dentro_do_teto(self) -> bool:
        mes = _ler_gastos().get(date.today().strftime("%Y-%m"), {})
        prox = mes.get("usd_estimado", 0) + self.cfg["custo_estimado_por_imagem_usd"]
        return prox <= self.cfg["teto_mensal_usd"] and self.gerados < self.cfg["max_imagens_por_video"]

    def gerar(self, descricao: str) -> Path | None:
        if not self.ativo:
            return None
        prompt = f"{descricao.strip().rstrip('.')}. Style: {self.estilo}"
        destino = self.pasta / (hashlib.sha1(prompt.encode()).hexdigest()[:16] + ".img")
        if destino.exists():
            return destino
        if not self._dentro_do_teto():
            log.warning("teto mensal do Higgsfield atingido — usando imagem grátis")
            self.ativo = False
            return None
        try:
            corpo = {"prompt": prompt, **(self.cfg.get("parametros_extra") or {})}
            r = requests.post(f"{BASE}/{self.cfg['modelo']}", headers=self.cabecalho, json=corpo, timeout=60)
            if r.status_code in (401, 402, 403):
                log.warning("Higgsfield recusou (%s): %s — sem saldo ou chave inválida", r.status_code, r.text[:200])
                self.ativo = False
                return None
            r.raise_for_status()
            status_url = r.json()["status_url"]
            for _ in range(120):  # até ~6 min
                time.sleep(3)
                s = requests.get(status_url, headers=self.cabecalho, timeout=30).json()
                if s.get("status") == "completed":
                    url = s["images"][0]["url"]
                    destino.write_bytes(requests.get(url, timeout=120).content)
                    self.gerados += 1
                    _registrar(1, self.cfg["custo_estimado_por_imagem_usd"])
                    log.info("ilustração gerada (%d no vídeo)", self.gerados)
                    return destino
                if s.get("status") in ("failed", "nsfw", "canceled"):
                    log.warning("Higgsfield: %s para '%s'", s.get("status"), descricao[:60])
                    return None
            log.warning("Higgsfield demorou demais para '%s'", descricao[:60])
        except Exception as e:
            log.warning("Higgsfield falhou: %s", e)
        return None
