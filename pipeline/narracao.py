"""Caça a "instrução de estilo" lida em voz alta pelo narrador de IA, em qualquer ponto do áudio.

O Gemini às vezes fala a direção de voz ("narre em português do Brasil, com sotaque…") junto com o texto.
Aqui o áudio é transcrito e cada janela de palavras é comparada com o vocabulário da instrução: palavras que
estão na instrução e NÃO estão no roteiro. Onde aparecem várias juntas, o trecho é cortado.

Uso:
  python -m pipeline.narracao verificar <arquivo.mp4|wav> <canal> [<pasta do vídeo>]   → só relata
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from .comum import carregar_config, log, rodar

MARCAS = ("narre narra narrar narrador sotaque neutro youtuber carismatico apresentadora professor leia leitora "
          "ritmo dinamico ironia leve pausas curtas revelacoes seriedade trechos tristes conversa bar locutor "
          "entonacao cantada directors notes transcript read only aloud word style tom estilo").split()


def _vocab_instrucao(cfg: dict) -> set[str]:
    from .gemini_voz import TOM_PADRAO
    from .gravacao import _norm
    v = cfg.get("voz", {})
    textos = [TOM_PADRAO, v.get("gemini_tom", ""), v.get("gemini_tom_teste", ""), " ".join(MARCAS)]
    return {t for t in (_norm(p) for x in textos for p in x.split()) if len(t) > 2}


def trechos(palavras: list[dict], roteiro: str, cfg: dict, janela: int = 6, minimo: int = 3) -> list[tuple[float, float, str]]:
    """Devolve [(inicio, fim, texto)] dos trechos que parecem a instrução sendo lida."""
    from .gravacao import _norm
    if not palavras:
        return []
    instr = _vocab_instrucao(cfg)
    do_roteiro = {_norm(p) for p in roteiro.split()}
    so_instr = [(_norm(w["palavra"]) in instr and _norm(w["palavra"]) not in do_roteiro) for w in palavras]
    toks = [_norm(w["palavra"]) for w in palavras]
    # "narre em português do Brasil" é o começo típico da instrução lida
    if not ("portugues" in do_roteiro and "sotaque" in do_roteiro):
        for k, t in enumerate(toks):
            if t == "portugues" and "brasil" in toks[k + 1:k + 4]:
                for j in range(max(0, k - 3), min(len(toks), k + 4)):
                    so_instr[j] = True
    marcado = [False] * len(palavras)
    for i in range(len(palavras)):
        if sum(so_instr[i:i + janela]) >= minimo:
            for j in range(i, min(len(palavras), i + janela)):
                marcado[j] = True
    # junta as palavras marcadas em trechos contínuos (folga de 1 palavra)
    out, i = [], 0
    while i < len(palavras):
        if not marcado[i]:
            i += 1
            continue
        j = i
        while j + 1 < len(palavras) and (marcado[j + 1] or (j + 2 < len(palavras) and marcado[j + 2])):
            j += 1
        # apara as pontas que são do roteiro
        while i < j and not so_instr[i]:
            i += 1
        while j > i and not so_instr[j]:
            j -= 1
        if j - i >= 2:
            out.append((max(0.0, palavras[i]["inicio"] - 0.15), palavras[j]["fim"] + 0.15,
                        " ".join(w["palavra"] for w in palavras[i:j + 1])))
        i = j + 1
    return out


def limpar(wav: Path, roteiro: str, cfg: dict) -> list[tuple[float, float, str]]:
    """Corta do áudio os trechos de instrução lida. Devolve o que cortou."""
    from .gravacao import transcrever
    achados = trechos(transcrever(wav), roteiro, cfg)
    if not achados:
        return []
    for ini, fim, txt in achados:
        log.warning("instrução lida em %s (%.1f–%.1fs): '%s' — cortando", wav.name, ini, fim, txt[:100])
    expr = "+".join(f"between(t,{a:.3f},{b:.3f})" for a, b, _ in achados)
    tmp = wav.with_suffix(".limpo.wav")
    rodar(["ffmpeg", "-nostdin", "-y", "-v", "error", "-i", str(wav),
           "-af", f"aselect='not({expr})',asetpts=N/SR/TB", str(tmp)])
    tmp.replace(wav)
    return achados


def verificar(arquivo: Path, canal: str, pasta: Path | None = None) -> list[tuple[float, float, str]]:
    from .gravacao import transcrever
    cfg = carregar_config(canal)
    roteiro = ""
    if pasta and (pasta / "roteiro.json").exists():
        roteiro = " ".join(b["texto"] for b in json.loads((pasta / "roteiro.json").read_text(encoding="utf-8"))["blocos"])
    achados = trechos(transcrever(arquivo), roteiro, cfg)
    if achados:
        for a, b, t in achados:
            print(f"⚠️ {arquivo.name} {int(a // 60)}:{a % 60:04.1f}–{int(b // 60)}:{b % 60:04.1f}  “{t}”")
    else:
        print(f"✅ {arquivo.name}: nenhuma instrução lida")
    return achados


if __name__ == "__main__":
    if sys.argv[1] == "verificar":
        verificar(Path(sys.argv[2]), sys.argv[3], Path(sys.argv[4]) if len(sys.argv) > 4 else None)
