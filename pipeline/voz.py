"""Narração: transforma o texto de cada cena em áudio.

Motores:
- kokoro  : open-source (Apache 2.0), roda no próprio GitHub Actions, grátis.
- edge    : vozes neurais da Microsoft via edge-tts. Grátis, mas é um serviço
            não oficial: pode parar de funcionar e os termos de uso comercial não são claros.
- openai  : API paga da OpenAI (centavos por vídeo). Precisa do segredo OPENAI_API_KEY.
- google  : Google Cloud Text-to-Speech (vozes Chirp 3 HD). Grátis até 1 milhão de caracteres/mês.
            Precisa do segredo GOOGLE_TTS_API_KEY.
- teste   : silêncio com a duração estimada (para testar o render sem voz).

`motor` pode ser uma lista (ex.: [google, edge, kokoro]): se um falhar, tenta o próximo.
"""
from __future__ import annotations

import asyncio
import os
import re
from pathlib import Path

from .comum import log, rodar

_kokoro = None


def limpar(texto: str) -> str:
    texto = re.sub(r"[*_#`>\[\]]", "", texto)
    return re.sub(r"\s+", " ", texto).strip()


def _normalizar(entrada: Path, saida: Path) -> None:
    rodar(["ffmpeg", "-y", "-v", "error", "-i", str(entrada), "-ac", "1", "-ar", "44100",
           "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", str(saida)])


def _kokoro_tts(texto: str, cfg: dict, destino: Path) -> None:
    global _kokoro
    import numpy as np
    import soundfile as sf
    from kokoro import KPipeline

    if _kokoro is None:
        _kokoro = KPipeline(lang_code="p")  # português do Brasil
    partes = [audio for _, _, audio in _kokoro(texto, voice=cfg["voz"]["kokoro_voz"],
                                                 speed=float(cfg["voz"].get("velocidade", 1.0)))]
    pausa = np.zeros(int(24000 * 0.25), dtype="float32")
    sf.write(destino, np.concatenate([pausa, *partes, pausa]), 24000)


def _edge_tts(texto: str, cfg: dict, destino: Path) -> None:
    import edge_tts

    vel = int(round((float(cfg["voz"].get("velocidade", 1.0)) - 1) * 100))
    com = edge_tts.Communicate(texto, cfg["voz"]["edge_voz"], rate=f"{vel:+d}%")
    asyncio.run(com.save(str(destino)))


def _openai_tts(texto: str, cfg: dict, destino: Path) -> None:
    import requests

    chave = os.environ.get("OPENAI_API_KEY")
    if not chave:
        raise SystemExit("Motor de voz 'openai' escolhido, mas o segredo OPENAI_API_KEY não existe.")
    r = requests.post(
        "https://api.openai.com/v1/audio/speech",
        headers={"Authorization": f"Bearer {chave}"},
        json={"model": "gpt-4o-mini-tts", "voice": cfg["voz"]["openai_voz"], "input": texto,
              "response_format": "wav", "speed": float(cfg["voz"].get("velocidade", 1.0))},
        timeout=300,
    )
    r.raise_for_status()
    destino.write_bytes(r.content)


def _google_tts(texto: str, cfg: dict, destino: Path) -> None:
    import base64
    import requests

    chave = os.environ.get("GOOGLE_TTS_API_KEY")
    if not chave:
        raise RuntimeError("segredo GOOGLE_TTS_API_KEY não configurado")
    nome = cfg["voz"].get("google_voz", "pt-BR-Chirp3-HD-Puck")
    corpo = {"input": {"text": texto},
             "voice": {"languageCode": "-".join(nome.split("-")[:2]), "name": nome},
             "audioConfig": {"audioEncoding": "LINEAR16", "sampleRateHertz": 44100,
                             "speakingRate": float(cfg["voz"].get("velocidade", 1.0))}}
    r = requests.post(f"https://texttospeech.googleapis.com/v1/text:synthesize?key={chave}", json=corpo, timeout=120)
    if r.status_code == 400 and "speakingRate" in r.text:
        corpo["audioConfig"].pop("speakingRate")
        r = requests.post(f"https://texttospeech.googleapis.com/v1/text:synthesize?key={chave}", json=corpo, timeout=120)
    if r.status_code != 200:
        raise RuntimeError(f"Google TTS {r.status_code}: {r.text[:300]}")
    destino.write_bytes(base64.b64decode(r.json()["audioContent"]))


def _teste_tts(texto: str, cfg: dict, destino: Path) -> None:
    dur = max(2.0, len(texto) / 15.0)  # ~15 caracteres por segundo
    rodar(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
           "-t", f"{dur:.2f}", str(destino)])


MOTORES = {"kokoro": _kokoro_tts, "edge": _edge_tts, "openai": _openai_tts, "google": _google_tts, "teste": _teste_tts}
_falhou: set[str] = set()  # motores que já falharam neste vídeo (não insiste)


def narrar(texto: str, cfg: dict, destino: Path, motor=None) -> Path:
    """Gera `destino` (.wav 44,1 kHz mono, volume normalizado). Tenta os motores em ordem."""
    motores = motor or os.environ.get("MOTOR_VOZ") or cfg["voz"]["motor"]
    if isinstance(motores, str):
        motores = [m.strip() for m in motores.split(",")]
    texto = limpar(texto)
    erros = []
    for m in motores:
        if m not in MOTORES:
            raise SystemExit(f"Motor de voz desconhecido: {m}")
        if m in _falhou:
            continue
        bruto = destino.with_suffix(".bruto" + (".mp3" if m == "edge" else ".wav"))
        try:
            MOTORES[m](texto, cfg, bruto)
        except Exception as e:
            log.warning("voz [%s] falhou: %s", m, e)
            erros.append(f"{m}: {e}")
            _falhou.add(m)
            continue
        if m == "teste":
            bruto.rename(destino)
        else:
            _normalizar(bruto, destino)
            bruto.unlink(missing_ok=True)
        log.info("voz [%s] %s", m, destino.name)
        return destino
    raise RuntimeError("Nenhum motor de voz funcionou: " + " | ".join(erros))


def escolher_motor(cfg: dict, tmp: Path, motor=None):
    """Testa a cadeia com uma frase curta e devolve UM motor, para o vídeo inteiro ter a mesma voz."""
    motores = motor or os.environ.get("MOTOR_VOZ") or cfg["voz"]["motor"]
    if isinstance(motores, str):
        motores = [m.strip() for m in motores.split(",")]
    if motores in (["gravada"], ["teste"]):
        return motores[0]
    for m in motores:
        try:
            narrar("Teste de voz.", cfg, tmp / f"teste_{m}.wav", [m])
            log.info("narrador do vídeo: %s", m)
            return m
        except Exception as e:
            log.warning("motor %s indisponível: %s", m, e)
    raise RuntimeError("Nenhum narrador de IA disponível (confira GOOGLE_TTS_API_KEY).")
