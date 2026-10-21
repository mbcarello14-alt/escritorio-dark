"""Estilo Draw My Life: qualquer quadro é "desenhado" na tela por uma caneta, traço a traço."""
from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageOps

from .comum import ALTURA, FPS, LARGURA, hex_rgb

CELULA = 16          # tamanho do "pedaço" revelado a cada passo
FAIXA = 4            # células por faixa (a caneta varre em zigue-zague, como quem escreve)


@lru_cache(maxsize=4)
def _caneta(cor_corpo=(30, 58, 138)):
    """Canetão desenhado por código. Devolve (sprite RGBA, deslocamento da ponta)."""
    w, h = 90, 420
    s = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(s)
    d.rounded_rectangle((18, 0, 72, 300), radius=18, fill=cor_corpo + (255,))
    d.rectangle((18, 230, 72, 300), fill=(235, 235, 235, 255))
    d.polygon([(24, 300), (66, 300), (52, 380), (38, 380)], fill=(60, 60, 60, 255))
    d.polygon([(38, 380), (52, 380), (46, 412)], fill=(20, 20, 20, 255))
    d.rectangle((18, 40, 72, 60), fill=(245, 158, 11, 255))
    rot = s.rotate(-32, expand=True, resample=Image.BICUBIC)
    # posição da ponta após a rotação
    ang = math.radians(32)
    px, py = 46 - w / 2, 412 - h / 2
    rx = px * math.cos(ang) - py * math.sin(ang) + rot.width / 2
    ry = px * math.sin(ang) + py * math.cos(ang) + rot.height / 2
    return rot, (int(rx), int(ry))


def preparar_desenho(origem: Path, cor_fundo: str) -> Image.Image:
    """Encaixa uma ilustração (doodle) num quadro branco 16:9, com margem."""
    bg = hex_rgb(cor_fundo)
    img = ImageOps.exif_transpose(Image.open(origem)).convert("RGB")
    img = ImageOps.contain(img, (int(LARGURA * 0.86), int(ALTURA * 0.86)), Image.LANCZOS)
    quadro = Image.new("RGB", (LARGURA, ALTURA), bg)
    quadro.paste(img, ((LARGURA - img.width) // 2, (ALTURA - img.height) // 2))
    return quadro


def animar(depois: Image.Image, pasta: Path, cor_fundo: str, antes: Image.Image | None = None,
           segundos: float = 2.0) -> int:
    """Salva em `pasta` os quadros q000.png… da caneta desenhando a diferença entre `antes` e `depois`.
    Devolve o número de quadros."""
    pasta.mkdir(parents=True, exist_ok=True)
    bg = hex_rgb(cor_fundo)
    base = (antes or Image.new("RGB", depois.size, bg)).convert("RGB")
    a, b = np.asarray(base, dtype=np.int16), np.asarray(depois.convert("RGB"), dtype=np.int16)
    tinta = np.abs(a - b).sum(axis=2) > 40
    H, W = tinta.shape
    nl, nc = math.ceil(H / CELULA), math.ceil(W / CELULA)
    pad = np.zeros((nl * CELULA, nc * CELULA), bool)
    pad[:H, :W] = tinta
    cont = pad.reshape(nl, CELULA, nc, CELULA).sum(axis=(1, 3))
    celulas = [(l, c) for l in range(nl) for c in range(nc) if cont[l, c] > 2]
    if not celulas:
        depois.save(pasta / "q000.png")
        return 1
    # ordem de escrita: faixas de cima para baixo, zigue-zague dentro de cada faixa
    celulas.sort(key=lambda lc: (lc[0] // FAIXA, lc[1] if (lc[0] // FAIXA) % 2 == 0 else -lc[1], lc[0]))
    n = max(2, int(segundos * FPS))
    caneta, ponta = _caneta()
    tela = base.copy()
    mascara_tinta = Image.fromarray((tinta * 255).astype("uint8"))
    feitas = 0
    for q in range(n):
        alvo = math.ceil(len(celulas) * (q + 1) / n)
        m = Image.new("L", depois.size, 0)
        md = ImageDraw.Draw(m)
        for l, c in celulas[feitas:alvo]:
            md.rectangle((c * CELULA, l * CELULA, (c + 1) * CELULA, (l + 1) * CELULA), fill=255)
        m = Image.fromarray(np.minimum(np.asarray(m), np.asarray(mascara_tinta)))
        tela.paste(depois, (0, 0), m)
        feitas = alvo
        quadro = tela.copy()
        if q < n - 1:
            l, c = celulas[min(feitas, len(celulas)) - 1]
            x, y = c * CELULA + CELULA // 2, l * CELULA + CELULA // 2
            quadro.paste(caneta, (x - ponta[0], y - ponta[1]), caneta)
        quadro.save(pasta / f"q{q:03d}.png")
    depois.save(pasta / f"q{n - 1:03d}.png")
    return n
