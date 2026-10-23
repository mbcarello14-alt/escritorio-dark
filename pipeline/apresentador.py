"""Apresentador na "webcam": personagem fixo de cada canal, num quadro no canto do vídeo,
com a boca acompanhando a narração e piscando de vez em quando.

Tudo é desenhado aqui (Pillow), então o personagem é sempre o mesmo, sai de graça e não
depende de nenhum serviço. O visual de cada canal vem de `apresentador:` no config do canal.

Uso (prévia):  python -m pipeline.apresentador historia  → saida/apresentador-historia.png
"""
from __future__ import annotations

import math
import random
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from .comum import ALTURA, FPS, LARGURA, RAIZ, carregar_config, fonte, hex_rgb, log, rodar

S = 4            # desenha 4x maior e reduz (bordas suaves)
BASE = 400       # lado da "câmera" em pixels do vídeo 1080p
CONTORNO = (34, 26, 22)


def _c(v):
    return hex_rgb(v) if isinstance(v, str) else tuple(v)


def _escurecer(cor, f=0.75):
    return tuple(int(c * f) for c in cor)


class _Pincel:
    """Desenha em coordenadas da câmera (0–400) já escaladas."""

    def __init__(self, img):
        self.d = ImageDraw.Draw(img)

    def _b(self, caixa):
        return [v * S for v in caixa]

    def elipse(self, caixa, cor, contorno=CONTORNO, w=3):
        self.d.ellipse(self._b(caixa), fill=cor, outline=contorno, width=int(w * S) if contorno else 0)

    def poligono(self, pts, cor, contorno=CONTORNO, w=3):
        self.d.polygon([(x * S, y * S) for x, y in pts], fill=cor, outline=contorno, width=int(w * S) if contorno else 0)

    def ret(self, caixa, cor, raio=0, contorno=CONTORNO, w=3):
        self.d.rounded_rectangle(self._b(caixa), radius=raio * S, fill=cor, outline=contorno, width=int(w * S) if contorno else 0)

    def arco(self, caixa, ini, fim, cor=CONTORNO, w=3):
        self.d.arc(self._b(caixa), ini, fim, fill=cor, width=int(w * S))

    def linha(self, pts, cor=CONTORNO, w=3):
        self.d.line([(x * S, y * S) for x, y in pts], fill=cor, width=int(w * S), joint="curve")

    def corda(self, caixa, ini, fim, cor, contorno=CONTORNO, w=3):
        self.d.chord(self._b(caixa), ini, fim, fill=cor, outline=contorno, width=int(w * S) if contorno else 0)


# ------------------------------------------------------------------ cenário
def _cenario(p: _Pincel, a: dict, fundo, destaque):
    fundo = _c(a.get("parede", fundo))
    escuro = _escurecer(fundo, 0.55)
    p.ret((0, 0, BASE, BASE), escuro, contorno=None)
    # luz suave atrás do personagem
    for i in range(12, 0, -1):
        f = 0.55 + 0.45 * (1 - i / 12)
        r = 30 + i * 14
        p.elipse((200 - r, 170 - r, 200 + r, 170 + r), _escurecer(fundo, f), contorno=None)
    tipo = a.get("cenario", "estante")
    if tipo == "estante":
        madeira = _escurecer(fundo, 0.42)
        for y in (60, 150):
            p.ret((-10, y + 62, 120, y + 72), madeira, contorno=None)
            p.ret((290, y + 62, 410, y + 72), madeira, contorno=None)
            rnd = random.Random(y)
            for lado in ((4, 116), (296, 404)):
                x = lado[0]
                while x < lado[1] - 10:
                    larg = rnd.randint(9, 16)
                    alt = rnd.randint(40, 60)
                    cor = rnd.choice([destaque, _escurecer(destaque, 0.6), (210, 200, 180), _escurecer(fundo, 1.3)])
                    p.ret((x, y + 62 - alt, x + larg, y + 62), _escurecer(cor, 0.8), contorno=None)
                    x += larg + 2
    elif tipo == "cofre":
        # quadro com moeda e pilhas de moedas na prateleira
        p.ret((22, 46, 112, 136), _escurecer(destaque, 0.55), raio=4, contorno=None)
        p.ret((30, 54, 104, 128), _escurecer(fundo, 0.35), raio=2, contorno=None)
        p.elipse((44, 68, 90, 114), destaque, contorno=_escurecer(destaque, 0.6), w=2)
        p.elipse((54, 78, 80, 104), _escurecer(destaque, 0.8), contorno=None)
        p.ret((286, 170, 410, 180), _escurecer(fundo, 0.4), contorno=None)
        for i, h in enumerate((5, 8, 4, 6)):
            x = 300 + i * 26
            for k in range(h):
                p.ret((x, 166 - k * 7, x + 20, 172 - k * 7), _escurecer(destaque, 0.9 - 0.04 * (k % 2)), raio=2,
                      contorno=_escurecer(destaque, 0.5), w=1)
    elif tipo == "lousa":
        p.ret((262, 40, 420, 170), (245, 245, 240), raio=4, contorno=_escurecer(fundo, 0.4), w=4)
        for i in range(3):
            p.linha([(280, 70 + i * 30), (300 + i * 20, 62 + i * 30), (330 + i * 10, 74 + i * 30)], destaque, 3)
        for i, cor in enumerate(((235, 90, 80), (80, 170, 110), (250, 200, 60))):
            p.ret((24 + i * 26, 150 - i * 6, 42 + i * 26, 200), cor, raio=3, w=2)   # canetões
        p.ret((10, 200, 120, 210), _escurecer(fundo, 0.42), contorno=None)


# ------------------------------------------------------------------ personagem
def _corpo(p: _Pincel, a: dict, dy: float):
    roupa, pele = _c(a["roupa"]), _c(a["pele"])
    p.poligono([(70, 420), (92, 330 + dy), (150, 302 + dy), (250, 302 + dy), (308, 330 + dy), (330, 420)], roupa)
    p.ret((178, 262 + dy, 222, 312 + dy), _escurecer(pele, 0.9), raio=8)
    gola = a.get("gola", "terno")
    if gola == "terno":
        camisa = (245, 242, 235)
        p.poligono([(160, 304 + dy), (200, 360 + dy), (240, 304 + dy)], camisa, w=2)
        p.poligono([(150, 302 + dy), (200, 372 + dy), (176, 400), (120, 330 + dy)], _escurecer(roupa, 0.8), w=2)
        p.poligono([(250, 302 + dy), (200, 372 + dy), (224, 400), (280, 330 + dy)], _escurecer(roupa, 0.8), w=2)
        gravata = _c(a.get("gravata", "#C0392B"))
        p.poligono([(188, 306 + dy), (212, 306 + dy), (206, 322 + dy), (194, 322 + dy)], gravata, w=2)
        p.poligono([(194, 320 + dy), (206, 320 + dy), (214, 368 + dy), (200, 384 + dy), (186, 368 + dy)], gravata, w=2)
    elif gola == "moletom":
        p.elipse((150, 296 + dy, 250, 330 + dy), _escurecer(roupa, 0.8), w=2)
        p.linha([(184, 322 + dy), (178, 368 + dy)], (240, 240, 235), 3)
        p.linha([(216, 322 + dy), (222, 368 + dy)], (240, 240, 235), 3)
    elif gola == "cardigan":
        blusa = _c(a.get("blusa", "#F3EBDD"))
        p.poligono([(156, 304 + dy), (244, 304 + dy), (232, 420), (168, 420)], blusa, w=2)
        p.linha([(200, 330 + dy), (200, 420)], _escurecer(roupa, 0.7), 2)
        for k in range(3):
            p.elipse((228, 340 + dy + k * 24, 236, 348 + dy + k * 24), _escurecer(roupa, 0.6), contorno=None)


def _cabelo_atras(p: _Pincel, a: dict, dy: float):
    cab = _c(a["cabelo"])
    est = a.get("penteado", "curto")
    if est == "coque":
        p.elipse((112, 120 + dy, 288, 290 + dy), cab)
        p.elipse((166, 44 + dy, 234, 108 + dy), cab)
    elif est == "longo":
        p.ret((110, 120 + dy, 290, 320 + dy), cab, raio=60)


def _cabeca(p: _Pincel, a: dict, dy: float):
    pele = _c(a["pele"])
    p.elipse((112, 168 + dy, 140, 214 + dy), pele)          # orelhas
    p.elipse((260, 168 + dy, 288, 214 + dy), pele)
    p.elipse((126, 92 + dy, 274, 280 + dy), pele)           # rosto
    bochecha = tuple(min(255, int(c * 1.0 + d)) for c, d in zip(pele, (25, -10, -10)))
    p.elipse((144, 212 + dy, 172, 232 + dy), bochecha, contorno=None)
    p.elipse((228, 212 + dy, 256, 232 + dy), bochecha, contorno=None)


def _cabelo_frente(p: _Pincel, a: dict, dy: float):
    cab = _c(a["cabelo"])
    est = a.get("penteado", "curto")
    if est == "careca_lados":
        p.corda((118, 130 + dy, 150, 210 + dy), 90, 270, cab, w=2)
        p.corda((250, 130 + dy, 282, 210 + dy), 270, 90, cab, w=2)
    elif est == "topete":
        p.poligono([(128, 160 + dy), (132, 112 + dy), (160, 84 + dy), (210, 74 + dy), (258, 92 + dy),
                    (276, 136 + dy), (272, 166 + dy), (252, 128 + dy), (214, 120 + dy), (190, 104 + dy),
                    (168, 124 + dy), (140, 136 + dy)], cab)
    elif est in ("coque", "longo"):
        p.poligono([(128, 176 + dy), (130, 128 + dy), (160, 96 + dy), (200, 88 + dy), (240, 96 + dy),
                    (270, 128 + dy), (272, 176 + dy), (250, 130 + dy), (206, 112 + dy), (176, 132 + dy), (146, 140 + dy)], cab)
    else:  # curto
        p.poligono([(128, 168 + dy), (134, 112 + dy), (170, 90 + dy), (232, 90 + dy), (266, 112 + dy),
                    (272, 168 + dy), (256, 128 + dy), (200, 116 + dy), (144, 128 + dy)], cab)


def _rosto(p: _Pincel, a: dict, dy: float, boca: int, olho_fechado: bool):
    cab = _c(a.get("sobrancelha", a["cabelo"]))
    pele = _c(a["pele"])
    # sobrancelhas (sobem um pouco quando a boca abre bem)
    sobe = 3 if boca >= 3 else 0
    p.linha([(154, 160 + dy - sobe), (168, 154 + dy - sobe), (184, 158 + dy - sobe)], cab, 6)
    p.linha([(216, 158 + dy - sobe), (232, 154 + dy - sobe), (246, 160 + dy - sobe)], cab, 6)
    # olhos
    for cx in (169, 231):
        if olho_fechado:
            p.arco((cx - 13, 168 + dy, cx + 13, 192 + dy), 200, 340, CONTORNO, 4)
        else:
            p.elipse((cx - 13, 168 + dy, cx + 13, 198 + dy), (255, 255, 255), w=2.5)
            p.elipse((cx - 7, 175 + dy, cx + 7, 193 + dy), (40, 30, 26), contorno=None)
            p.elipse((cx - 2, 177 + dy, cx + 3, 182 + dy), (255, 255, 255), contorno=None)
    # nariz
    p.arco((190, 192 + dy, 210, 222 + dy), 300, 80, _escurecer(pele, 0.6), 3)
    # acessórios do rosto
    if a.get("oculos"):
        cor = _c(a.get("cor_oculos", "#2B2B2B"))
        for cx in (169, 231):
            p.ret((cx - 23, 166 + dy, cx + 23, 200 + dy), None, raio=10, contorno=cor, w=4)
        p.linha([(192, 180 + dy), (208, 180 + dy)], cor, 4)
    if a.get("monoculo"):
        ouro = (226, 182, 72)
        p.elipse((210, 162 + dy, 252, 204 + dy), None, contorno=ouro, w=4)
        p.linha([(250, 196 + dy), (262, 250 + dy), (256, 300 + dy)], ouro, 2)
    # boca: 0 fechada, 1 entreaberta, 2 aberta, 3 bem aberta
    labio = (120, 40, 40)
    by = (256 if a.get("bigode") else 246) + dy
    if boca == 0:
        p.arco((180, by - 14, 220, by + 6), 20, 160, CONTORNO, 4)
    else:
        alt = (6, 14, 22)[boca - 1]
        larg = (18, 22, 24)[boca - 1]
        p.elipse((200 - larg, by - 6, 200 + larg, by - 6 + alt), labio, w=3)
        if boca >= 2:
            p.corda((200 - larg + 5, by - 6 + alt * 0.45, 200 + larg - 5, by - 6 + alt - 2), 0, 180, (214, 96, 96), contorno=None)
            p.ret((200 - larg + 6, by - 5, 200 + larg - 6, by - 1), (250, 250, 250), raio=1, contorno=None)
    if a.get("bigode"):
        cor = _c(a.get("cor_bigode", a["cabelo"]))
        p.poligono([(200, 228 + dy), (176, 226 + dy), (152, 236 + dy), (140, 228 + dy), (150, 244 + dy),
                    (176, 244 + dy), (200, 236 + dy)], cor, w=2)
        p.poligono([(200, 228 + dy), (224, 226 + dy), (248, 236 + dy), (260, 228 + dy), (250, 244 + dy),
                    (224, 244 + dy), (200, 236 + dy)], cor, w=2)


def _chapeu(p: _Pincel, a: dict, dy: float):
    if a.get("chapeu") == "cartola":
        preto = (30, 26, 28)
        p.ret((150, 18 + dy, 250, 112 + dy), preto, raio=6)
        p.ret((150, 86 + dy, 250, 104 + dy), _c(a.get("faixa_chapeu", "#C9A24A")), contorno=None)
        p.elipse((112, 98 + dy, 288, 128 + dy), preto)


def personagem(a: dict, fundo, destaque, boca=0, olho_fechado=False, dy=0.0) -> Image.Image:
    img = Image.new("RGB", (BASE * S, BASE * S))
    p = _Pincel(img)
    _cenario(p, a, fundo, destaque)
    _cabelo_atras(p, a, dy)
    _corpo(p, a, dy)
    _cabeca(p, a, dy)
    _cabelo_frente(p, a, dy)
    _rosto(p, a, dy, boca, olho_fechado)
    _chapeu(p, a, dy)
    return img.resize((BASE, BASE), Image.LANCZOS)


# ------------------------------------------------------------------ moldura da webcam
def _moldura(cfg: dict, rosto: Image.Image, tam: int) -> Image.Image:
    a = cfg["apresentador"]
    est = cfg["estilo"]
    fundo, destaque, texto = _c(est["fundo"]), _c(est["destaque"]), _c(est.get("texto", "#FFFFFF"))
    borda = max(4, tam // 70)
    tag_h = int(tam * 0.15)
    W, H = tam + borda * 2, tam + borda * 2 + tag_h // 2
    out = Image.new("RGBA", (W + 24, H + 24), (0, 0, 0, 0))
    # sombra
    sombra = Image.new("RGBA", out.size, (0, 0, 0, 0))
    ImageDraw.Draw(sombra).rounded_rectangle((12, 16, 12 + W, 16 + tam + borda * 2), radius=tam // 12, fill=(0, 0, 0, 150))
    out.alpha_composite(sombra.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(out)
    d.rounded_rectangle((12, 12, 12 + W, 12 + tam + borda * 2), radius=tam // 12, fill=destaque + (255,))
    mascara = Image.new("L", (tam, tam), 0)
    ImageDraw.Draw(mascara).rounded_rectangle((0, 0, tam - 1, tam - 1), radius=tam // 14, fill=255)
    out.paste(rosto.resize((tam, tam), Image.LANCZOS), (12 + borda, 12 + borda), mascara)
    # "AO VIVO"
    f = fonte(cfg.get("estilo", {}).get("fonte_texto", "Inter.ttf"), max(12, tam // 18), "Bold")
    x0, y0 = 12 + borda + tam // 22, 12 + borda + tam // 22
    w = f.getlength("AO VIVO")
    d.rounded_rectangle((x0, y0, x0 + w + tam // 9, y0 + tam // 11), radius=tam // 40, fill=(0, 0, 0, 150))
    r = tam // 50
    d.ellipse((x0 + tam // 40, y0 + tam // 22 - r, x0 + tam // 40 + 2 * r, y0 + tam // 22 + r), fill=(235, 50, 50))
    d.text((x0 + tam // 40 + 2 * r + tam // 60, y0 + tam // 22), "AO VIVO", font=f, fill=(255, 255, 255), anchor="lm")
    # plaquinha com o nome
    nome = a.get("nome", "")
    if nome:
        fn = fonte(est.get("fonte_titulo", "Inter.ttf"), int(tag_h * 0.55), est.get("fonte_titulo_variacao"))
        wn = fn.getlength(nome) + tag_h
        xn = 12 + (W - wn) / 2
        yn = 12 + tam + borda * 2 - tag_h // 2
        d.rounded_rectangle((xn, yn, xn + wn, yn + tag_h), radius=tag_h // 2, fill=fundo + (255,), outline=destaque, width=borda)
        d.text((xn + wn / 2, yn + tag_h / 2), nome, font=fn, fill=texto, anchor="mm")
    return out


def sprites(cfg: dict, pasta: Path, tam: int) -> dict:
    """Gera os quadros possíveis (boca 0–3 × olho aberto/fechado × 3 alturas de respiração)."""
    a = cfg["apresentador"]
    fundo, destaque = _c(cfg["estilo"]["fundo"]), _c(cfg["estilo"]["destaque"])
    pasta.mkdir(parents=True, exist_ok=True)
    mapa = {}
    for boca in range(4):
        for olho in (False, True):
            for k, dy in enumerate((0.0, -2.0, -4.0)):
                arq = pasta / f"cam_b{boca}_o{int(olho)}_r{k}.png"
                _moldura(cfg, personagem(a, fundo, destaque, boca, olho, dy), tam).save(arq)
                mapa[(boca, olho, k)] = arq
    return mapa


# ------------------------------------------------------------------ sincronia com a voz
def _volumes(audio: Path, fps: int) -> np.ndarray:
    sr = 8000
    bruto = subprocess.run(["ffmpeg", "-v", "error", "-i", str(audio), "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"],
                           capture_output=True, check=True).stdout
    x = np.frombuffer(bruto, dtype=np.int16).astype(np.float32) / 32768
    n = sr // fps
    q = len(x) // n
    return np.sqrt((x[: q * n].reshape(q, n) ** 2).mean(axis=1) + 1e-12)


def _bocas(vol: np.ndarray) -> list[int]:
    ref = np.percentile(vol, 95) or 1.0
    v = np.clip(vol / ref, 0, 1)
    out, ant = [], 0
    for i, x in enumerate(v):
        alvo = 0 if x < 0.12 else 1 if x < 0.35 else 2 if x < 0.65 else 3
        # nunca pula de fechada para bem aberta em um quadro (fica menos robótico)
        alvo = min(alvo, ant + 2) if alvo > ant else max(alvo, ant - 2)
        out.append(alvo)
        ant = alvo
    # tira tremidinhas de 1 quadro
    for i in range(1, len(out) - 1):
        if out[i - 1] == out[i + 1] != out[i]:
            out[i] = out[i - 1]
    return out


def faixa(cfg: dict, audio: Path, tmp: Path) -> tuple[Path, int, int] | None:
    """Vídeo (sem áudio) só da webcam, do tamanho do áudio. Devolve (arquivo, x, y) no quadro 1080p."""
    a = cfg.get("apresentador") or {}
    if not a.get("ligado"):
        return None
    tam = int(ALTURA * a.get("tamanho", 0.30))
    spr = sprites(cfg, tmp / "webcam", tam)
    bocas = _bocas(_volumes(audio, FPS))
    rnd = random.Random(7)
    proximo_piscar = rnd.randint(60, 150)
    linhas, atual, cont = [], None, 0
    for i, b in enumerate(bocas):
        olho = proximo_piscar <= i < proximo_piscar + 4
        if i >= proximo_piscar + 4:
            proximo_piscar = i + rnd.randint(75, 170)
        resp = int(1 + math.sin(i / FPS * 2 * math.pi / 3.2) + 0.5)   # respira devagar (0, 1 ou 2)
        chave = (b, olho, max(0, min(2, resp)))
        if chave == atual:
            cont += 1
        else:
            if atual is not None:
                linhas.append((spr[atual], cont))
            atual, cont = chave, 1
    if atual is not None:
        linhas.append((spr[atual], cont))
    lista = tmp / "webcam.txt"
    with lista.open("w", encoding="utf-8") as f:
        for arq, n in linhas:
            f.write(f"file '{arq.resolve()}'\nduration {n / FPS:.5f}\n")
        f.write(f"file '{linhas[-1][0].resolve()}'\n")
    saida = tmp / "webcam.mov"
    rodar(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lista),
           "-vf", f"fps={FPS},format=yuva444p10le", "-c:v", "prores_ks", "-profile:v", "4444", "-qscale:v", "12",
           str(saida)], timeout=3600)
    w, h = Image.open(next(iter(spr.values()))).size
    margem = int(ALTURA * 0.025)
    canto = a.get("posicao", "inferior_direita")
    x = margem if "esquerda" in canto else LARGURA - w - margem + 12
    y = margem if "superior" in canto else ALTURA - h - margem + 12
    return saida, x, y


def sobrepor(video: Path, cfg: dict, tmp: Path, saida: Path) -> Path:
    """Põe a webcam por cima do vídeo narrado. Sem apresentador ligado, devolve o vídeo como está."""
    f = faixa(cfg, video, tmp)
    if not f:
        return video
    cam, x, y = f
    from .render import AAC, X264
    rodar(["ffmpeg", "-y", "-v", "error", "-i", str(video), "-i", str(cam),
           "-filter_complex", f"[0:v][1:v]overlay={x}:{y}:eof_action=pass:format=auto[v]",
           "-map", "[v]", "-map", "0:a", *X264, "-c:a", "copy", str(saida)], timeout=7200)
    log.info("apresentador na webcam aplicado (%s)", cfg["apresentador"].get("nome", ""))
    return saida


if __name__ == "__main__":
    canal = sys.argv[1] if len(sys.argv) > 1 else "historia"
    cfg = carregar_config(canal)
    destino = RAIZ / "saida"
    destino.mkdir(exist_ok=True)
    a, est = cfg["apresentador"], cfg["estilo"]
    quadros = [_moldura(cfg, personagem(a, _c(est["fundo"]), _c(est["destaque"]), b, o), 420)
               for b, o in ((0, False), (1, False), (2, False), (3, False), (0, True))]
    folha = Image.new("RGBA", (sum(q.width for q in quadros) + 20 * 6, quadros[0].height + 40), (60, 60, 60, 255))
    x = 20
    for q in quadros:
        folha.alpha_composite(q, (x, 20))
        x += q.width + 20
    folha.convert("RGB").save(destino / f"apresentador-{canal}.png")
    print(destino / f"apresentador-{canal}.png")
