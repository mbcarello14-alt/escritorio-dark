"""Bonecos animados por código (SVG + GSAP) para as cenas `cena_animada` do HyperFrames.

Estilo de documentário animado: personagens vetoriais simples (cabeça redonda, rosto mínimo), com esqueleto
de verdade — pernas, braços com cotovelo, cabeça —, que piscam, respiram, mexem a boca no ritmo da narração,
gesticulam e andam. O figurino (época/papel) muda roupa, chapéu e acessórios; o cenário é a ilustração de IA
sem pessoas. Formato da cena em `pipeline/animacao/FORMATO.md` (seção `cena_animada`).
"""
from __future__ import annotations

import html as H
import json
import math

PELE = {"clara": "#F2CDAE", "media": "#D9A577", "morena": "#B07A4E", "escura": "#7A4E31"}
CABELO = {"preto": "#231A14", "castanho": "#5A3A22", "loiro": "#C9A24A", "ruivo": "#A8502A", "grisalho": "#9A958C", "branco": "#E8E4DA"}

# figurino: cores (túnica, calça, sapato, capa), saia (túnica longa), chapéu, barba, acessório e cabelo padrão
FIGURINOS = {
    "romano":        {"tunica": "#E9E0CC", "calca": "#D9A577", "sapato": "#6B4A2E", "capa": "#9E2A2B", "saia": True, "chapeu": "louros", "cabelo": "castanho"},
    "senador":       {"tunica": "#F3EEE2", "calca": "#D9A577", "sapato": "#6B4A2E", "capa": None, "faixa": "#7A2E3A", "saia": True, "chapeu": None, "cabelo": "grisalho"},
    "legionario":    {"tunica": "#A8322D", "calca": "#D9A577", "sapato": "#5A3E26", "capa": "#7E1F22", "saia": True, "chapeu": "galea", "armadura": "#B9A57F", "cabelo": "castanho"},
    "rei":           {"tunica": "#2F4A8A", "calca": "#22305A", "sapato": "#3A2A1C", "capa": "#8E1F2A", "arminho": True, "saia": True, "chapeu": "coroa", "barba": True, "cabelo": "castanho"},
    "rainha":        {"tunica": "#7A2E5E", "calca": "#7A2E5E", "sapato": "#3A2A1C", "capa": "#4E1E3E", "saia": True, "vestido": True, "chapeu": "coroa", "cabelo": "ruivo", "cabelo_longo": True},
    "nobre":         {"tunica": "#3E5E4A", "calca": "#2B2B2B", "sapato": "#2B1E14", "capa": "#5A2A3A", "saia": False, "chapeu": "boina", "cabelo": "castanho"},
    "campones":      {"tunica": "#8A6E4B", "calca": "#5E4B33", "sapato": "#3A2A1C", "capa": None, "saia": True, "chapeu": "capuz", "cabelo": "castanho"},
    "monge":         {"tunica": "#5A4632", "calca": "#5A4632", "sapato": "#3A2A1C", "capa": None, "saia": True, "vestido": True, "corda": True, "chapeu": "tonsura", "cabelo": "castanho"},
    "cavaleiro":     {"tunica": "#E9E0CC", "calca": "#8A8F96", "sapato": "#5E636A", "capa": "#2F4A8A", "saia": True, "chapeu": "elmo", "armadura": "#A9AFB7", "cruz": "#A8322D", "cabelo": "castanho"},
    "conquistador":  {"tunica": "#7A2E2E", "calca": "#3A2E22", "sapato": "#2B1E14", "capa": None, "saia": False, "chapeu": "morriao", "armadura": "#A9AFB7", "barba": True, "cabelo": "preto"},
    "inca_nobre":    {"tunica": "#C9A24A", "calca": "#D9A577", "sapato": "#8A5A2E", "capa": "#A8322D", "saia": True, "padrao": "#2F4A8A", "chapeu": "llautu", "cabelo": "preto"},
    "inca":          {"tunica": "#B5532A", "calca": "#D9A577", "sapato": "#8A5A2E", "capa": None, "saia": True, "padrao": "#E9C870", "chapeu": "faixa", "cabelo": "preto"},
    "mercador":      {"tunica": "#3E6E7A", "calca": "#5E4B33", "sapato": "#3A2A1C", "capa": "#C9A24A", "saia": True, "chapeu": "turbante", "barba": True, "cabelo": "preto"},
    "farao":         {"tunica": "#F3EEE2", "calca": "#B07A4E", "sapato": "#C9A24A", "capa": None, "saia": True, "colar": "#2F6FA8", "chapeu": "nemes", "cabelo": "preto"},
    "samurai":       {"tunica": "#2E3A5E", "calca": "#1E2438", "sapato": "#2B1E14", "capa": None, "saia": True, "armadura": "#8E2A2A", "chapeu": "coque", "cabelo": "preto"},
    "viking":        {"tunica": "#6E5A3E", "calca": "#4A3E2E", "sapato": "#3A2A1C", "capa": "#8A8F96", "saia": False, "chapeu": "elmo_viking", "barba": True, "cabelo": "loiro"},
    "pirata":        {"tunica": "#E9E0CC", "calca": "#2E3A5E", "sapato": "#2B1E14", "capa": "#7A2E2E", "saia": False, "chapeu": "tricornio", "barba": True, "cabelo": "preto"},
    "soldado_napoleao": {"tunica": "#2F4A8A", "calca": "#F3EEE2", "sapato": "#1E1812", "capa": None, "saia": False, "faixa": "#E9E0CC", "chapeu": "bicornio", "cabelo": "castanho"},
    "soldado_1900":  {"tunica": "#6E6A4A", "calca": "#5E5A3E", "sapato": "#2B1E14", "capa": None, "saia": False, "chapeu": "capacete", "cabelo": "castanho"},
    "cavalheiro_1900": {"tunica": "#2B2B30", "calca": "#2B2B30", "sapato": "#141414", "capa": None, "saia": False, "colete": "#5A2A3A", "chapeu": "cartola", "bigode": True, "cabelo": "castanho"},
    "dama_1900":     {"tunica": "#5E3A5A", "calca": "#5E3A5A", "sapato": "#2B1E14", "capa": None, "saia": True, "vestido": True, "chapeu": "chapeu_dama", "cabelo": "castanho", "cabelo_longo": True},
    "operario":      {"tunica": "#3E5E7A", "calca": "#3A3A3A", "sapato": "#2B1E14", "capa": None, "saia": False, "chapeu": "boina", "cabelo": "castanho"},
    "cientista":     {"tunica": "#F3F3F0", "calca": "#3A3A40", "sapato": "#2B1E14", "capa": None, "saia": True, "chapeu": None, "oculos": True, "cabelo": "grisalho"},
    "terno":         {"tunica": "#2E3A4E", "calca": "#2E3A4E", "sapato": "#141414", "capa": None, "saia": False, "gravata": "#8E2A2A", "chapeu": None, "cabelo": "preto"},
    "estudante":     {"tunica": "#3B82F6", "calca": "#2E3A4E", "sapato": "#F3F3F0", "capa": None, "saia": False, "chapeu": None, "cabelo": "castanho"},
    "narrador":      {"tunica": "#C9A24A", "calca": "#2E3A4E", "sapato": "#2B1E14", "capa": None, "saia": False, "chapeu": None, "cabelo": "castanho"},
}
ACOES = ("entra", "sai", "anda", "aponta", "acena", "comemora", "cruza_bracos", "pensa", "segura", "assusta", "ri",
         "nega", "concorda", "olha", "triste", "bravo", "surpreso", "feliz", "fala", "cala", "senta")
PROPS = ("espada", "lanca", "pergaminho", "pena", "saco_moedas", "bandeira", "tocha", "livro", "calice", "moeda")


def _e(t) -> str:
    return H.escape(str(t), quote=True)


# ---------------------------------------------------------------- desenho (unidade: px, origem no meio dos pés)
def _chapeu(tipo: str | None, cab: str) -> str:
    if not tipo:
        return ""
    t = {
        "coroa": '<path d="M-48 -448 L-48 -476 L-30 -458 L-14 -486 L0 -460 L14 -486 L30 -458 L48 -476 L48 -448 Z" fill="#E2B33C" stroke="#9C7A2C" stroke-width="3"/>'
                 '<circle cx="0" cy="-466" r="5" fill="#B23A4A"/><circle cx="-30" cy="-462" r="4" fill="#2F6FA8"/><circle cx="30" cy="-462" r="4" fill="#2F6FA8"/>',
        "louros": '<path d="M-58 -420 Q-62 -458 -20 -462" fill="none" stroke="#6E8E3A" stroke-width="8" stroke-dasharray="10 5" stroke-linecap="round"/>'
                  '<path d="M58 -420 Q62 -458 20 -462" fill="none" stroke="#6E8E3A" stroke-width="8" stroke-dasharray="10 5" stroke-linecap="round"/>',
        "galea": '<path d="M-64 -400 Q-66 -472 0 -472 Q66 -472 64 -400 L50 -404 Q48 -452 0 -452 Q-48 -452 -50 -404 Z" fill="#B9A57F"/>'
                 '<path d="M-40 -470 Q0 -520 40 -470" fill="none" stroke="#A8322D" stroke-width="16" stroke-linecap="round"/>',
        "elmo": '<path d="M-66 -380 Q-68 -476 0 -476 Q68 -476 66 -380 Z" fill="#A9AFB7" stroke="#6E747C" stroke-width="3"/>'
                '<rect x="-46" y="-412" width="92" height="9" rx="4" fill="#2B2B30"/><rect x="-3" y="-470" width="6" height="90" fill="#6E747C"/>',
        "morriao": '<path d="M-86 -432 Q0 -400 86 -432 Q60 -446 40 -446 Q30 -500 0 -506 Q-30 -500 -40 -446 Q-60 -446 -86 -432 Z" fill="#A9AFB7" stroke="#6E747C" stroke-width="3"/>'
                   '<path d="M-24 -500 Q0 -526 24 -500" fill="none" stroke="#6E747C" stroke-width="8"/>',
        "llautu": '<rect x="-60" y="-440" width="120" height="16" rx="6" fill="#B23A4A"/><rect x="-60" y="-436" width="120" height="5" fill="#E9C870"/>'
                  '<path d="M0 -440 Q-6 -500 14 -520 Q8 -480 6 -440 Z" fill="#E9E0CC"/><path d="M-10 -424 L-10 -400 L10 -400 L10 -424 Z" fill="#B23A4A"/>',
        "faixa": '<rect x="-60" y="-440" width="120" height="14" rx="6" fill="#E9C870"/>',
        "turbante": '<path d="M-64 -420 Q-70 -488 0 -490 Q70 -488 64 -420 Q0 -440 -64 -420 Z" fill="#E9E0CC" stroke="#C9C2B3" stroke-width="3"/>'
                    '<circle cx="0" cy="-452" r="8" fill="#B23A4A"/>',
        "nemes": '<path d="M-66 -350 L-74 -410 Q-60 -470 0 -472 Q60 -470 74 -410 L66 -350 L44 -350 L50 -420 L-50 -420 L-44 -350 Z" fill="#E2B33C"/>'
                 '<path d="M-60 -440 L60 -440 M-66 -410 L66 -410 M-70 -380 L70 -380" stroke="#2F6FA8" stroke-width="6"/>',
        "coque": f'<circle cx="0" cy="-470" r="16" fill="{cab}"/>',
        "elmo_viking": '<path d="M-64 -404 Q-66 -474 0 -476 Q66 -474 64 -404 Z" fill="#8A8F96" stroke="#5E636A" stroke-width="3"/>'
                       '<rect x="-4" y="-410" width="8" height="40" fill="#5E636A"/>',
        "tricornio": '<path d="M-82 -430 Q-40 -500 0 -470 Q40 -500 82 -430 Q0 -450 -82 -430 Z" fill="#1E1812"/><path d="M-76 -432 Q0 -452 76 -432" stroke="#C9A24A" stroke-width="4" fill="none"/>',
        "bicornio": '<path d="M-96 -430 Q0 -520 96 -430 Q0 -450 -96 -430 Z" fill="#1E1812"/><circle cx="30" cy="-462" r="9" fill="#2F4A8A"/><circle cx="30" cy="-462" r="5" fill="#B23A4A"/>',
        "capacete": '<path d="M-76 -420 Q-70 -480 0 -482 Q70 -480 76 -420 Q0 -432 -76 -420 Z" fill="#6E6A4A" stroke="#4E4A32" stroke-width="3"/>',
        "cartola": '<rect x="-46" y="-530" width="92" height="90" rx="6" fill="#1E1E22"/><rect x="-74" y="-446" width="148" height="12" rx="6" fill="#1E1E22"/>'
                   '<rect x="-46" y="-462" width="92" height="12" fill="#5A2A3A"/>',
        "chapeu_dama": '<ellipse cx="0" cy="-450" rx="92" ry="16" fill="#3A2A3A"/><path d="M-44 -452 Q-40 -500 0 -502 Q40 -500 44 -452 Z" fill="#3A2A3A"/>'
                       '<path d="M30 -480 Q70 -520 60 -470" fill="none" stroke="#E9E0CC" stroke-width="7" stroke-linecap="round"/>',
        "boina": f'<path d="M-66 -420 Q-60 -478 6 -474 Q70 -470 70 -428 Q0 -438 -66 -420 Z" fill="#3A3A40"/>',
        "capuz": '<path d="M-76 -330 Q-86 -470 0 -484 Q86 -470 76 -330 L58 -340 Q66 -444 0 -458 Q-66 -444 -58 -340 Z" fill="#6E5A3E"/>',
        "tonsura": "",
    }.get(tipo, "")
    return f'<g class="chapeu">{t}</g>'


def _boneco(i: int, p: dict) -> str:
    f = dict(FIGURINOS.get(p.get("figurino", "narrador"), FIGURINOS["narrador"]))
    pele = PELE.get(p.get("pele", "media"), PELE["media"])
    cab = CABELO.get(p.get("cabelo") or f.get("cabelo", "castanho"), CABELO["castanho"])
    tun, calca, sap, capa = f["tunica"], f["calca"], f["sapato"], f.get("capa")
    sombra = '<ellipse cx="0" cy="4" rx="96" ry="16" fill="rgba(0,0,0,.28)"/>'
    capa_svg = (f'<path d="M-74 -322 Q-110 -150 -96 -40 L96 -40 Q110 -150 74 -322 Z" fill="{capa}"/>' if capa else "")
    if f.get("arminho") and capa:
        capa_svg += '<path d="M-78 -330 Q0 -300 78 -330 L74 -306 Q0 -280 -74 -306 Z" fill="#F3EEE2"/>'
    pernas = "".join(
        f'<g class="perna" id="pe{i}{l}">'
        f'<rect x="{x - 17}" y="-160" width="34" height="150" rx="14" fill="{calca}"/>'
        f'<ellipse cx="{x + 10}" cy="-10" rx="30" ry="14" fill="{sap}"/></g>' for l, x in (("e", -26), ("d", 26)))
    saia = ""
    if f.get("saia"):
        fim = -20 if f.get("vestido") else -88
        saia = f'<path d="M-62 -176 L62 -176 L{86 if f.get("vestido") else 74} {fim} L-{86 if f.get("vestido") else 74} {fim} Z" fill="{tun}"/>'
        if f.get("padrao"):
            saia += f'<path d="M-70 {fim + 8} L70 {fim + 8}" stroke="{f["padrao"]}" stroke-width="10" stroke-dasharray="14 8"/>'
    tronco = f'<path d="M-76 -322 Q-80 -330 -60 -336 L60 -336 Q80 -330 76 -322 L62 -168 L-62 -168 Z" fill="{tun}"/>'
    if f.get("armadura"):
        tronco += f'<path d="M-62 -318 L62 -318 L54 -200 Q0 -184 -54 -200 Z" fill="{f["armadura"]}" opacity=".95"/>'
        if f.get("cruz"):
            tronco += f'<path d="M-8 -300 L8 -300 L8 -270 L36 -270 L36 -254 L8 -254 L8 -210 L-8 -210 L-8 -254 L-36 -254 L-36 -270 L-8 -270 Z" fill="{f["cruz"]}"/>'
    if f.get("faixa"):
        tronco += f'<path d="M-70 -320 L-52 -320 L70 -190 L52 -180 Z" fill="{f["faixa"]}"/>'
    if f.get("colete"):
        tronco += f'<path d="M-40 -330 L0 -260 L40 -330 L46 -180 L-46 -180 Z" fill="{f["colete"]}"/><path d="M-12 -330 L0 -300 L12 -330 Z" fill="#F3F3F0"/>'
    if f.get("gravata"):
        tronco += f'<path d="M-14 -334 L14 -334 L0 -316 Z M-6 -318 L6 -318 L10 -240 L0 -226 L-10 -240 Z" fill="{f["gravata"]}"/>'
    if f.get("colar"):
        tronco += f'<path d="M-56 -334 Q0 -270 56 -334" fill="none" stroke="{f["colar"]}" stroke-width="16"/>'
    if f.get("corda"):
        tronco += '<rect x="-62" y="-196" width="124" height="8" rx="4" fill="#C9B88E"/>'
    tronco += f'<rect x="-62" y="-184" width="124" height="14" rx="6" fill="rgba(0,0,0,.18)"/>'

    def braco(lado: str, sx: int) -> str:
        return (f'<g class="ombro" id="om{i}{lado}">'
                f'<rect x="{sx - 16}" y="-330" width="32" height="104" rx="15" fill="{tun}"/>'
                f'<g class="cotovelo" id="co{i}{lado}">'
                f'<rect x="{sx - 14}" y="-240" width="28" height="94" rx="13" fill="{tun}"/>'
                f'<circle cx="{sx}" cy="-146" r="17" fill="{pele}"/>'
                + (f'<g id="prop{i}">{_prop(p.get("prop"), sx)}</g>' if lado == "d" and p.get("prop") else "")
                + "</g></g>")

    cabelo = ""
    if p.get("figurino") != "monge" and f.get("chapeu") not in ("nemes", "capuz", "elmo", "turbante"):
        cabelo = f'<path d="M-62 -398 Q-66 -470 0 -472 Q66 -470 62 -398 Q48 -440 0 -440 Q-48 -440 -62 -398 Z" fill="{cab}"/>'
        if f.get("cabelo_longo"):
            cabelo = f'<path d="M-64 -330 Q-76 -472 0 -474 Q76 -472 64 -330 L48 -340 Q56 -436 0 -440 Q-56 -436 -48 -340 Z" fill="{cab}"/>'
    if f.get("chapeu") == "tonsura":
        cabelo = f'<path d="M-62 -398 Q-64 -440 -40 -456 L-30 -440 Q-52 -428 -50 -398 Z M62 -398 Q64 -440 40 -456 L30 -440 Q52 -428 50 -398 Z" fill="{cab}"/>'
    barba = (f'<path d="M-50 -392 Q-48 -330 0 -322 Q48 -330 50 -392 Q30 -362 0 -360 Q-30 -362 -50 -392 Z" fill="{cab}"/>'
             if p.get("barba", f.get("barba")) else "")
    bigode = f'<path d="M-24 -378 Q0 -390 24 -378 Q12 -372 0 -376 Q-12 -372 -24 -378 Z" fill="{cab}"/>' if f.get("bigode") or p.get("bigode") else ""
    oculos = ('<circle cx="-22" cy="-402" r="13" fill="none" stroke="#2B2B30" stroke-width="4"/>'
              '<circle cx="22" cy="-402" r="13" fill="none" stroke="#2B2B30" stroke-width="4"/><path d="M-9 -402 L9 -402" stroke="#2B2B30" stroke-width="4"/>'
              if f.get("oculos") else "")
    cabeca = (f'<g class="cabeca" id="ca{i}">'
              f'<rect x="-14" y="-350" width="28" height="22" fill="{pele}"/>'
              f'<circle cx="0" cy="-400" r="64" fill="{pele}"/>'
              f'{cabelo}'
              f'<g id="ol{i}"><ellipse class="olho" cx="-22" cy="-402" rx="6.5" ry="8" fill="#1E1812"/><ellipse class="olho" cx="22" cy="-402" rx="6.5" ry="8" fill="#1E1812"/></g>'
              f'<path id="sbe{i}" d="M-34 -422 L-12 -424" stroke="{cab}" stroke-width="6" stroke-linecap="round"/>'
              f'<path id="sbd{i}" d="M12 -424 L34 -422" stroke="{cab}" stroke-width="6" stroke-linecap="round"/>'
              f'<path d="M-4 -394 Q2 -384 -4 -378" fill="none" stroke="rgba(90,50,30,.45)" stroke-width="4" stroke-linecap="round"/>'
              f'{barba}{bigode}'
              f'<path id="sor{i}" d="M-16 -366 Q0 -356 16 -366" fill="none" stroke="#5A2A1E" stroke-width="5" stroke-linecap="round"/>'
              f'<ellipse id="bo{i}" cx="0" cy="-362" rx="13" ry="10" fill="#5A2A1E"/>'
              f'{oculos}{_chapeu(f.get("chapeu"), cab)}</g>')
    corpo = (f'{sombra}<g class="corpo" id="cp{i}">{capa_svg}{pernas}{saia}'
             f'{braco("e", -74)}{tronco}{cabeca}{braco("d", 74)}</g>')
    return corpo


def _prop(nome: str | None, sx: int) -> str:
    x, y = sx, -146
    return {
        "espada": f'<g transform="translate({x},{y}) rotate(-35)"><rect x="-4" y="-150" width="8" height="140" fill="#C9CED6"/><rect x="-22" y="-12" width="44" height="8" fill="#9C7A2C"/><rect x="-4" y="-4" width="8" height="26" fill="#5A3E26"/></g>',
        "lanca": f'<g transform="translate({x},{y})"><rect x="-4" y="-260" width="8" height="380" fill="#6E4A2E"/><path d="M-12 -260 L0 -300 L12 -260 Z" fill="#C9CED6"/></g>',
        "pergaminho": f'<g transform="translate({x + 6},{y - 30})"><rect x="-26" y="0" width="52" height="66" fill="#F3E7C2"/><rect x="-32" y="-6" width="64" height="12" rx="6" fill="#D9C79A"/><rect x="-32" y="60" width="64" height="12" rx="6" fill="#D9C79A"/></g>',
        "pena": f'<g transform="translate({x},{y}) rotate(-20)"><path d="M0 0 Q-8 -60 6 -96 Q14 -50 0 0 Z" fill="#F3EEE2"/></g>',
        "saco_moedas": f'<g transform="translate({x},{y + 34})"><path d="M-34 0 Q-40 50 0 52 Q40 50 34 0 Q20 -14 0 -14 Q-20 -14 -34 0 Z" fill="#9C7A4B"/><text x="0" y="34" font-size="34" text-anchor="middle" fill="#E9C870" font-family="Oswald">$</text></g>',
        "bandeira": f'<g transform="translate({x},{y})"><rect x="-3" y="-240" width="6" height="300" fill="#5A3E26"/><path d="M3 -236 L110 -210 L3 -180 Z" fill="#A8322D"/></g>',
        "tocha": f'<g transform="translate({x},{y})"><rect x="-6" y="-70" width="12" height="90" fill="#6E4A2E"/><path class="chama" d="M0 -120 Q-26 -84 -10 -70 L10 -70 Q26 -84 0 -120 Z" fill="#FF9A3C"/></g>',
        "livro": f'<g transform="translate({x + 4},{y - 20})"><rect x="-34" y="-10" width="68" height="50" rx="4" fill="#7A1F2B"/><rect x="-30" y="-6" width="60" height="42" fill="#F3EBDD"/></g>',
        "calice": f'<g transform="translate({x},{y - 10})"><path d="M-20 -40 L20 -40 Q18 -6 0 -2 Q-18 -6 -20 -40 Z" fill="#E2B33C"/><rect x="-3" y="-2" width="6" height="20" fill="#E2B33C"/><rect x="-14" y="16" width="28" height="6" fill="#E2B33C"/></g>',
        "moeda": f'<g transform="translate({x},{y - 26})"><circle r="18" fill="#E2B33C" stroke="#9C7A2C" stroke-width="3"/></g>',
    }.get(nome or "", "")


# ---------------------------------------------------------------- animação
POSES = {   # ângulos (graus) de ombro e cotovelo de cada braço: (ombro_e, cotovelo_e, ombro_d, cotovelo_d)
    "repouso": (8, -6, -8, 6),
    "aponta": (8, -6, -96, 0),
    "acena": (8, -6, -150, 10),
    "comemora": (150, 10, -150, -10),
    "cruza_bracos": (-40, -110, 40, 110),
    "pensa": (8, -6, -30, -145),
    "segura": (8, -6, -55, -55),
    "assusta": (60, 40, -60, -40),
    "triste": (4, -2, -4, 2),
}


def boneco_html(i: int, p: dict, dur: float) -> str:
    x = float(p.get("x", 0.5)) * 1920
    esc = float(p.get("escala", 1.0))
    vira = -1 if p.get("olha") == "esquerda" else 1
    return (f'<div class="boneco" id="bn{i}" style="left:{x:.0f}px; top:{float(p.get("chao", 0.93)) * 1080:.0f}px">'
            f'<div class="vira" id="vi{i}" style="position:absolute; left:0; top:0; width:0; height:0">'
            f'<svg width="440" height="620" viewBox="-220 -560 440 620" style="position:absolute; left:{-220 * esc:.0f}px; top:{-560 * esc:.0f}px; '
            f'width:{440 * esc:.0f}px; height:{620 * esc:.0f}px; overflow:visible">'
            f'{_boneco(i, p)}</svg></div></div>')


def _seed(i: int, k: int) -> float:
    return (math.sin(i * 12.9898 + k * 78.233) * 43758.5453) % 1


def boneco_js(i: int, p: dict, dur: float, boca: list[float] | None, fps: int) -> str:
    """Esqueleto por código: as tweens mexem num objeto de estado (B{i}) e `posar` escreve os transform do SVG
    com o pivô certo de cada junta (ombro, cotovelo, quadril, pescoço)."""
    o = POSES["repouso"]
    vira = -1 if p.get("olha") == "esquerda" else 1
    js = [f"const B{i} = {{ ome: {o[0]}, coe: {o[1]}, omd: {o[2]}, cod: {o[3]}, pee: 0, ped: 0, ca: 0, cay: 0, cps: 1, cpy: 0,"
          f" ols: 1, olsy: 1, sber: 0, sbey: 0, sbdr: 0, sbdy: 0, bo: 0, bof: 0 }};",
          f"gsap.set('#vi{i}', {{ scaleX: {vira} }});"]
    # boca no ritmo da narração
    fala_ini, fala_fim = None, None
    for a in p.get("acoes", []):
        if a.get("acao") == "fala":
            fala_ini, fala_fim = a.get("em", 0), a.get("ate", 1)
    if p.get("fala") and fala_ini is None:
        fala_ini, fala_fim = 0, 1
    if fala_ini is not None and boca:
        js.append(f"const boca{i} = {json.dumps([round(v, 2) for v in boca])}; const fala{i} = [{int(fala_ini * dur * fps)}, {int(fala_fim * dur * fps)}];")
    else:
        js.append(f"const boca{i} = null; const fala{i} = [0, 0];")
    js.append(f"""POSAR.push(() => {{
  const b = B{i}, at = (id, t) => document.getElementById(id).setAttribute('transform', t);
  at('om{i}e', `rotate(${{b.ome}} -74 -322)`); at('co{i}e', `rotate(${{b.coe}} -74 -232)`);
  at('om{i}d', `rotate(${{b.omd}} 74 -322)`); at('co{i}d', `rotate(${{b.cod}} 74 -232)`);
  at('pe{i}e', `rotate(${{b.pee}} -26 -150)`); at('pe{i}d', `rotate(${{b.ped}} 26 -150)`);
  at('cp{i}', `translate(0 ${{b.cpy}}) translate(0 -150) scale(1 ${{b.cps}}) translate(0 150)`);
  at('ca{i}', `translate(0 ${{b.cay}}) rotate(${{b.ca}} 0 -340)`);
  at('ol{i}', `translate(0 -402) scale(${{b.ols}} ${{b.ols * b.olsy}}) translate(0 402)`);
  at('sbe{i}', `translate(0 ${{b.sbey}}) rotate(${{b.sber}} -22 -423)`); at('sbd{i}', `translate(0 ${{b.sbdy}}) rotate(${{b.sbdr}} 22 -423)`);
  const f = Math.round(tl.time() * {fps});
  let v = (boca{i} && f >= fala{i}[0] && f <= fala{i}[1]) ? (boca{i}[f] || 0) : 0;
  v = Math.max(v, b.bof);
  at('bo{i}', `translate(0 -368) scale(1 ${{0.05 + v * 0.95}}) translate(0 368)`);
  document.getElementById('bo{i}').style.opacity = v > 0.08 ? 1 : 0; document.getElementById('sor{i}').style.opacity = v > 0.08 ? 0 : 1;
}});""")
    # vida de fundo: respiração, cabeça, piscadas
    n_resp = max(1, int(dur / 1.8))
    js.append(f"tl.fromTo(B{i}, {{ cps: 1 }}, {{ cps: 1.018, duration: 0.9, ease: 'sine.inOut', yoyo: true, repeat: {n_resp * 2 - 1} }}, 0);")
    n_cab = max(1, int(dur / 2.6))
    js.append(f"tl.fromTo(B{i}, {{ ca: -1.5 }}, {{ ca: 1.5, duration: 1.3, ease: 'sine.inOut', yoyo: true, repeat: {n_cab * 2 - 1} }}, 0);")
    t = 0.6 + _seed(i, 1) * 1.2
    while t < dur - 0.3:
        js.append(f"tl.to(B{i}, {{ olsy: 0.1, duration: 0.06, ease: 'power1.in', yoyo: true, repeat: 1 }}, {t:.2f});")
        t += 2.4 + _seed(i, int(t * 10)) * 2.2
    x0 = float(p.get("x", 0.5)) * 1920

    def braco(pose, t0, ease="back.out(1.4)", d=0.45):
        oe, ce, od, cd = POSES[pose]
        return f"tl.to(B{i}, {{ ome: {oe}, coe: {ce}, omd: {od}, cod: {cd}, duration: {d}, ease: '{ease}' }}, {t0:.2f});"

    for a in p.get("acoes", []):
        ac, t0 = a.get("acao"), float(a.get("em", 0.1)) * dur
        t1 = float(a.get("ate", min(1.0, a.get("em", 0.1) + 0.35))) * dur
        if ac in ("aponta", "acena", "comemora", "cruza_bracos", "pensa", "segura", "assusta", "triste"):
            js.append(braco(ac, t0))
            if ac == "acena":
                n = max(2, int((t1 - t0) / 0.3))
                js.append(f"tl.to(B{i}, {{ cod: -30, duration: 0.15, ease: 'sine.inOut', yoyo: true, repeat: {n} }}, {t0 + 0.45:.2f});")
            if ac == "comemora":
                n = max(1, int((t1 - t0) / 0.45))
                js.append(f"tl.to('#bn{i}', {{ y: -36, duration: 0.22, ease: 'power2.out', yoyo: true, repeat: {n * 2 - 1} }}, {t0:.2f});"
                          f"tl.to(B{i}, {{ bof: 0.7, duration: 0.2 }}, {t0:.2f}); tl.to(B{i}, {{ bof: 0, duration: 0.2 }}, {t1:.2f});")
            if ac == "assusta":
                js.append(f"tl.to('#bn{i}', {{ y: -46, duration: 0.18, ease: 'power3.out', yoyo: true, repeat: 1 }}, {t0:.2f});"
                          f"tl.to(B{i}, {{ sbey: -12, sbdy: -12, ols: 1.3, bof: 0.8, duration: 0.15 }}, {t0:.2f});"
                          f"tl.to(B{i}, {{ bof: 0, duration: 0.3 }}, {t0 + 0.8:.2f});")
            if ac == "triste":
                js.append(f"tl.to(B{i}, {{ sber: -18, sbdr: 18, cay: 10, duration: 0.5, ease: 'power2.out' }}, {t0:.2f});")
            if a.get("volta", ac not in ("cruza_bracos", "triste")) and t1 < dur - 0.4:
                js.append(braco("repouso", t1, "power2.inOut", 0.5))
        elif ac in ("entra", "sai", "anda"):
            if ac == "entra":
                xi = -260 if a.get("de", "esquerda") == "esquerda" else 2180
                js.append(f"gsap.set('#bn{i}', {{ x: {xi - x0:.0f} }}); tl.to('#bn{i}', {{ x: 0, duration: {max(0.8, t1 - t0):.2f}, ease: 'power1.out' }}, {t0:.2f});")
            elif ac == "sai":
                xf = 2180 if a.get("para", "direita") == "direita" else -260
                js.append(f"tl.to('#bn{i}', {{ x: {xf - x0:.0f}, duration: {max(0.8, t1 - t0):.2f}, ease: 'power1.in' }}, {t0:.2f});")
            else:
                xa = float(a.get("x", 0.5)) * 1920
                js.append(f"tl.to('#bn{i}', {{ x: {xa - x0:.0f}, duration: {max(0.8, t1 - t0):.2f}, ease: 'power1.inOut' }}, {t0:.2f});")
            passos = max(2, int((t1 - t0) / 0.3))
            fim = t0 + passos * 0.3
            js.append(f"tl.fromTo(B{i}, {{ pee: -18, ped: 18, ome: -16, omd: 16 }}, {{ pee: 18, ped: -18, ome: 22, omd: -22, duration: 0.3, ease: 'sine.inOut', yoyo: true, repeat: {passos - 1} }}, {t0:.2f});"
                      f"tl.to(B{i}, {{ pee: 0, ped: 0, ome: {o[0]}, omd: {o[2]}, duration: 0.2 }}, {fim:.2f});"
                      f"tl.fromTo(B{i}, {{ cpy: 0 }}, {{ cpy: -8, duration: 0.15, ease: 'sine.inOut', yoyo: true, repeat: {passos * 2 - 1} }}, {t0:.2f});")
        elif ac == "olha":
            js.append(f"tl.to('#vi{i}', {{ scaleX: {-1 if a.get('para') == 'esquerda' else 1}, duration: 0.18, ease: 'power2.inOut' }}, {t0:.2f});")
        elif ac == "nega":
            js.append(f"tl.to(B{i}, {{ ca: 9, duration: 0.14, ease: 'sine.inOut', yoyo: true, repeat: 5 }}, {t0:.2f});")
        elif ac == "concorda":
            js.append(f"tl.to(B{i}, {{ cay: 9, duration: 0.16, ease: 'sine.inOut', yoyo: true, repeat: 3 }}, {t0:.2f});")
        elif ac == "ri":
            js.append(f"tl.to(B{i}, {{ cpy: -10, bof: 0.7, duration: 0.12, ease: 'sine.inOut', yoyo: true, repeat: 7 }}, {t0:.2f});")
        elif ac in ("bravo", "surpreso", "feliz"):
            sb = {"bravo": (16, -16, 4), "surpreso": (-6, 6, -12), "feliz": (0, 0, -4)}[ac]
            js.append(f"tl.to(B{i}, {{ sber: {sb[0]}, sbdr: {sb[1]}, sbey: {sb[2]}, sbdy: {sb[2]}, duration: 0.25 }}, {t0:.2f});")
            if ac == "surpreso":
                js.append(f"tl.to(B{i}, {{ ols: 1.35, duration: 0.2, ease: 'back.out(3)' }}, {t0:.2f});")
    return "\n".join(js)
