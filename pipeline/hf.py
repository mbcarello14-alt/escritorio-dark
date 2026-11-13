"""Cenas animadas renderizadas pelo HyperFrames (HTML + GSAP → vídeo, quadro a quadro).

Mesmo formato de cena do motor antigo (`pipeline/animacao/FORMATO.md`): mapa, contador, linha_tempo e imagem
(ilustração "viva" com título, partículas, neblina e luzes). Cada cena vira um projetinho HyperFrames, é
renderizada sem som e convertida para o mesmo padrão de vídeo do motor; o som (voz + efeitos) entra depois,
em `animar.clipe`. Ligado por canal com `estilo.motor_animacao: hyperframes`. Se falhar, o motor usa o antigo.

Teste: python -m pipeline.hf teste <cena.json> <saida.mp4> [segundos]
"""
from __future__ import annotations

import html as H
import json
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path

from .comum import FPS, RAIZ, log, rodar

DIR = RAIZ / "pipeline" / "hf"
W, H_ = 1920, 1080
CORES = {"ouro": "rgba(201,162,74,.62)", "cinza": "rgba(105,100,94,.72)", "vermelho": "rgba(168,64,44,.45)",
         "verde": "rgba(98,122,72,.6)", "azul": "rgba(58,88,128,.6)", "roxo": "rgba(104,72,120,.6)",
         "laranja": "rgba(214,120,52,.6)", "marrom": "rgba(122,88,56,.7)"}


def _cor(c, padrao):
    return CORES.get(c, c) if c else padrao


def _e(t) -> str:
    return H.escape(str(t), quote=True)


def _letras(t: str) -> str:
    return "".join(f"<span>{'&nbsp;' if ch == ' ' else _e(ch)}</span>" for ch in t)


def _palavras(t: str) -> str:
    return "".join(f"<span>{_e(w)}</span>" for w in t.split())


def _em(it: dict, i: int, base: float, passo: float) -> float:
    return it["em"] if it.get("em") is not None else min(0.8, base + i * passo)


# ---------------------------------------------------------------- peças comuns
CSS_BASE = """
@font-face { font-family: "Oswald"; src: url("assets/fonts/Oswald-Bold.ttf"); font-weight: 700; }
@font-face { font-family: "Oswald"; src: url("assets/fonts/Oswald-Medium.ttf"); font-weight: 500; }
:root { --mar:#4A6F86; --mar2:#34566A; --terra:#E9DDC1; --borda:#B9A57F; --tinta:#221B13; --creme:#F3EBDD; --ouro:#C9A24A; --laranja:#E2782E; }
* { margin:0; padding:0; box-sizing:border-box; }
html, body { width:1920px; height:1080px; overflow:hidden; background:#0d0b08; }
#root { position:relative; width:1920px; height:1080px; overflow:hidden; font-family:"Oswald"; }
#cena { position:absolute; inset:0; }
#vinheta { position:absolute; inset:0; pointer-events:none; background:radial-gradient(ellipse at 50% 50%, rgba(0,0,0,0) 55%, rgba(0,0,0,.42) 100%); }
#grao { position:absolute; inset:-40px; opacity:.08; mix-blend-mode:overlay; pointer-events:none;
  background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='300' height='300'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' seed='4'/></filter><rect width='300' height='300' filter='url(%23n)'/></svg>"); }
#sombraTit { position:absolute; left:0; bottom:0; width:1500px; height:520px; background:radial-gradient(ellipse at 0% 100%, rgba(0,0,0,.72), rgba(0,0,0,.35) 45%, rgba(0,0,0,0) 72%); }
#tit { position:absolute; left:84px; bottom:178px; font-weight:700; font-size:100px; letter-spacing:2px; color:var(--creme); text-shadow:0 4px 18px rgba(0,0,0,.55); white-space:nowrap; }
#tit.peq { font-size:62px; bottom:150px; }
#tit span, #sub span { display:inline-block; }
#linhaTit { position:absolute; left:84px; bottom:160px; height:5px; background:var(--ouro); transform-origin:0 50%; }
#tit.peq ~ #linhaTit { bottom:136px; }
#sub { position:absolute; left:84px; bottom:104px; font-weight:500; font-size:34px; letter-spacing:4px; color:rgba(243,235,221,.92); text-shadow:0 2px 10px rgba(0,0,0,.6); white-space:nowrap; text-transform:uppercase; }
#sub span { margin-right:12px; }
"""


def _titulo_html(ti: dict | None) -> str:
    if not ti or not ti.get("titulo"):
        return ""
    t = str(ti["titulo"]).upper()
    larg = min(1700, max(300, int(len(t) * (34 if ti.get("pequeno") else 56))))
    sub = f'<div id="sub">{_palavras(ti["subtitulo"])}</div>' if ti.get("subtitulo") else ""
    return (f'<div id="sombraTit"></div><div id="tit" class="{"peq" if ti.get("pequeno") else ""}">{_letras(t)}</div>'
            f'<div id="linhaTit" style="width:{larg}px"></div>{sub}')


def _titulo_js(ti: dict | None) -> str:
    if not ti or not ti.get("titulo"):
        return ""
    em = ti.get("em") if ti.get("em") is not None else 0.12
    return f"""
gsap.set("#sombraTit", {{ opacity: 0 }}); gsap.set("#tit span", {{ opacity: 0, filter: "blur(10px)" }});
gsap.set("#linhaTit", {{ scaleX: 0 }}); gsap.set("#sub span", {{ opacity: 0 }});
tl.to("#sombraTit", {{ opacity: 1, duration: 0.5, ease: "power2.out" }}, em({em}));
tl.to("#tit span", {{ opacity: 1, filter: "blur(0px)", duration: 0.18, ease: "power2.out", stagger: 0.04 }}, em({em}) + 0.15);
tl.to("#linhaTit", {{ scaleX: 1, duration: 0.7, ease: "expo.out" }}, em({em}) + 0.4);
tl.to("#sub span", {{ opacity: 1, duration: 0.2, ease: "power2.out", stagger: 0.08 }}, em({em}) + 0.7);
"""


def _pagina(dur: float, css: str, corpo: str, js: str) -> str:
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=1920, height=1080">
<script src="assets/gsap.min.js"></script>
<style>{CSS_BASE}{css}</style></head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{dur:.3f}" data-width="1920" data-height="1080">
  <div id="cena" class="clip" data-start="0" data-duration="{dur:.3f}" data-track-index="0" data-layout-allow-overflow data-layout-allow-overlap data-layout-allow-occlusion>
{corpo}
    <div id="vinheta"></div><div id="grao"></div>
  </div>
</div>
<script>
const D = {dur:.3f};
const em = x => x * D;
const tl = gsap.timeline({{ paused: true }});
{js}
window.__timelines["main"] = tl;
</script>
</body></html>"""


# ---------------------------------------------------------------- modelos
def _mapa(cena: dict, dur: float, pasta: Path) -> str:
    entrada, saida = pasta / "cena.json", pasta / "geo.json"
    entrada.write_text(json.dumps(cena, ensure_ascii=False), encoding="utf-8")
    rodar(["node", str(DIR / "mapa.mjs"), str(entrada), str(saida)], timeout=120)
    g = json.loads(saida.read_text(encoding="utf-8"))
    ondas = "".join(f"M{x - 9},{y} q5,-6 9,0 t9,0 " for x, y in g["ondas"])
    svg = [f'<svg id="mapa" width="{g["W"]}" height="{g["H"]}" viewBox="0 0 {g["W"]} {g["H"]}" style="position:absolute;left:0;top:0">',
           f'<defs><clipPath id="soTerra"><path d="{g["terra"]}"/></clipPath>']
    for i, a in enumerate(g["areas"]):
        svg.append(f'<clipPath id="cresce{i}"><circle id="raio{i}" cx="{a["centro"][0]}" cy="{a["centro"][1]}" r="0"/></clipPath>')
    for i, r in enumerate(g["rotas"]):
        svg.append(f'<mask id="m{i}"><path id="mr{i}" d="{r["d"]}" fill="none" stroke="#fff" stroke-width="16" stroke-linecap="round" stroke-linejoin="round"/></mask>')
    svg.append("</defs>")
    svg.append(f'<rect width="{g["W"]}" height="{g["H"]}" fill="url(#marG)"/>')
    svg.append(f'<path d="{ondas}" fill="none" stroke="rgba(230,240,245,.2)" stroke-width="2.4" stroke-linecap="round"/>')
    for w, a in ((22, ".16"), (8, ".24")):
        svg.append(f'<path d="{g["terra"]}" fill="none" stroke="rgba(25,45,60,{a})" stroke-width="{w}" stroke-linejoin="round"/>')
    svg.append(f'<path d="{g["terra"]}" fill="var(--terra)" stroke="var(--borda)" stroke-width="1.6"/>')
    svg.append(f'<path d="{g["bordas"]}" fill="none" stroke="rgba(130,110,80,.32)" stroke-width="1.2"/>')
    for i, (p, gp) in enumerate(zip(cena.get("paises", []), g["paises"])):
        svg.append(f'<path id="pa{i}" d="{gp["d"]}" fill="{_cor(p.get("cor"), CORES["ouro"])}" stroke="rgba(60,45,30,.55)" stroke-width="1.8"/>')
    for i, (a, ga) in enumerate(zip(cena.get("areas", []), g["areas"])):
        cres = a.get("crescer", True) is not False
        svg.append(f'<g clip-path="url(#soTerra)"><g id="ar{i}" {"clip-path=" + chr(34) + f"url(#cresce{i})" + chr(34) if cres else ""}>'
                   f'<path d="{ga["d"]}" fill="{_cor(a.get("cor"), CORES["vermelho"])}" stroke="rgba(70,35,20,.85)" stroke-width="3" stroke-dasharray="12 8"/></g></g>')
    for i, (r, gr) in enumerate(zip(cena.get("rotas", []), g["rotas"])):
        svg.append(f'<g mask="url(#m{i})"><path id="rb{i}" d="{gr["d"]}" fill="none" stroke="rgba(243,235,221,.6)" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/>'
                   f'<path d="{gr["d"]}" fill="none" stroke="{_cor(r.get("cor"), "#2E241A")}" stroke-width="4.5" stroke-dasharray="16 11" stroke-linecap="round"/></g>')
    svg.append("</svg>")
    divs = []
    for i, (c, xy) in enumerate(zip(cena.get("cidades", []), g["cidades"])):
        lado = " esq" if c.get("lado") == "esquerda" else ""
        brilho = f'<div class="brilho" id="br{i}"></div>' if c.get("destaque") else ""
        divs.append(f'<div class="cidade{lado} fixo" id="ci{i}" data-px="{xy[0]}" data-py="{xy[1]}">{brilho}<div class="ponto"></div>'
                    f'<div class="nome">{_e(str(c.get("nome", "")).upper())}</div></div>')
    rot = []
    for i, (p, gp) in enumerate(zip(cena.get("paises", []), g["paises"])):
        if p.get("rotulo") and gp["centro"]:
            rot.append(("pais", p["rotulo"], gp["centro"], _em(p, i, 0.05, 0.1) + 0.04))
    for i, (a, ga) in enumerate(zip(cena.get("areas", []), g["areas"])):
        if a.get("rotulo"):
            rot.append(("pais", a["rotulo"], ga["centro"], _em(a, i, 0.06, 0.12) + 0.08))
    for i, (r, xy) in enumerate(zip(cena.get("rotulos", []), g["rotulos"])):
        rot.append((r.get("tipo", "pais"), r["texto"], xy, _em(r, i, 0.1, 0.1)))
    for k, (tipo, txt, xy, _) in enumerate(rot):
        divs.append(f'<div class="fixo rotw" data-px="{xy[0]}" data-py="{xy[1]}"><div class="rot {tipo}" id="ro{k}">{_e(str(txt).upper())}</div></div>')
    cargas = []
    for i, r in enumerate(cena.get("rotas", [])):
        c = r.get("carga")
        if c == "navio":
            ic = ('<svg width="90" height="80" viewBox="-45 -60 90 80" style="position:absolute;left:-45px;top:-60px;overflow:visible">'
                  '<path d="M-32 2 L32 2 L22 16 L-23 16 Z" fill="#5A3E26"/><rect x="-2" y="-40" width="4" height="42" fill="#3A2A1C"/>'
                  '<path d="M3 -37 Q27 -19 3 -3 Z" fill="#F3EBDD"/><path d="M-3 -34 Q-24 -17 -3 -4 Z" fill="#F3EBDD"/></svg>')
        elif c in ("moeda", "ouro"):
            ic = '<div class="moeda"></div>'
        else:
            ic = '<div class="pontoRota"></div>'
        cargas.append(f'<div class="carga" id="cg{i}"><div class="vira" id="cv{i}">{ic}</div></div>')
    css = f"""
#cam {{ position:absolute; left:0; top:0; width:{g["W"]}px; height:{g["H"]}px; transform-origin:0 0; }}
#sobre {{ position:absolute; inset:0; }}
.fixo {{ position:absolute; left:0; top:0; width:0; height:0; }}
.cidade {{ position:absolute; width:0; height:0; }}
.cidade .ponto {{ position:absolute; left:-11px; top:-11px; width:22px; height:22px; border-radius:50%; background:#1E1812; border:4px solid var(--creme); }}
.cidade .nome {{ position:absolute; left:20px; top:-17px; font-weight:500; font-size:28px; letter-spacing:2px; color:#1E1812; text-shadow:0 0 6px var(--creme),0 0 3px var(--creme),0 0 2px var(--creme); white-space:nowrap; }}
.cidade.esq .nome {{ left:auto; right:20px; }}
.brilho {{ position:absolute; left:-70px; top:-70px; width:140px; height:140px; border-radius:50%; background:radial-gradient(circle, rgba(255,150,60,.95) 0%, rgba(240,120,45,.5) 35%, rgba(240,120,45,0) 70%); }}
.rot {{ position:absolute; white-space:nowrap; }}
.rot.pais {{ font-weight:700; font-size:50px; letter-spacing:6px; color:var(--tinta); text-shadow:0 0 8px var(--creme),0 0 4px var(--creme),0 0 2px var(--creme); }}
.rot.mar {{ font-weight:500; font-size:30px; letter-spacing:14px; color:rgba(232,240,245,.75); }}
.rot.destaque {{ font-weight:500; font-size:28px; letter-spacing:3px; color:#A9481A; text-shadow:0 0 6px var(--creme),0 0 3px var(--creme); }}
.carga {{ position:absolute; left:0; top:0; width:0; height:0; }}
.moeda {{ position:absolute; left:-16px; top:-16px; width:32px; height:32px; border-radius:50%; background:radial-gradient(circle at 35% 35%, #FFE7A0, #D9AE48 60%, #A9822E); border:3px solid #8F6A1E; }}
.pontoRota {{ position:absolute; left:-7px; top:-7px; width:14px; height:14px; border-radius:50%; background:#2E241A; }}
"""
    corpo = (f'<div id="cam">{"".join(svg)}{"".join(cargas)}</div><div id="sobre">{"".join(divs)}</div>'
             f'<svg width="0" height="0" style="position:absolute"><defs><radialGradient id="marG" cx="50%" cy="45%" r="75%">'
             f'<stop offset="0" stop-color="#4A6F86"/><stop offset="1" stop-color="#34566A"/></radialGradient></defs></svg>'
             + _titulo_html(cena.get("titulo_inferior")))
    ini, fim = g["inicio"], g["fim"]
    cam_em = cena.get("camera_em", 0.2) if cena.get("camera_em") is not None else 0.2
    js = [f"const cam = document.getElementById('cam');",
          "const cena = (s, cx, cy) => ({ scale: s, x: 960 - cx * s, y: 540 - cy * s });",
          f"gsap.set(cam, cena({ini['s']}, {ini['cx']}, {ini['cy']}));",
          "tl.fromTo('#mapa', { opacity: 0.4 }, { opacity: 1, duration: 0.5, ease: 'power2.out' }, 0);",
          # posiciona cidades e rótulos pela câmera a cada quadro (eles não crescem com o zoom)
          "const fixos = [...document.querySelectorAll('.fixo')];",
          "const sync = () => { const s = gsap.getProperty(cam, 'scale'), x = gsap.getProperty(cam, 'x'), y = gsap.getProperty(cam, 'y');"
          " fixos.forEach(f => gsap.set(f, { x: x + f.dataset.px * s, y: y + f.dataset.py * s })); };",
          "tl.to({}, { duration: D, onUpdate: sync }, 0);",
          "gsap.set('.rot', { xPercent: -50, yPercent: -50 });"]
    if fim:
        js.append(f"tl.to(cam, {{ ...cena({ini['s'] * 1.03}, {ini['cx']}, {ini['cy']}), duration: Math.max(0.1, em({cam_em})), ease: 'none' }}, 0);")
        js.append(f"tl.to(cam, {{ ...cena({fim['s']}, {fim['cx']}, {fim['cy']}), duration: Math.min(2.4, Math.max(1.0, em(0.45))), ease: 'power2.inOut' }}, em({cam_em}));")
    else:
        js.append(f"tl.to(cam, {{ ...cena({ini['s'] * 1.05}, {ini['cx']}, {ini['cy']}), duration: D, ease: 'none' }}, 0);")
    for i, p in enumerate(cena.get("paises", [])):
        t = _em(p, i, 0.05, 0.1)
        js.append(f"gsap.set('#pa{i}', {{ opacity: 0 }}); tl.to('#pa{i}', {{ opacity: 1, duration: 0.6, ease: 'power2.out' }}, em({t}));")
    for i, a in enumerate(cena.get("areas", [])):
        t = _em(a, i, 0.06, 0.12)
        if a.get("crescer", True) is not False:
            js.append(f"tl.to('#raio{i}', {{ attr: {{ r: 2600 }}, duration: Math.min(2.2, Math.max(1.0, em(0.35))), ease: 'power2.inOut' }}, em({t}));")
        else:
            js.append(f"gsap.set('#ar{i}', {{ opacity: 0 }}); tl.to('#ar{i}', {{ opacity: 1, duration: 0.6, ease: 'power2.out' }}, em({t}));")
    for i, r in enumerate(cena.get("rotas", [])):
        t = _em(r, i, 0.15, 0.15)
        d = r.get("duracao", 0.4)
        js.append(f"""{{ const m = document.getElementById('mr{i}'), b = document.getElementById('rb{i}'), L = m.getTotalLength(), LB = b.getTotalLength();
  gsap.set(m, {{ strokeDasharray: L, strokeDashoffset: L }}); gsap.set('#cg{i}', {{ opacity: 0 }});
  const pr = {{ p: 0 }};
  const pos = () => {{ const a = b.getPointAtLength(pr.p * LB), c = b.getPointAtLength(Math.min(LB, pr.p * LB + 4));
    gsap.set('#cg{i}', {{ x: a.x, y: a.y }}); gsap.set('#cv{i}', {{ scaleX: c.x < a.x ? -1 : 1 }}); m.style.strokeDashoffset = L * (1 - pr.p); }};
  tl.to('#cg{i}', {{ opacity: 1, duration: 0.2 }}, em({t}));
  tl.to(pr, {{ p: 1, duration: Math.min(5, Math.max(1.2, em({d}))), ease: 'power1.inOut', onUpdate: pos }}, em({t}));
  pos(); }}""")
    for i, c in enumerate(cena.get("cidades", [])):
        t = _em(c, i, 0.12, 0.09)
        js.append(f"gsap.set('#ci{i}', {{ scale: 0 }}); tl.to('#ci{i}', {{ scale: 1, duration: 0.55, ease: 'back.out(2.2)' }}, em({t}));")
        if c.get("destaque"):
            reps = max(1, int((dur - t * dur) / 1.4))
            js.append(f"tl.fromTo('#br{i}', {{ scale: 0.6 }}, {{ scale: 1.15, duration: 0.7, ease: 'sine.inOut', yoyo: true, repeat: {reps} }}, em({t}) + 0.1);")
    for k, (_, _, _, t) in enumerate(rot):
        js.append(f"gsap.set('#ro{k}', {{ opacity: 0 }}); tl.to('#ro{k}', {{ opacity: 1, duration: 0.5, ease: 'power2.out' }}, em({t}));"
                  f"tl.fromTo('#ro{k}', {{ scale: 1.1, filter: 'blur(6px)' }}, {{ scale: 1, filter: 'blur(0px)', duration: 0.8, ease: 'expo.out' }}, em({t}));")
    js.append(_titulo_js(cena.get("titulo_inferior")))
    js.append("sync();")
    return _pagina(dur, css, corpo, "\n".join(js))


def _contador(cena: dict, dur: float, pasta: Path) -> str:
    de, ate = float(cena.get("de", 0)), float(cena["ate"])
    casas = cena.get("casas", 0 if float(ate).is_integer() else 1)
    moedas = ""
    for i in range(16):
        x = (i * 137) % 1880 + 20
        moedas += f'<div class="mo" id="mo{i}" style="left:{x}px"></div>'
    css = """
#fundoC { position:absolute; inset:0; background:radial-gradient(ellipse at 50% 45%, #2B2218, #14110D 75%); }
.mo { position:absolute; top:-80px; width:44px; height:44px; border-radius:50%; background:radial-gradient(circle at 35% 35%, #FFE7A0, #D9AE48 60%, #A9822E); border:3px solid #8F6A1E; opacity:.75; }
#num .suf { font-size:0.42em; letter-spacing:1px; margin-left:0.18em; }
#num .pre { font-size:0.5em; margin-right:0.12em; }
#num { position:absolute; left:50%; top:47%; font-weight:700; font-size:200px; letter-spacing:2px; white-space:nowrap;
  color:#E9C870; background:linear-gradient(180deg, #F7DE93, #C9A24A 55%, #9C7A2C); -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent; }
#rotC { position:absolute; left:50%; top:66%; font-weight:500; font-size:42px; letter-spacing:6px; color:var(--creme); white-space:nowrap; text-transform:uppercase; }
#linhaC { position:absolute; left:50%; top:73%; width:260px; margin-left:-130px; height:4px; background:var(--ouro); transform-origin:50% 50%; }
#comp { position:absolute; left:50%; top:78%; font-weight:500; font-size:36px; letter-spacing:2px; color:rgba(243,235,221,.85); white-space:nowrap; }
"""
    corpo = (f'<div id="fundoC"></div>{moedas}<div id="num"></div><div id="rotC">{_e(cena.get("rotulo", ""))}</div><div id="linhaC"></div>'
             + (f'<div id="comp">{_e(cena["comparacao"])}</div>' if cena.get("comparacao") else ""))
    js = f"""
const n = {{ v: {de} }};
const PRE = {json.dumps(cena.get("prefixo", "").strip())}, SUF = {json.dumps(cena.get("sufixo", "").strip())};
const fmt = v => Number(v).toLocaleString("pt-BR", {{ minimumFractionDigits: {casas}, maximumFractionDigits: {casas} }});
const num = document.getElementById("num");
const mostra = () => {{ num.innerHTML = (PRE ? `<span class="pre">${{PRE}}</span>` : "") + fmt({casas} === 0 ? Math.round(n.v) : n.v) + (SUF ? `<span class="suf">${{SUF}}</span>` : ""); }};
const larg = fmt({ate}).length + (PRE.length + SUF.length) * 0.45; num.style.fontSize = Math.min(220, Math.floor(1650 / (larg * 0.5))) + "px";
gsap.set(["#num", "#rotC", "#comp"], {{ xPercent: -50 }}); gsap.set("#num", {{ yPercent: -50 }});
const t0 = em(0.12), dc = Math.min(4, Math.max(1, em(0.5)));
gsap.set("#num", {{ opacity: 0, scale: 0.9 }});
tl.to("#num", {{ opacity: 1, scale: 1, duration: 0.5, ease: "expo.out" }}, em(0.05));
tl.to(n, {{ v: {ate}, duration: dc, ease: "power3.out", onUpdate: mostra }}, t0);
tl.to("#num", {{ scale: 1.06, duration: 0.15, ease: "power2.out", yoyo: true, repeat: 1 }}, t0 + dc);
gsap.set("#rotC", {{ opacity: 0, y: 20 }}); tl.to("#rotC", {{ opacity: 1, y: 0, duration: 0.6, ease: "expo.out" }}, em(0.08));
gsap.set("#linhaC", {{ scaleX: 0 }}); tl.to("#linhaC", {{ scaleX: 1, duration: 0.7, ease: "expo.out" }}, em(0.14));
gsap.set("#comp", {{ opacity: 0, y: 16 }}); tl.to("#comp", {{ opacity: 1, y: 0, duration: 0.6, ease: "expo.out" }}, t0 + dc + 0.3);
document.querySelectorAll(".mo").forEach((m, i) => {{
  const ini = (i * 0.37) % Math.max(0.5, D * 0.6);
  tl.fromTo(m, {{ y: 0, rotation: 0 }}, {{ y: 1240, rotation: 360 + i * 40, duration: 2.2 + (i % 5) * 0.35, ease: "power1.in" }}, ini);
}});
mostra();
"""
    return _pagina(dur, css, corpo, js)


def _linha_tempo(cena: dict, dur: float, pasta: Path) -> str:
    ev = cena.get("eventos") or []
    foco = min(int(cena.get("foco", len(ev) - 1)), len(ev) - 1)
    passo = 480
    itens = ""
    for i, e in enumerate(ev[:foco + 1]):
        cls = "ev foco" if i == foco else "ev"
        itens += (f'<div class="{cls}" id="ev{i}" style="left:{i * passo}px"><div class="ano">{_e(e.get("ano", ""))}</div>'
                  f'<div class="bola"></div><div class="txt">{_e(e.get("texto", ""))}</div></div>')
    css = """
#fundoL { position:absolute; inset:0; background:radial-gradient(ellipse at 50% 45%, #E8DCC2, #D8C7A3); }
#trilhaL { position:absolute; left:0; top:600px; width:100000px; }
#linhaL { position:absolute; left:-2000px; top:-3px; width:100000px; height:6px; background:#3B2F22; border-radius:3px; }
.ev { position:absolute; top:0; width:0; height:0; opacity:.5; }
.ev .bola { position:absolute; left:-15px; top:-15px; width:30px; height:30px; border-radius:50%; background:#6B5A44; border:4px solid #2B241B; }
.ev .ano { position:absolute; left:0; bottom:40px; font-weight:700; font-size:56px; color:#2B241B; white-space:nowrap; }
.ev .txt { position:absolute; left:-200px; top:46px; width:400px; text-align:center; font-weight:500; font-size:28px; letter-spacing:1px; color:#2B241B; text-transform:uppercase; line-height:1.25; }
.ev.foco { opacity:1; }
.ev.foco .bola { left:-22px; top:-22px; width:44px; height:44px; background:var(--ouro); box-shadow:0 0 0 14px rgba(226,120,46,.25); }
.ev.foco .ano { font-size:92px; }
.ev.foco .txt { font-size:34px; }
"""
    corpo = f'<div id="fundoL"></div><div id="trilhaL"><div id="linhaL"></div>{itens}</div>' + _titulo_html(cena.get("titulo_inferior"))
    ant = max(0, foco - 1)
    js = f"""
gsap.set(".ev .ano", {{ xPercent: -50 }});
gsap.set("#trilhaL", {{ x: 960 - {ant * passo} }});
tl.to("#trilhaL", {{ x: 960 - {foco * passo}, duration: Math.min(1.6, Math.max(0.6, em(0.3))), ease: "power2.inOut" }}, em(0.05));
gsap.set("#ev{foco}", {{ opacity: 0 }});
tl.to("#ev{foco}", {{ opacity: 1, duration: 0.3 }}, em(0.2));
tl.fromTo("#ev{foco} .bola", {{ scale: 0 }}, {{ scale: 1, duration: 0.5, ease: "back.out(2.4)" }}, em(0.2));
tl.fromTo("#ev{foco} .ano", {{ y: 30, filter: "blur(8px)" }}, {{ y: 0, filter: "blur(0px)", duration: 0.6, ease: "expo.out" }}, em(0.24));
tl.fromTo("#ev{foco} .txt", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.5 }}, em(0.32));
{_titulo_js(cena.get("titulo_inferior"))}
"""
    return _pagina(dur, css, corpo, js)


def _imagem(cena: dict, dur: float, pasta: Path) -> str:
    img = Path(cena["imagem"])
    destino = pasta / "assets" / ("cena" + (img.suffix if img.suffix else ".jpg"))
    shutil.copy(img, destino)
    mov = cena.get("movimento") or "zoom_in"
    de, para = {"zoom_in": ((1.02, 0, 0), (1.12, 0, 0)), "zoom_out": ((1.12, 0, 0), (1.02, 0, 0)),
                "pan_esquerda": ((1.12, 85, 0), (1.12, -85, 0)), "pan_direita": ((1.12, -85, 0), (1.12, 85, 0)),
                "sobe": ((1.12, 0, 43), (1.12, 0, -43))}.get(mov, ((1.02, 0, 0), (1.12, 0, 0)))
    tipo = cena.get("particulas")
    part = ""
    n = {"folhas": 22, "poeira": 45, "neve": 70, "brasas": 36, "moedas": 16, "chuva": 90}.get(tipo, 0)
    for i in range(n):
        x, y = (i * 211) % 1920, (i * 397) % 1080
        part += f'<div class="pt {tipo}" id="pt{i}" style="left:{x}px; top:{y}px"></div>'
    luzes = "".join(f'<div class="luz" id="lz{i}" style="left:{l["x"] * W}px; top:{l["y"] * H_}px; width:{(l.get("raio") or 0.18) * W * 2}px; '
                    f'height:{(l.get("raio") or 0.18) * W * 2}px"></div>' for i, l in enumerate(cena.get("luzes") or []))
    neb = '<div class="neb" id="nb0" style="top:520px"></div><div class="neb" id="nb1" style="top:720px"></div>' if cena.get("neblina") else ""
    css = """
#quadro { position:absolute; inset:0; overflow:hidden; }
#img { position:absolute; left:0; top:0; width:1920px; height:1080px; object-fit:cover; }
.pt { position:absolute; border-radius:50%; }
.pt.poeira { width:4px; height:4px; background:rgba(255,243,214,.6); }
.pt.brasas { width:6px; height:6px; background:#FF8A3A; box-shadow:0 0 8px #FFB347; }
.pt.neve { width:7px; height:7px; background:#fff; opacity:.8; }
.pt.chuva { width:2px; height:30px; border-radius:1px; background:rgba(221,230,238,.35); rotate:12deg; }
.pt.folhas { width:18px; height:9px; background:#B7772F; border-radius:50%; }
.pt.moedas { width:30px; height:30px; background:radial-gradient(circle at 35% 35%, #FFE7A0, #D9AE48 60%, #A9822E); border:2px solid #8F6A1E; }
.luz { position:absolute; translate:-50% -50%; border-radius:50%; mix-blend-mode:screen; background:radial-gradient(circle, rgba(255,196,110,.5), rgba(255,170,80,0) 70%); }
.neb { position:absolute; left:-600px; width:1600px; height:420px; border-radius:50%; background:radial-gradient(ellipse, rgba(235,225,205,.22), rgba(235,225,205,0) 70%); mix-blend-mode:screen; }
"""
    corpo = (f'<div id="quadro"><img id="img" src="assets/{destino.name}">{luzes}{neb}{part}</div>' + _titulo_html(cena.get("titulo_inferior")))
    js = [f"tl.fromTo('#img', {{ scale: {de[0]}, x: {de[1]}, y: {de[2]} }}, {{ scale: {para[0]}, x: {para[1]}, y: {para[2]}, duration: D, ease: 'sine.inOut' }}, 0);"]
    if n:
        vel = {"poeira": (-40, 25), "brasas": (-260, 30), "neve": (180, 25), "chuva": (1500, -260), "folhas": (160, 90), "moedas": (420, 0)}[tipo]
        js.append(f"""document.querySelectorAll('.pt').forEach((p, i) => {{
  const k = 0.6 + (i % 7) / 7, dy = {vel[0]} * k * D, dx = {vel[1]} * k * D * (i % 2 ? 1 : -1);
  tl.fromTo(p, {{ x: 0, y: 0, rotation: 0 }}, {{ x: dx, y: dy, rotation: {360 if tipo in ("folhas", "moedas") else 0} * k * D / 3, duration: D, ease: 'none' }}, 0);
  tl.fromTo(p, {{ opacity: 0.2 }}, {{ opacity: 0.9, duration: 0.6 + (i % 4) * 0.2, ease: 'sine.inOut', yoyo: true, repeat: Math.floor(D / (0.6 + (i % 4) * 0.2)) }}, 0);
}});""")
    for i, _ in enumerate(cena.get("luzes") or []):
        js.append(f"tl.fromTo('#lz{i}', {{ opacity: 0.75 }}, {{ opacity: 1, duration: 0.18, ease: 'sine.inOut', yoyo: true, repeat: Math.floor(D / 0.18) }}, 0);")
    if cena.get("neblina"):
        js.append("tl.fromTo('#nb0', { x: 0 }, { x: 420, duration: D, ease: 'none' }, 0); tl.fromTo('#nb1', { x: 500 }, { x: 0, duration: D, ease: 'none' }, 0);")
    js.append(_titulo_js(cena.get("titulo_inferior")))
    return _pagina(dur, css, corpo, "\n".join(js))


def _cenario_codigo(desc: str) -> str:
    """Cenário vetorial simples (céu, relevo, chão) escolhido pelas palavras da descrição."""
    d = desc.lower()
    if any(k in d for k in ("throne", "palace", "room", "hall", "interior", "church", "temple interior", "office", "court")):
        return ('<div class="camada" style="background:linear-gradient(#5E4632, #3E2E20)"></div>'
                '<svg class="camada" viewBox="0 0 2160 1080"><rect x="0" y="0" width="2160" height="760" fill="#6E5440"/>'
                + "".join(f'<rect x="{120 + k * 400}" y="120" width="70" height="640" fill="#5A4430"/>' for k in range(6))
                + '<rect x="840" y="160" width="480" height="380" rx="200" fill="#8E6E4E"/><rect x="0" y="760" width="2160" height="320" fill="#4A382A"/>'
                '<path d="M0 760 L2160 760" stroke="#2E2218" stroke-width="10"/></svg>')
    if any(k in d for k in ("sea", "port", "harbor", "beach", "coast", "ship", "ocean")):
        return ('<div class="camada" style="background:linear-gradient(#9EC3D6, #E8D9B8 70%)"></div>'
                '<svg class="camada" viewBox="0 0 2160 1080"><rect y="560" width="2160" height="300" fill="#4A7A92"/>'
                '<path d="M0 600 q40 -10 80 0 t80 0 t80 0 t80 0 t80 0 t80 0 t80 0 t80 0 t80 0 t80 0 t80 0 t80 0 t80 0 t80 0 t80 0 t80 0 t80 0 t80 0 t80 0 t80 0 t80 0 t80 0 t80 0 t80 0 t80 0 t80 0 t80 0" fill="none" stroke="#E8F0F4" stroke-opacity=".4" stroke-width="4"/>'
                '<path d="M0 800 Q540 760 1080 790 T2160 780 L2160 1080 L0 1080 Z" fill="#D9C08E"/></svg>')
    if any(k in d for k in ("desert", "dune", "egypt", "pyramid", "sand")):
        return ('<div class="camada" style="background:linear-gradient(#F2C98E, #F7E3B8)"></div>'
                '<svg class="camada" viewBox="0 0 2160 1080"><circle cx="1600" cy="300" r="90" fill="#FFF1C8"/>'
                '<path d="M200 760 L520 360 L840 760 Z" fill="#D9A866"/><path d="M760 760 L980 470 L1200 760 Z" fill="#C99858"/>'
                '<path d="M0 820 Q600 720 1200 800 T2160 790 L2160 1080 L0 1080 Z" fill="#E2B878"/></svg>')
    mont = any(k in d for k in ("mountain", "andes", "valley", "highland", "peak"))
    return ('<div class="camada" style="background:linear-gradient(#A9C7D8, #EDE0C2 75%)"></div>'
            '<svg class="camada" viewBox="0 0 2160 1080">'
            + ('<path d="M0 700 L260 380 L460 560 L760 260 L1060 600 L1320 340 L1640 620 L1900 400 L2160 640 L2160 1080 L0 1080 Z" fill="#8E9AA6"/>'
               '<path d="M690 330 L760 260 L830 330 Z M1260 400 L1320 340 L1380 400 Z" fill="#F3F3F0"/>' if mont else
               '<path d="M0 700 Q400 560 900 660 T2160 620 L2160 1080 L0 1080 Z" fill="#9FB08A"/>')
            + '</svg><svg class="camada" viewBox="0 0 2160 1080"><path d="M0 800 Q700 730 1300 790 T2160 770 L2160 1080 L0 1080 Z" fill="#B8A777"/>'
            '<path d="M0 860 Q800 820 2160 850 L2160 1080 L0 1080 Z" fill="#A38F60"/></svg>')


def _personagens(cena: dict, dur: float, pasta: Path) -> str:
    from . import personagens as P
    fundo = ""
    if cena.get("imagem"):
        img = Path(cena["imagem"])
        destino = pasta / "assets" / ("fundo" + (img.suffix or ".jpg"))
        shutil.copy(img, destino)
        fundo = f'<img id="fundo" src="assets/{destino.name}">'
    if not fundo:   # sem ilustração (cota de imagens): cenário desenhado por código, com camadas em parallax
        fundo = _cenario_codigo(cena.get("cenario", ""))
    bonecos = cena.get("personagens") or []
    css = """
.camada { position:absolute; left:-120px; top:0; width:2160px; height:1080px; }
#palco { position:absolute; inset:0; overflow:hidden; background:linear-gradient(#C9B48E, #8E7656); }
#fundo { position:absolute; left:0; top:0; width:1920px; height:1080px; object-fit:cover; }
#chaoSombra { position:absolute; left:0; right:0; bottom:0; height:260px; background:linear-gradient(rgba(0,0,0,0), rgba(0,0,0,.28)); }
.boneco { position:absolute; width:0; height:0; }
"""
    corpo = (f'<div id="palco"><div id="camP" style="position:absolute; inset:0; transform-origin:960px 700px">{fundo}<div id="chaoSombra"></div>'
             + "".join(P.boneco_html(i, b, dur) for i, b in enumerate(bonecos)) + "</div></div>" + _titulo_html(cena.get("titulo_inferior")))
    js = []
    mov = cena.get("movimento") or "zoom_in"
    alvo = {"zoom_in": (1.0, 1.08), "zoom_out": (1.08, 1.0)}.get(mov, (1.04, 1.04))
    dx = {"pan_esquerda": (40, -40), "pan_direita": (-40, 40)}.get(mov, (0, 0))
    js.append(f"tl.fromTo('#camP', {{ scale: {alvo[0]}, x: {dx[0]} }}, {{ scale: {alvo[1]}, x: {dx[1]}, duration: D, ease: 'sine.inOut' }}, 0);")
    js.append("tl.fromTo('#fundo', { x: 0 }, { x: -18, duration: D, ease: 'none' }, 0);")
    js.append("document.querySelectorAll('.camada').forEach((c, k) => tl.fromTo(c, { x: 0 }, { x: -12 - k * 22, duration: D, ease: 'none' }, 0));")   # parallax leve: o fundo anda menos que os bonecos
    js.append("const POSAR = []; const posar = () => POSAR.forEach(f => f());")
    for i, b in enumerate(bonecos):
        js.append(f"gsap.set('#bn{i}', {{ opacity: 0 }}); tl.to('#bn{i}', {{ opacity: 1, duration: 0.35, ease: 'power2.out' }}, 0.05);")
        js.append(P.boneco_js(i, b, dur, cena.get("boca"), FPS))
    js.append(_titulo_js(cena.get("titulo_inferior")))
    js.append("tl.eventCallback('onUpdate', posar); tl.to({}, { duration: D, onUpdate: posar }, 0); posar();")
    return _pagina(dur, css, corpo, "\n".join(js))


MODELOS = {"mapa": _mapa, "contador": _contador, "linha_tempo": _linha_tempo, "imagem": _imagem, "personagens": _personagens}


# ---------------------------------------------------------------- render
def _hyperframes() -> list[str]:
    local = DIR / "node_modules" / ".bin" / "hyperframes"
    return [str(local)] if local.exists() else ["npx", "--yes", "hyperframes@0.9.40"]


class AnimadorHF:
    """Mesma interface do animar.Animador: video(cena, saida) → mp4 sem som, no padrão do motor."""

    def __init__(self, tmp: Path):
        self.tmp = tmp / "hf"
        self.tmp.mkdir(parents=True, exist_ok=True)
        self.n = 0
        self.falhou = False

    def video(self, cena: dict, saida: Path) -> Path:
        if self.falhou:
            raise RuntimeError("HyperFrames indisponível nesta execução")
        self.n += 1
        proj = self.tmp / f"c{self.n:03d}"
        if proj.exists():
            shutil.rmtree(proj)
        (proj / "assets" / "fonts").mkdir(parents=True)
        for f in ("Oswald-Bold.ttf", "Oswald-Medium.ttf"):
            shutil.copy(RAIZ / "assets" / "fonts" / f, proj / "assets" / "fonts" / f)
        gsap = DIR / "node_modules" / "gsap" / "dist" / "gsap.min.js"
        shutil.copy(gsap, proj / "assets" / "gsap.min.js")
        (proj / "hyperframes.json").write_text(json.dumps({"paths": {"assets": "assets"}}), encoding="utf-8")
        (proj / "meta.json").write_text(json.dumps({"id": f"cena{self.n}", "name": f"cena {self.n}"}), encoding="utf-8")
        dur = float(cena["duracao"])
        (proj / "index.html").write_text(MODELOS[cena.get("modelo", "imagem")](cena, dur, proj), encoding="utf-8")
        bruto = proj / "bruto.mp4"
        env = {**os.environ, "HYPERFRAMES_NO_TELEMETRY": "1", "DO_NOT_TRACK": "1"}
        r = subprocess.run([*_hyperframes(), "render", "-o", str(bruto), "--quality", "draft", "--fps", str(FPS)],
                           cwd=proj, env=env, capture_output=True, text=True, timeout=900)
        if r.returncode != 0 or not bruto.exists():
            msg = (r.stderr or r.stdout or "")[-600:]
            if "chrome" in msg.lower() and "install" in msg.lower():
                self.falhou = True
            raise RuntimeError(f"hyperframes render falhou: {msg}")
        # mesmo padrão de vídeo do motor (para juntar as cenas sem recodificar)
        rodar(["ffmpeg", "-y", "-v", "error", "-i", str(bruto), "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
               "-pix_fmt", "yuv420p", "-r", str(FPS), "-t", f"{dur:.3f}", str(saida)])
        return saida

    def fechar(self):
        pass


if __name__ == "__main__" and len(sys.argv) > 3 and sys.argv[1] == "teste":
    c = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    from .animar import cena_de
    cena = c if c.get("modelo") else cena_de(c)
    cena["duracao"] = float(sys.argv[4]) if len(sys.argv) > 4 else 8
    a = AnimadorHF(Path(sys.argv[3]).parent)
    print(a.video(cena, Path(sys.argv[3])))
