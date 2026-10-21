"""Narração: transforma o texto de cada cena em áudio.

Motores:
- kokoro  : open-source (Apache 2.0), roda no próprio GitHub Actions, grátis.
- edge    : vozes neurais da Microsoft via edge-tts. Grátis, mas é um serviço
            não oficial: pode parar de funcionar e os termos de uso comercial não são claros.
- openai  : API paga da OpenAI (centavos por vídeo). Precisa do segredo OPENAI_API_KEY.
- teste   : silêncio com a duração estimada (para testar o render sem voz).
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


def _teste_tts(texto: str, cfg: dict, destino: Path) -> None:
    dur = max(2.0, len(texto) / 15.0)  # ~15 caracteres por segundo
    rodar(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
           "-t", f"{dur:.2f}", str(destino)])


MOTORES = {"kokoro": _kokoro_tts, "edge": _edge_tts, "openai": _openai_tts, "teste": _teste_tts}


def narrar(texto: str, cfg: dict, destino: Path, motor: str | None = None) -> Path:
    """Gera `destino` (.wav 44,1 kHz mono, volume normalizado)."""
    motor = motor or os.environ.get("MOTOR_VOZ") or cfg["voz"]["motor"]
    if motor not in MOTORES:
        raise SystemExit(f"Motor de voz desconhecido: {motor}")
    texto = limpar(texto)
    bruto = destino.with_suffix(".bruto" + (".mp3" if motor == "edge" else ".wav"))
    MOTORES[motor](texto, cfg, bruto)
    if motor == "teste":
        bruto.rename(destino)
    else:
        _normalizar(bruto, destino)
        bruto.unlink(missing_ok=True)
    log.info("voz [%s] %s", motor, destino.name)
    return destino
