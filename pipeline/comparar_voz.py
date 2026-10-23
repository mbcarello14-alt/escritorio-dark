"""Manda no Telegram o mesmo trecho narrado de 3 jeitos, para o Miguel escolher a direção de voz.

A = direção atual (gemini_tom) · B = direção nova (gemini_tom_teste) · C = direção nova + marcações no texto.
Uso: python -m pipeline.comparar_voz historia [vestibular livros]
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

from . import telegram as T
from .comum import RAIZ, carregar_config, rodar
from .gemini_voz import sintetizar


def _trecho(canal: str) -> str:
    """Um trecho real (~70 palavras) do roteiro mais recente do canal."""
    roteiros = sorted((RAIZ / "canais" / canal / "videos").glob("*/roteiro.json"))
    if not roteiros:
        return "Em mil novecentos e vinte e nove, o Brasil queimou café para salvar o preço do café. Parece piada, né? Mas foi a política mais séria da época."
    blocos = json.loads(roteiros[-1].read_text(encoding="utf-8"))["blocos"]
    texto = blocos[1 if len(blocos) > 1 else 0]["texto"]
    frases = re.split(r"(?<=[.!?])\s+", texto)
    out = []
    for f in frases:
        out.append(f)
        if len(" ".join(out).split()) >= 65:
            break
    return " ".join(out)


def _marcado(texto: str) -> str:
    """Versão com marcações de interpretação: pausas antes de números e revelações, ênfase nas perguntas."""
    t = re.sub(r"(?<=[.!?]) (Mas|E aí|Só que|Surpresa|Resultado|Então|O problema|Pensa|Agora|Só|Detalhe)", r" ... \1", texto)
    t = re.sub(r": ", r": ... ", t)
    return t


def comparar(canal: str, pasta: Path) -> None:
    cfg = carregar_config(canal)
    v = cfg["voz"]
    voz, atual, nova = v["gemini_voz"], v["gemini_tom"], v.get("gemini_tom_teste") or v["gemini_tom"]
    texto = _trecho(canal)
    T.enviar(f"🎧 <b>{T.esc(cfg['nome'])} — {voz}</b>: o mesmo trecho de 3 jeitos. Me diga qual ficou mais natural (A, B ou C).")
    for rot, tom, txt, desc in (("A", atual, texto, "direção atual"), ("B", nova, texto, "direção nova"),
                                ("C", nova, _marcado(texto), "direção nova + pausas marcadas no texto")):
        wav = pasta / f"{canal}-{rot}.wav"
        sintetizar(txt, voz, tom, wav)
        mp3 = wav.with_suffix(".mp3")
        rodar(["ffmpeg", "-nostdin", "-y", "-v", "error", "-i", str(wav), "-b:a", "128k", str(mp3)])
        T.enviar_audio(mp3, f"<b>{rot}</b> · {desc}", f"{cfg['nome']} {rot}")


if __name__ == "__main__":
    p = Path(tempfile.mkdtemp())
    for c in sys.argv[1:] or ["historia"]:
        try:
            comparar(c, p)
        except Exception as e:
            T.enviar(f"⚠️ Comparação de voz ({c}): {T.esc(str(e))[:300]}")
