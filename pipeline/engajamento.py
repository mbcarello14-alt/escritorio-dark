"""Arte animada de "Inscreva-se · Gostei · Comente" que entra na tela quando a narração faz a chamada.

- vídeo longo: aparece nas cenas cuja narração pede inscrição, like ou comentário (começo, meio e fim);
- Shorts: aparece no meio e nos últimos segundos de cada corte.
Desenhada aqui (Pillow), nas cores do canal: sempre igual, nítida e sem custo.
"""
from __future__ import annotations

import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from .comum import FONTES, hex_rgb, rodar

CHAMADA = re.compile(r"inscrev|deixa o like|deixe o like|d[aá] o like|sininho|coment[aá]rio", re.I)
VERMELHO = (230, 33, 23)
S = 3  # desenha 3x maior e reduz


def eh_chamada(narracao: str) -> bool:
    return bool(CHAMADA.search(narracao))


def _sino(d, x, y, t, cor):
    d.pieslice((x - t * .55, y - t * .55, x + t * .55, y + t * .45), 180, 360, fill=cor)
    d.rectangle((x - t * .55, y - t * .05, x + t * .55, y + t * .32), fill=cor)
    d.rounded_rectangle((x - t * .72, y + t * .28, x + t * .72, y + t * .42), radius=t * .07, fill=cor)
    d.ellipse((x - t * .16, y + t * .42, x + t * .16, y + t * .66), fill=cor)
    d.ellipse((x - t * .1, y - t * .72, x + t * .1, y - t * .52), fill=cor)


def _joinha(d, x, y, t, cor):
    d.rounded_rectangle((x - t * .7, y - t * .05, x - t * .38, y + t * .62), radius=t * .06, fill=cor)    # punho
    d.rounded_rectangle((x - t * .3, y - t * .1, x + t * .62, y + t * .62), radius=t * .14, fill=cor)     # mão
    d.polygon([(x - t * .3, y - t * .02), (x - t * .02, y - t * .72), (x + t * .2, y - t * .7),
               (x + t * .12, y - t * .1)], fill=cor)                                                    # polegar
    d.ellipse((x - t * .06, y - t * .82, x + t * .22, y - t * .56), fill=cor)


def _balao(d, x, y, t, cor):
    d.rounded_rectangle((x - t * .7, y - t * .55, x + t * .7, y + t * .35), radius=t * .25, fill=cor)
    d.polygon([(x - t * .35, y + t * .3), (x - t * .55, y + t * .7), (x - t * .05, y + t * .3)], fill=cor)


def arte(cfg: dict, largura: int = 1920, altura: int = 1080, vertical: bool = False) -> Image.Image:
    """PNG transparente do tamanho do vídeo, com a faixa de chamada embaixo."""
    est = cfg["estilo"]
    escuro = est.get("modo") != "quadro_branco"
    fundo = hex_rgb(est["fundo"]) if escuro else hex_rgb(est["destaque2"])
    destaque = hex_rgb(est["destaque"])
    from PIL import ImageFont
    k = 1.3 if vertical else 1.0
    f = ImageFont.truetype(str(FONTES / "Poppins-ExtraBold.ttf"), int(46 * S * k))
    botoes = [("INSCREVA-SE", VERMELHO, (255, 255, 255), _sino),
              ("GOSTEI", (255, 255, 255), (20, 20, 20), _joinha),
              ("COMENTE", destaque, (20, 20, 20), _balao)]
    h, ic, pad, gap = int(104 * S * k), int(56 * S * k), int(34 * S * k), int(26 * S * k)
    larg = [int(f.getlength(t) + ic + pad * 2.4) for t, *_ in botoes]
    if vertical:   # um embaixo do outro não cabe bem; no vertical fica em duas linhas
        linhas = [[0], [1, 2]]
    else:
        linhas = [[0, 1, 2]]
    W = largura * S
    alto_total = len(linhas) * h + (len(linhas) - 1) * gap + 2 * 30 * S
    larg_faixa = max(sum(larg[i] for i in l) + gap * (len(l) - 1) for l in linhas) + 2 * 34 * S
    img = Image.new("RGBA", (W, altura * S), (0, 0, 0, 0))
    x0 = (W - larg_faixa) // 2
    y0 = (altura - (60 if vertical else 70)) * S - alto_total   # no vertical: abaixo da legenda
    sombra = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sombra).rounded_rectangle((x0, y0 + 14 * S, x0 + larg_faixa, y0 + alto_total + 14 * S),
                                             radius=40 * S, fill=(0, 0, 0, 140))
    img.alpha_composite(sombra.filter(ImageFilter.GaussianBlur(14 * S)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((x0, y0, x0 + larg_faixa, y0 + alto_total), radius=40 * S, fill=fundo + (240,),
                        outline=destaque, width=5 * S)
    y = y0 + 30 * S
    for l in linhas:
        lw = sum(larg[i] for i in l) + gap * (len(l) - 1)
        x = (W - lw) // 2
        for i in l:
            texto, cor_bt, cor_tx, icone = botoes[i]
            d.rounded_rectangle((x, y, x + larg[i], y + h), radius=h // 2, fill=cor_bt)
            icone(d, x + pad + ic / 2, y + h / 2, ic * .62, cor_tx)
            d.text((x + pad + ic + pad * .4, y + h / 2), texto, font=f, fill=cor_tx, anchor="lm")
            x += larg[i] + gap
        y += h + gap
    return img.resize((largura, altura), Image.LANCZOS)


def aplicar(clipe: Path, png: Path, inicio: float, dur: float, saida: Path) -> Path:
    """Faz a arte entrar (subindo e aparecendo) em `inicio` e sair no fim do trecho de `dur` segundos."""
    fim = inicio + dur
    filtro = (f"[1:v]format=rgba,fade=t=in:st={inicio:.2f}:d=0.35:alpha=1,"
              f"fade=t=out:st={max(inicio, fim - 0.35):.2f}:d=0.35:alpha=1[a];"
              f"[0:v][a]overlay=x=0:y='if(lt(t,{inicio:.2f}+0.35),(1-(t-{inicio:.2f})/0.35)*60,0)':"
              f"enable='between(t,{inicio:.2f},{fim:.2f})':shortest=1[v]")
    rodar(["ffmpeg", "-y", "-v", "error", "-i", str(clipe), "-loop", "1", "-i", str(png), "-filter_complex", filtro,
           "-map", "[v]", "-map", "0:a?", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
           "-r", "30", "-c:a", "copy", str(saida)])
    return saida


if __name__ == "__main__":   # prévia: python -m pipeline.engajamento historia
    import sys
    from .comum import RAIZ, carregar_config
    c = carregar_config(sys.argv[1] if len(sys.argv) > 1 else "historia")
    (RAIZ / "saida").mkdir(exist_ok=True)
    base = Image.new("RGBA", (1920, 1080), (90, 110, 130, 255))
    base.alpha_composite(arte(c))
    base.convert("RGB").save(RAIZ / "saida" / "chamada.png")
    v = Image.new("RGBA", (1080, 1920), (90, 110, 130, 255))
    v.alpha_composite(arte(c, 1080, 1920, vertical=True))
    v.convert("RGB").save(RAIZ / "saida" / "chamada-vertical.png")
