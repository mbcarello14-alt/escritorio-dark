"""Musiquinha de fundo viciante, gerada por código (sem arquivo de terceiros = sem Content ID, sem desmonetizar).

Batida simples a 118–126 bpm: bumbo, chimbal, palma, baixo e uma melodia curtinha que se repete (o "chiclete"),
sobre a progressão mais pegajosa do pop (I–V–vi–IV). A semente muda o tom, o andamento e a melodia,
então cada reel tem a sua música, mas sempre no mesmo estilo.

  python -m pipeline.musica <segundos> <saida.wav> [semente]
"""
from __future__ import annotations

import sys
import wave
from pathlib import Path

import numpy as np

SR = 44100


def _env(n: int, ataque: float, queda: float) -> np.ndarray:
    t = np.arange(n) / SR
    return np.minimum(1, t / max(ataque, 1e-4)) * np.exp(-t / max(queda, 1e-4))


def _nota(freq: float, dur: float, forma: str, vol: float, queda: float) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    if forma == "pulso":      # chiptune suavizado (soma de harmônicos ímpares, sem ficar estridente)
        onda = sum(np.sin(2 * np.pi * freq * k * t) / k for k in (1, 3, 5, 7))
    elif forma == "baixo":
        onda = np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(2 * np.pi * freq * 2 * t)
    else:                     # "sino": acorde/pluck
        onda = np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(2 * np.pi * freq * 3 * t) * np.exp(-t * 8)
    return vol * onda * _env(n, 0.004, queda)


def _bumbo(vol=0.9):
    n = int(0.28 * SR); t = np.arange(n) / SR
    f = 45 + 95 * np.exp(-t * 28)
    return vol * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 11)


def _ruido(dur, queda, vol, rng, agudo=True):
    n = int(dur * SR)
    r = rng.standard_normal(n)
    if agudo:
        r = np.diff(np.concatenate([[0], r]))   # tira o grave: vira chiado de chimbal
    return vol * r * np.exp(-np.arange(n) / SR / queda)


def gerar(dur: float, destino: Path, semente: int = 1) -> Path:
    rng = np.random.default_rng(semente)
    bpm = float(rng.choice([118, 120, 122, 124, 126]))
    batida = 60 / bpm
    total = int((dur + 0.5) * SR)
    mix = np.zeros(total + SR * 2)

    def pos(seg):
        return int(seg * SR)

    def por(sinal, seg):
        i = pos(seg)
        mix[i:i + len(sinal)] += sinal[:max(0, len(mix) - i)]

    tom = float(rng.choice([0, 2, 5, 7, -3]))           # C, D, F, G, A (em semitons a partir de dó)
    hz = lambda semi: 261.63 * 2 ** ((semi + tom) / 12)  # noqa: E731
    escala = [0, 2, 4, 5, 7, 9, 11, 12, 14, 16]
    progressao = [[0, 4, 7], [7, 11, 14], [9, 12, 16], [5, 9, 12]]   # I V vi IV
    if rng.random() < 0.4:
        progressao = progressao[2:] + progressao[:2]                # vi IV I V
    # o "chiclete": 8 colcheias por compasso, repetidas a cada 2 compassos (com variação no 4º)
    motivo = [int(rng.choice([0, 2, 4, 4, 7, 7, 9, 12])) if rng.random() > 0.18 else None for _ in range(16)]
    motivo[0] = 0
    compasso = 4 * batida
    n_comp = int(np.ceil(dur / compasso)) + 1
    for c in range(n_comp):
        t0 = c * compasso
        acorde = progressao[c % 4]
        for b in range(4):                                  # bateria
            tb = t0 + b * batida
            por(_bumbo(), tb)
            por(_ruido(0.05, 0.02, 0.12, rng), tb + batida / 2)
            if b in (1, 3):
                por(_ruido(0.18, 0.05, 0.22, rng, agudo=False), tb)
                por(_ruido(0.12, 0.03, 0.12, rng), tb)
        for k in range(8):                                  # baixo em colcheias
            por(_nota(hz(acorde[0] - 24), batida / 2 * 0.9, "baixo", 0.32, 0.18), t0 + k * batida / 2)
        for k, semi in enumerate(acorde):                   # acorde em pluck nos tempos 1 e 3
            for b in (0, 2):
                por(_nota(hz(semi), batida * 1.6, "sino", 0.07, 0.35), t0 + b * batida + k * 0.012)
        if c == 0 and dur > 6:
            continue                                        # entra a melodia depois de 1 compasso
        frase = motivo[(c % 2) * 8:(c % 2) * 8 + 8]
        if c % 4 == 3:
            frase = frase[:4] + [frase[4] + 2 if frase[4] is not None else 7, None, 12, None]
        for k, grau in enumerate(frase):
            if grau is None:
                continue
            semi = min(escala, key=lambda s: abs(s - (grau + acorde[0] % 12)))   # puxa para notas do acorde
            por(_nota(hz(semi + 12), batida / 2 * 0.85, "pulso", 0.085, 0.16), t0 + k * batida / 2)
    mix = mix[:total]
    # fade in/out, compressão leve e volume de "fundo"
    f_in, f_out = pos(0.25), pos(1.2)
    mix[:f_in] *= np.linspace(0, 1, f_in)
    mix[-f_out:] *= np.linspace(1, 0, f_out)
    mix = np.tanh(mix * 1.3)
    mix *= 0.6 / max(1e-6, np.max(np.abs(mix)))
    destino = Path(destino)
    with wave.open(str(destino), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())
    return destino


if __name__ == "__main__":
    gerar(float(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3]) if len(sys.argv) > 3 else 1)
