"""Desenho por código: cartões de texto, mapas mentais, preparo de imagens e thumbnails."""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageOps

from .comum import (ALTURA, ASSETS, LARGURA, fonte_texto, fonte_titulo, hex_rgb, misturar,
                    quebrar_linhas)


# ---------------------------------------------------------------- base visual
def _cores(cfg):
    e = cfg["estilo"]
    return hex_rgb(e["fundo"]), hex_rgb(e["destaque"]), hex_rgb(e["destaque2"]), hex_rgb(e["texto"])


def fundo(cfg, w=LARGURA, h=ALTURA) -> Image.Image:
    """Fundo da cor do canal com vinheta suave."""
    bg, *_ = _cores(cfg)
    if cfg["estilo"].get("modo") == "quadro_branco":
        return Image.new("RGB", (w, h), bg)
    escuro = misturar(bg, (0, 0, 0), 0.45)
    img = Image.new("RGB", (w, h), escuro)
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).ellipse((-w * 0.15, -h * 0.35, w * 1.15, h * 1.35), fill=255)
    m = m.filter(ImageFilter.GaussianBlur(w // 8))
    img.paste(Image.new("RGB", (w, h), bg), (0, 0), m)
    return img


def _titulo(cfg, texto):
    return texto.upper() if cfg["estilo"].get("caixa_alta_titulo") else texto


def _texto_centralizado(d, linhas, fnt, y, cor, w=LARGURA, entre=1.15):
    alt = fnt.size * entre
    for i, l in enumerate(linhas):
        d.text((w / 2, y + i * alt), l, font=fnt, fill=cor, anchor="ma")
    return y + len(linhas) * alt


def _simbolo(cfg, tamanho):
    s = Image.open(ASSETS / cfg["canal"] / "simbolo.png").convert("RGBA")
    return s.resize((tamanho, tamanho), Image.LANCZOS)


# ---------------------------------------------------------------- cartões
def cartao(cfg, titulo: str, subtitulo: str = "") -> Image.Image:
    bg, ac, ac2, tx = _cores(cfg)
    img = fundo(cfg)
    d = ImageDraw.Draw(img)
    ft = fonte_titulo(cfg, 110)
    linhas = quebrar_linhas(_titulo(cfg, titulo), ft, 1500)
    if len(linhas) > 2:
        ft = fonte_titulo(cfg, 80)
        linhas = quebrar_linhas(_titulo(cfg, titulo), ft, 1600)
    fs = fonte_texto(cfg, 44)
    sub = quebrar_linhas(subtitulo, fs, 1400) if subtitulo else []
    altura_total = len(linhas) * ft.size * 1.15 + (60 + len(sub) * 44 * 1.3 if sub else 0)
    y = (ALTURA - altura_total) / 2
    y = _texto_centralizado(d, linhas, ft, y, ac)
    if sub:
        d.line((LARGURA / 2 - 60, y + 22, LARGURA / 2 + 60, y + 22), fill=ac, width=4)
        _texto_centralizado(d, sub, fs, y + 56, tx, entre=1.3)
    return img


def numero(cfg, valor: str, rotulo: str = "") -> Image.Image:
    bg, ac, ac2, tx = _cores(cfg)
    img = fundo(cfg)
    d = ImageDraw.Draw(img)
    fv = fonte_titulo(cfg, 260 if len(valor) <= 6 else 170)
    d.text((LARGURA / 2, ALTURA / 2 - 40), valor, font=fv, fill=ac, anchor="mm")
    if rotulo:
        fr = fonte_texto(cfg, 50)
        _texto_centralizado(d, quebrar_linhas(rotulo, fr, 1400), fr, ALTURA / 2 + fv.size * 0.55, tx)
    return img


def citacao(cfg, texto: str, autor: str = "") -> Image.Image:
    bg, ac, ac2, tx = _cores(cfg)
    img = fundo(cfg)
    d = ImageDraw.Draw(img)
    d.text((LARGURA / 2, 170), "“", font=fonte_titulo(cfg, 240), fill=ac, anchor="mm")
    fq = fonte_titulo(cfg, 66)
    linhas = quebrar_linhas(texto, fq, 1450)
    y = _texto_centralizado(d, linhas, fq, 330, tx, entre=1.3)
    if autor:
        d.text((LARGURA / 2, y + 50), f"— {autor}", font=fonte_texto(cfg, 40, "SemiBold"), fill=ac, anchor="ma")
    return img


def lista(cfg, titulo: str, itens: list[str]) -> Image.Image:
    bg, ac, ac2, tx = _cores(cfg)
    img = fundo(cfg)
    d = ImageDraw.Draw(img)
    ft = fonte_titulo(cfg, 84)
    d.text((220, 150), _titulo(cfg, titulo), font=ft, fill=ac)
    fi = fonte_texto(cfg, 52)
    y = 330
    for it in itens[:5]:
        d.ellipse((230, y + 18, 258, y + 46), fill=ac)
        linhas = quebrar_linhas(it, fi, 1320)
        for l in linhas:
            d.text((300, y), l, font=fi, fill=tx)
            y += 66
        y += 34
    return img


def comparacao(cfg, esquerda: dict, direita: dict) -> Image.Image:
    bg, ac, ac2, tx = _cores(cfg)
    img = fundo(cfg)
    d = ImageDraw.Draw(img)
    d.line((LARGURA / 2, 170, LARGURA / 2, ALTURA - 170), fill=misturar(ac, bg, 0.5), width=3)
    ft, fi = fonte_titulo(cfg, 70), fonte_texto(cfg, 44)
    for lado, x0 in ((esquerda, 160), (direita, LARGURA / 2 + 100)):
        d.text((x0, 190), _titulo(cfg, lado.get("titulo", "")), font=ft, fill=ac)
        y = 330
        for it in lado.get("itens", [])[:5]:
            for i, l in enumerate(quebrar_linhas(it, fi, 700)):
                d.text((x0 + (40 if i else 0), y), ("• " if i == 0 else "") + l, font=fi, fill=tx)
                y += 58
            y += 26
    return img


# ---------------------------------------------------------------- mapa mental
def _pilula(d, centro, texto, fnt, cor_fundo, cor_texto, cor_borda=None, larg_max=420, pad=(30, 18), alpha=1.0):
    linhas = quebrar_linhas(texto, fnt, larg_max)
    w = max(fnt.getlength(l) for l in linhas) + pad[0] * 2
    h = len(linhas) * fnt.size * 1.2 + pad[1] * 2
    x, y = centro
    caixa = (x - w / 2, y - h / 2, x + w / 2, y + h / 2)
    d.rounded_rectangle(caixa, radius=min(h / 2, 40), fill=cor_fundo, outline=cor_borda, width=4 if cor_borda else 0)
    for i, l in enumerate(linhas):
        d.text((x, y - h / 2 + pad[1] + i * fnt.size * 1.2), l, font=fnt, fill=cor_texto, anchor="ma")
    return caixa


def mapa_mental(cfg, mapa: dict, revelar: int, progresso: float = 1.0) -> Image.Image:
    """Desenha o mapa com `revelar` ramos; o último entra com `progresso` (0→1) para animar."""
    bg, ac, ac2, tx = _cores(cfg)
    escala = 2  # desenha em 2x e reduz, para linhas suaves
    W, H = LARGURA * escala, ALTURA * escala
    img = fundo(cfg, W, H)
    camada = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(camada)
    cx, cy = W / 2, H / 2
    ramos = mapa.get("ramos", [])[:6]
    n = max(len(ramos), 1)
    revelar = max(0, min(revelar, len(ramos)))
    rx1, ry1, rx2, ry2 = 560 * escala, 300 * escala, 820 * escala, 430 * escala
    f_ramo, f_filho, f_centro = fonte_texto(cfg, 34 * escala, "SemiBold"), fonte_texto(cfg, 27 * escala), fonte_titulo(cfg, 46 * escala)
    linha_cor = misturar(tx, bg, 0.35)

    for i, ramo in enumerate(ramos[:revelar]):
        t = progresso if i == revelar - 1 else 1.0
        if t <= 0:
            continue
        ang = math.radians(-90 + i * 360 / n) if n > 1 else 0
        px, py = cx + rx1 * math.cos(ang) * t, cy + ry1 * math.sin(ang) * t
        d.line((cx, cy, px, py), fill=linha_cor, width=6 * escala)
        filhos = ramo.get("filhos", [])[:3]
        dx, dy = math.cos(ang), math.sin(ang)
        vertical = abs(dy)  # ramos de cima/baixo espalham os filhos na horizontal
        dist = (250 - 120 * vertical) * escala
        passo = (78 + 240 * vertical) * escala
        for j, filho in enumerate(filhos):
            k = j - (len(filhos) - 1) / 2
            # filhos em leque: afastados do ramo e espalhados na perpendicular
            alvo_x = (cx + rx1 * dx) + dx * dist + (-dy) * passo * k
            alvo_y = (cy + ry1 * dy) + dy * dist + dx * passo * k
            fx, fy = px + (alvo_x - px) * t, py + (alvo_y - py) * t
            if t > 0.5:
                d.line((px, py, fx, fy), fill=linha_cor, width=3 * escala)
                fundo_filho = bg if cfg["estilo"].get("modo") == "quadro_branco" else misturar(bg, (0, 0, 0), 0.25)
                _pilula(d, (fx, fy), filho, f_filho, fundo_filho, tx,
                        cor_borda=linha_cor, larg_max=300 * escala, pad=(22 * escala, 12 * escala))
        novo = i == revelar - 1 and progresso < 1.0
        _pilula(d, (px, py), ramo.get("rotulo", ""), f_ramo, ac if (i == revelar - 1) else tx,
                bg if (i == revelar - 1) else bg, larg_max=360 * escala, pad=(30 * escala, 16 * escala))
    _pilula(d, (cx, cy), mapa.get("centro", ""), f_centro, misturar(bg, (255, 255, 255), 0.06), ac,
            cor_borda=ac, larg_max=480 * escala, pad=(40 * escala, 26 * escala))
    img.paste(camada, (0, 0), camada)
    return img.resize((LARGURA, ALTURA), Image.LANCZOS)


# ---------------------------------------------------------------- imagens
def preparar_imagem(origem: Path, destino: Path, legenda: str = "") -> Path:
    """Recorta para 16:9 em 4K (folga para o zoom suave) e salva como JPG."""
    img = ImageOps.exif_transpose(Image.open(origem)).convert("RGB")
    alvo = (LARGURA * 2, ALTURA * 2)
    if img.width / img.height < 1.2:  # retrato: põe sobre fundo desfocado
        fundo_img = ImageOps.fit(img, alvo).filter(ImageFilter.GaussianBlur(40))
        fundo_img = Image.blend(fundo_img, Image.new("RGB", alvo, (0, 0, 0)), 0.45)
        frente = ImageOps.contain(img, (alvo[0], int(alvo[1] * 0.96)))
        fundo_img.paste(frente, ((alvo[0] - frente.width) // 2, (alvo[1] - frente.height) // 2))
        img = fundo_img
    else:
        img = ImageOps.fit(img, alvo, Image.LANCZOS)
    img.save(destino, quality=92)
    return destino


def sobreposicao_legenda(cfg, legenda: str, destino: Path) -> Path:
    """PNG transparente com a legenda da imagem no canto inferior esquerdo."""
    bg, ac, ac2, tx = _cores(cfg)
    img = Image.new("RGBA", (LARGURA, ALTURA), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = fonte_texto(cfg, 34, "SemiBold")
    w = f.getlength(legenda)
    d.rectangle((70, ALTURA - 150, 70 + w + 60, ALTURA - 82), fill=bg + (225,))
    d.rectangle((70, ALTURA - 150, 78, ALTURA - 82), fill=ac + (255,))
    d.text((108, ALTURA - 116), legenda, font=f, fill=tx, anchor="lm")
    img.save(destino)
    return destino


# ---------------------------------------------------------------- thumbnail
def thumbnail(cfg, texto: str, imagem: Path | None, layout: str, destino: Path) -> Path:
    bg, ac, ac2, tx = _cores(cfg)
    W, H = 1280, 720
    if imagem:
        base = ImageOps.fit(ImageOps.exif_transpose(Image.open(imagem)).convert("RGB"), (W, H), Image.LANCZOS)
        base = Image.blend(base, Image.new("RGB", (W, H), misturar(bg, (0, 0, 0), 0.3)), 0.15)
    else:
        base = fundo(cfg, W, H)
        s = _simbolo(cfg, 520)
        base.paste(s, ((W - 520) // 2 if layout == "centro" else (60 if layout == "direita" else W - 580), 100), s)
    # degradê do lado do texto
    grad = Image.new("L", (W, H), 0)
    gd = ImageDraw.Draw(grad)
    for x in range(W):
        if layout == "esquerda":
            a = max(0, 1 - x / (W * 0.62))
        elif layout == "direita":
            a = max(0, (x - W * 0.38) / (W * 0.62))
        else:
            a = 0.55
        gd.line((x, 0, x, H), fill=int(235 * min(1, a * 1.4)))
    base.paste(Image.new("RGB", (W, H), misturar(bg, (0, 0, 0), 0.35)), (0, 0), grad)
    d = ImageDraw.Draw(base)
    palavras = _titulo(cfg, texto)
    larg = 620 if layout != "centro" else 1100
    tam = 150
    while tam > 60:
        f = fonte_titulo(cfg, tam)
        linhas = quebrar_linhas(palavras, f, larg)
        if len(linhas) <= 3 and all(f.getlength(l) <= larg for l in linhas):
            break
        tam -= 8
    alt = len(linhas) * tam * 1.05
    y = (H - alt) / 2
    for i, l in enumerate(linhas):
        if layout == "esquerda":
            pos, anc = (70, y + i * tam * 1.05), "la"
        elif layout == "direita":
            pos, anc = (W - 70, y + i * tam * 1.05), "ra"
        else:
            pos, anc = (W / 2, y + i * tam * 1.05), "ma"
        cor = ac if i == len(linhas) - 1 else (255, 255, 255)
        d.text(pos, l, font=f, fill=cor, anchor=anc, stroke_width=max(3, tam // 18), stroke_fill=(0, 0, 0))
    s = _simbolo(cfg, 92)
    base.paste(s, (W - 120 if layout != "direita" else 28, H - 120), s)
    base.save(destino, quality=92)
    if destino.stat().st_size > 2_000_000:  # limite do YouTube
        base.save(destino, quality=80)
    return destino
