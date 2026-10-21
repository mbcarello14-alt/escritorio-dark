"""Utilidades compartilhadas: caminhos, configuração, cores e fontes."""
from __future__ import annotations

import json
import logging
import subprocess
from functools import lru_cache
from pathlib import Path

import yaml
from PIL import ImageFont

RAIZ = Path(__file__).resolve().parent.parent
ASSETS = RAIZ / "assets"
FONTES = ASSETS / "fonts"
MUSICA = RAIZ / "musica"

LARGURA, ALTURA, FPS = 1920, 1080, 30

log = logging.getLogger("escritorio")
if not log.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")


def carregar_config(canal: str) -> dict:
    caminho = RAIZ / "pipeline" / "config" / f"{canal}.yaml"
    if not caminho.exists():
        raise SystemExit(f"Canal desconhecido: {canal} (não achei {caminho})")
    return yaml.safe_load(caminho.read_text(encoding="utf-8"))


def carregar_producao(pasta: Path) -> dict:
    arq = pasta / "producao.json"
    if not arq.exists():
        raise SystemExit(f"Não achei {arq}. Os agentes precisam escrever o producao.json antes.")
    return json.loads(arq.read_text(encoding="utf-8"))


def hex_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def misturar(a, b, t: float):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


@lru_cache(maxsize=64)
def fonte(nome: str, tamanho: int, variacao: str | None = None) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(str(FONTES / nome), tamanho)
    if variacao:
        try:
            f.set_variation_by_name(variacao)
        except Exception:  # fonte sem eixos variáveis
            pass
    return f


def fonte_titulo(cfg: dict, tamanho: int):
    e = cfg["estilo"]
    return fonte(e["fonte_titulo"], int(tamanho * e.get("escala_fonte", 1.0)), e.get("fonte_titulo_variacao"))


def fonte_texto(cfg: dict, tamanho: int, peso: str = "Regular"):
    e = cfg["estilo"]
    return fonte(e["fonte_texto"], int(tamanho * e.get("escala_fonte", 1.0)), peso)


def rodar(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    log.debug("$ %s", " ".join(map(str, cmd)))
    kw.setdefault("timeout", 1800)
    r = subprocess.run(cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL, **kw)
    if r.returncode != 0:
        raise RuntimeError(f"Comando falhou ({r.returncode}): {' '.join(map(str, cmd))}\n{r.stderr[-3000:]}")
    return r


def duracao_audio(arq: Path) -> float:
    r = rodar(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(arq)])
    return float(r.stdout.strip())


def quebrar_linhas(texto: str, fnt, largura_max: int) -> list[str]:
    palavras, linhas, atual = texto.split(), [], ""
    for p in palavras:
        teste = f"{atual} {p}".strip()
        if fnt.getlength(teste) <= largura_max or not atual:
            atual = teste
        else:
            linhas.append(atual)
            atual = p
    if atual:
        linhas.append(atual)
    return linhas
