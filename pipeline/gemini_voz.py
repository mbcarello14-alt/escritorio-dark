"""Narrador Gemini TTS (Google AI Studio): voz natural, com interpretação e tom por canal.

Precisa do segredo GEMINI_API_KEY (aistudio.google.com/apikey — não pede cartão).
Narra um BLOCO inteiro por chamada (poucas chamadas = cabe no plano gratuito) e salva em
<pasta>/audio/bloco_NN.wav. Depois o motor trata como narração gravada (sincroniza com Whisper).
"""
from __future__ import annotations

import base64
import os
import time
from functools import lru_cache
from pathlib import Path

import requests

from .comum import log, rodar

API = "https://generativelanguage.googleapis.com/v1beta"
PREFERIDOS = ["gemini-3.8-flash-tts", "gemini-3.1-flash-tts-preview", "gemini-2.5-flash-preview-tts",
              "gemini-3.8-flash-lite-tts", "gemini-2.5-pro-preview-tts"]

TOM_PADRAO = ("Narre em português do Brasil, com sotaque brasileiro neutro, como um youtuber jovem e "
              "carismático explicando história com bom humor: ritmo dinâmico, ironia leve nas piadas, "
              "pausas curtas antes das revelações e seriedade quando o assunto for triste.")


def _chave() -> str:
    k = os.environ.get("GEMINI_API_KEY", "").strip()
    if not k:
        raise RuntimeError("segredo GEMINI_API_KEY não configurado")
    return k


@lru_cache(maxsize=1)
def modelo() -> str:
    forcado = os.environ.get("GEMINI_TTS_MODEL")
    if forcado:
        return forcado
    r = requests.get(f"{API}/models", params={"key": _chave(), "pageSize": 200}, timeout=60)
    r.raise_for_status()
    nomes = [m["name"].split("/")[-1] for m in r.json().get("models", [])
             if "tts" in m["name"] and "generateContent" in m.get("supportedGenerationMethods", ["generateContent"])]
    for p in PREFERIDOS:
        if p in nomes:
            return p
    if nomes:
        return sorted(nomes)[-1]
    raise RuntimeError("nenhum modelo de voz (TTS) disponível para esta chave")


def sintetizar(texto: str, voz: str, tom: str, destino_wav: Path, tentativas: int = 6) -> Path:
    corpo = {
        "contents": [{"parts": [{"text": f"{tom}\n\nTexto:\n{texto}"}]}],
        "generationConfig": {"responseModalities": ["AUDIO"],
                             "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voz}}}},
    }
    espera = 20
    for t in range(tentativas):
        r = requests.post(f"{API}/models/{modelo()}:generateContent", params={"key": _chave()}, json=corpo, timeout=300)
        if r.status_code == 429 or r.status_code >= 500:
            log.warning("Gemini TTS ocupado (%s) — tentando de novo em %ss", r.status_code, espera)
            time.sleep(espera)
            espera = min(espera * 2, 180)
            continue
        if r.status_code != 200:
            raise RuntimeError(f"Gemini TTS {r.status_code}: {r.text[:300]}")
        partes = r.json()["candidates"][0]["content"]["parts"]
        dados = next(p["inlineData"] for p in partes if "inlineData" in p)
        pcm = destino_wav.with_suffix(".pcm")
        pcm.write_bytes(base64.b64decode(dados["data"]))
        taxa = 24000
        mime = dados.get("mimeType", "")
        if "rate=" in mime:
            taxa = int(mime.split("rate=")[1].split(";")[0])
        rodar(["ffmpeg", "-nostdin", "-y", "-v", "error", "-f", "s16le", "-ar", str(taxa), "-ac", "1", "-i", str(pcm),
               "-ar", "44100", str(destino_wav)])
        pcm.unlink(missing_ok=True)
        return destino_wav
    raise RuntimeError("Gemini TTS: limite de uso atingido, tente mais tarde")


def narrar_blocos(pasta: Path, prod: dict, cfg: dict) -> None:
    """Gera audio/bloco_NN.wav para cada bloco que ainda não tem áudio."""
    from .gravacao import arquivo_bloco
    voz = cfg["voz"].get("gemini_voz", "Puck")
    tom = cfg["voz"].get("gemini_tom", TOM_PADRAO)
    (pasta / "audio").mkdir(exist_ok=True)
    for n, b in enumerate(prod["blocos"], 1):
        if arquivo_bloco(pasta, n):
            continue
        texto = " ".join(c["narracao"] for c in b["cenas"])
        sintetizar(texto, voz, tom, pasta / "audio" / f"bloco_{n:02d}.wav")
        log.info("narrador Gemini (%s, %s): bloco %d/%d", modelo(), voz, n, len(prod["blocos"]))
