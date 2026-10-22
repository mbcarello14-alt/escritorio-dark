"""Manda no Telegram amostras das vozes do narrador de IA, para o Miguel escolher."""
from __future__ import annotations

import asyncio
import base64
import os
import tempfile
from pathlib import Path

import requests

from . import telegram as T

TEXTO = ("Em mil novecentos e vinte e nove, o Brasil queimou café para salvar o preço do café. "
         "Parece piada, né? Mas foi a política econômica mais séria da época. Vem comigo que eu te explico.")

GOOGLE = [("Puck", "masculina, animada"), ("Charon", "masculina, grave"), ("Fenrir", "masculina, enérgica"),
          ("Orus", "masculina, firme"), ("Kore", "feminina, clara"), ("Aoede", "feminina, leve"),
          ("Leda", "feminina, jovem")]
EDGE = [("pt-BR-AntonioNeural", "masculina"), ("pt-BR-FranciscaNeural", "feminina"), ("pt-BR-ThalitaMultilingualNeural", "feminina, jovem")]


def _google(nome: str, destino: Path) -> None:
    chave = os.environ["GOOGLE_TTS_API_KEY"]
    r = requests.post(f"https://texttospeech.googleapis.com/v1/text:synthesize?key={chave}", timeout=120, json={
        "input": {"text": TEXTO}, "voice": {"languageCode": "pt-BR", "name": f"pt-BR-Chirp3-HD-{nome}"},
        "audioConfig": {"audioEncoding": "MP3"}})
    if r.status_code != 200:
        raise RuntimeError(f"{r.status_code}: {r.text[:200]}")
    destino.write_bytes(base64.b64decode(r.json()["audioContent"]))


def _edge(nome: str, destino: Path) -> None:
    import edge_tts
    asyncio.run(edge_tts.Communicate(TEXTO, nome).save(str(destino)))


GEMINI = [("Puck", "masculina, animada"), ("Charon", "masculina, grave"), ("Fenrir", "masculina, enérgica"),
          ("Orus", "masculina, firme"), ("Kore", "feminina, clara"), ("Aoede", "feminina, leve"),
          ("Leda", "feminina, jovem"), ("Zephyr", "feminina, brilhante")]


def _gemini(nome: str, destino: Path) -> None:
    from .gemini_voz import TOM_PADRAO, sintetizar
    from .comum import rodar
    wav = destino.with_suffix(".wav")
    sintetizar(TEXTO, nome, TOM_PADRAO, wav)
    rodar(["ffmpeg", "-nostdin", "-y", "-v", "error", "-i", str(wav), "-b:a", "128k", str(destino)])


def main():
    pasta = Path(tempfile.mkdtemp())
    if os.environ.get("GEMINI_API_KEY"):
        from .gemini_voz import modelo
        try:
            T.enviar(f"🎧 <b>Vozes Gemini</b> ({T.esc(modelo())}) — as mais naturais, com interpretação:")
            for nome, desc in GEMINI:
                arq = pasta / f"gemini-{nome}.mp3"
                _gemini(nome, arq)
                T.enviar_audio(arq, f"<b>{nome}</b> · {desc}", f"Gemini {nome}")
        except Exception as e:
            T.enviar(f"⚠️ Gemini: {T.esc(str(e))[:300]}")
    else:
        T.enviar("ℹ️ As vozes Gemini (as mais naturais) aparecem aqui depois que o segredo <code>GEMINI_API_KEY</code> for salvo.")
    if os.environ.get("GOOGLE_TTS_API_KEY"):
        T.enviar("🎧 <b>Vozes do Google (Chirp 3 HD)</b> — a opção principal, oficial e grátis até 1 milhão de caracteres/mês:")
        for nome, desc in GOOGLE:
            arq = pasta / f"google-{nome}.mp3"
            try:
                _google(nome, arq)
                T.enviar_audio(arq, f"<b>{nome}</b> · {desc}", f"Google {nome}")
            except Exception as e:
                T.enviar(f"⚠️ Google {nome}: {T.esc(str(e))}")
                break
    else:
        T.enviar("ℹ️ As vozes do Google aparecem aqui depois que o segredo <code>GOOGLE_TTS_API_KEY</code> for salvo.")
    T.enviar("🎧 <b>Vozes da Microsoft (Edge)</b> — reserva gratuita, não oficial:")
    for nome, desc in EDGE:
        arq = pasta / f"edge-{nome}.mp3"
        try:
            _edge(nome, arq)
            T.enviar_audio(arq, f"<b>{nome.split('-')[2].replace('MultilingualNeural', '').replace('Neural', '')}</b> · {desc}", nome)
        except Exception as e:
            T.enviar(f"⚠️ Edge {nome}: {T.esc(str(e))}")
    T.enviar("Me diga no Claude Code qual voz você quer em cada canal (ex.: \"Puck no Ouro & Império, "
             "Kore no Mapeado, Charon no Marca-Página\").")


if __name__ == "__main__":
    main()
