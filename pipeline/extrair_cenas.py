"""Tira de um vídeo já montado a imagem de cada cena, para reaproveitar numa nova montagem.

Uso: python -m pipeline.extrair_cenas <pasta do vídeo> <video_antigo.mp4>
Salva <pasta>/imagens-fixas/cena_NNN.jpg para as cenas de imagem/ilustração; o motor usa essas no lugar de gerar.
Os cortes de cena são achados por detecção de troca de imagem, guiada pelo tamanho do texto de cada cena.
"""
from __future__ import annotations

import json
import os
import tempfile
import re
import subprocess
import sys
from pathlib import Path

from .comum import duracao_audio, log, rodar


def _cortes_detectados(video: Path) -> list[float]:
    r = subprocess.run(["ffmpeg", "-nostdin", "-v", "info", "-i", str(video), "-vf", "select='gt(scene,0.2)',showinfo",
                        "-an", "-f", "null", "-"], capture_output=True, text=True)
    return [float(m) for m in re.findall(r"pts_time:([0-9.]+)", r.stderr)]


def extrair(pasta: Path, video: Path) -> int:
    prod = json.loads((pasta / "producao.json").read_text(encoding="utf-8"))
    cenas = [c for b in prod["blocos"] for c in b["cenas"]]
    total = duracao_audio(video)
    detectados = _cortes_detectados(video)
    motor = os.environ.get("MOTOR_ANTIGO")
    if motor:
        # a versão antiga foi narrada por uma voz sintética previsível: narra de novo só para medir cada cena,
        # com a mesma regra de duração do motor → início exato de cada cena
        from .comum import FPS, carregar_config
        from .voz import narrar
        cfg = carregar_config(prod["canal"])
        tmp = Path(tempfile.mkdtemp())
        inicios, t = [], 0.0
        for i, c in enumerate(cenas, 1):
            inicios.append(t)
            dur = round(duracao_audio(narrar(c["narracao"], cfg, tmp / f"v{i:03d}.wav", motor)) + 0.15, 3)
            t += max(1.0, round(dur * FPS) / FPS)
        bate = sum(1 for s in inicios[1:] if any(abs(d - s) < 0.15 for d in detectados))
        log.info("durações medidas: total %.1fs (vídeo antigo %.1fs); %d de %d cortes batem com a detecção",
                 t, total, bate, len(cenas) - 1)
        esperados = inicios
    else:
        palavras = [len(c["narracao"].split()) + 1.5 for c in cenas]     # +1,5 ≈ pausa de cada cena
        k = total / sum(palavras)
        esperados, t = [], 0.0
        for p in palavras:
            esperados.append(t)
            t += p * k
        inicios = [0.0]
        for e in esperados[1:]:
            perto = [d for d in detectados if abs(d - e) < 2.5 and d > inicios[-1] + 0.8]
            inicios.append(min(perto, key=lambda d: abs(d - e)) if perto else e)
    destino = pasta / "imagens-fixas"
    destino.mkdir(exist_ok=True)
    feitas = 0
    for i, (c, ini) in enumerate(zip(cenas, inicios), 1):
        if c["visual"]["tipo"] not in ("imagem", "ilustracao"):
            continue
        rodar(["ffmpeg", "-nostdin", "-y", "-v", "error", "-ss", f"{ini + 0.12:.3f}", "-i", str(video), "-frames:v", "1",
               "-q:v", "3", str(destino / f"cena_{i:03d}.jpg")])
        feitas += 1
    from PIL import Image, ImageDraw
    arqs = sorted(destino.glob("cena_*.jpg"))
    folha = Image.new("RGB", (8 * 240, ((len(arqs) + 7) // 8) * 160), "black")
    for j, a in enumerate(arqs):
        im = Image.open(a).resize((240, 135))
        ImageDraw.Draw(im).text((4, 4), a.stem[-3:], fill="yellow")
        folha.paste(im, ((j % 8) * 240, (j // 8) * 160))
    folha.save(pasta / "imagens-fixas" / "_conferencia.png")
    achados = sum(1 for e, s in zip(esperados[1:], inicios[1:]) if abs(e - s) > 1e-6)
    log.info("%d imagens extraídas (%d de %d cortes confirmados pela detecção)", feitas, achados, len(cenas) - 1)
    return feitas


if __name__ == "__main__":
    extrair(Path(sys.argv[1]), Path(sys.argv[2]))
