"""Legendas (.srt) e capítulos a partir dos tempos reais de cada cena."""
from __future__ import annotations

import re

MAX_CARACTERES = 84  # 2 linhas de ~42


def _hms(seg: float, srt=True) -> str:
    ms = int(round(seg * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}" if srt else (f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}")


def _pedacos(texto: str) -> list[str]:
    frases = re.split(r"(?<=[.!?…])\s+", texto.strip())
    out = []
    for f in frases:
        while len(f) > MAX_CARACTERES:
            corte = max(f.rfind(", ", 0, MAX_CARACTERES), f.rfind(" ", 0, MAX_CARACTERES))
            corte = corte if corte > 20 else MAX_CARACTERES
            out.append(f[:corte + 1].strip())
            f = f[corte + 1:].strip()
        if f:
            out.append(f)
    return out


def _duas_linhas(t: str) -> str:
    if len(t) <= 42:
        return t
    meio = len(t) // 2
    esq, dir_ = t.rfind(" ", 0, meio + 8), t.find(" ", meio - 8)
    corte = esq if abs(esq - meio) <= abs(dir_ - meio) or dir_ == -1 else dir_
    return t[:corte].strip() + "\n" + t[corte:].strip()


def gerar_srt(cenas: list[dict], pausa_inicio: float = 0.25) -> str:
    """`cenas`: [{inicio, duracao, narracao}]. Tempo de cada pedaço proporcional ao nº de caracteres."""
    blocos, i = [], 1
    for c in cenas:
        pedacos = _pedacos(c["narracao"])
        if not pedacos:
            continue
        util = max(0.5, c["duracao"] - pausa_inicio - 0.2)
        total = sum(len(p) for p in pedacos)
        t = c["inicio"] + pausa_inicio
        for p in pedacos:
            d = util * len(p) / total
            blocos.append(f"{i}\n{_hms(t)} --> {_hms(t + d - 0.05)}\n{_duas_linhas(p)}\n")
            i += 1
            t += d
    return "\n".join(blocos)


def capitulos(blocos: list[dict]) -> str:
    """`blocos`: [{inicio, capitulo}]. O YouTube exige ≥3 capítulos, o 1º em 0:00, cada um com ≥10 s."""
    validos = [b for b in blocos if b.get("capitulo")]
    if len(validos) < 3:
        return ""
    validos[0] = {**validos[0], "inicio": 0}
    linhas, ultimo = [], -999.0
    for b in validos:
        if b["inicio"] - ultimo < 10:
            continue
        linhas.append(f"{_hms(b['inicio'], srt=False)} {b['capitulo']}")
        ultimo = b["inicio"]
    return "\n".join(linhas) if len(linhas) >= 3 else ""
