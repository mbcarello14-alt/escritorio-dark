"""Teste rápido do visual: gera 2 ilustrações por canal (Flux) e monta um quadro com a webcam.

Uso: python -m pipeline.teste_visual   → canais/amostras/visual/<canal>-N.jpg
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

from . import apresentador, cartoes
from .comum import ALTURA, LARGURA, RAIZ, carregar_config, log
from .imagens_ia import Ilustrador

CENAS = {
    "historia": ["a nervous 1920s stock broker on Wall Street throwing paper money in the air while coffee sacks pile up behind him",
                 "a Brazilian coffee farmer in 1929 watching a ship dump sacks of coffee into the sea, shocked expression"],
    "vestibular": ["a steam engine", "a sad factory worker holding a hammer"],
    "livros": ["a tiny person standing on a giant open book like a bridge over a river of letters-free papers",
               "a woman reading in an armchair while thought bubbles turn into birds flying out of the window"],
}


def main():
    destino = RAIZ / "canais" / "amostras" / "visual"
    destino.mkdir(parents=True, exist_ok=True)
    tmp = RAIZ / "saida" / "teste_visual"
    for canal, cenas in CENAS.items():
        cfg = carregar_config(canal)
        il = Ilustrador(tmp / canal, cfg)
        a, est = cfg["apresentador"], cfg["estilo"]
        cam = apresentador._moldura(cfg, apresentador.personagem(a, apresentador._c(est["fundo"]),
                                                                 apresentador._c(est["destaque"]), 2), int(ALTURA * a.get("tamanho", 0.3)))
        for n, cena in enumerate(cenas, 1):
            orig = il.gerar(cena)
            if not orig:
                log.warning("%s: não gerou '%s'", canal, cena)
                continue
            jpg = cartoes.preparar_imagem(orig, tmp / f"{canal}-{n}.jpg", preencher=True)
            quadro = Image.open(jpg).convert("RGBA").resize((LARGURA, ALTURA))
            m = int(ALTURA * 0.025)
            quadro.alpha_composite(cam, (LARGURA - cam.width - m + 12, ALTURA - cam.height - m + 12))
            quadro.convert("RGB").resize((1280, 720)).save(destino / f"{canal}-{n}.jpg", quality=85)
            log.info("amostra %s-%d pronta", canal, n)


if __name__ == "__main__":
    main()
