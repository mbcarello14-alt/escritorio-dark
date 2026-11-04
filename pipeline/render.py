"""Montagem do vídeo com FFmpeg: um clipe por cena, concatenação e trilha."""
from __future__ import annotations

import hashlib
import random
from pathlib import Path

from .comum import ALTURA, FPS, LARGURA, MUSICA, log, rodar

X264 = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(FPS)]
AAC = ["-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2"]

MOVIMENTOS = {
    "zoom_in": ("1+0.10*on/{n}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
    "zoom_out": ("1.10-0.10*on/{n}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
    "pan_esquerda": ("1.10", "(iw-iw/zoom)*(1-on/{n})", "ih/2-(ih/zoom/2)"),
    "pan_direita": ("1.10", "(iw-iw/zoom)*on/{n}", "ih/2-(ih/zoom/2)"),
}


def clipe_imagem(img: Path, audio: Path, dur: float, saida: Path, movimento: str = "zoom_in",
                 sobreposicao: Path | None = None, textura: bool = False) -> Path:
    n = max(1, round(dur * FPS))
    z, x, y = (e.format(n=n) for e in MOVIMENTOS.get(movimento, MOVIMENTOS["zoom_in"]))
    filtro = f"[0:v]zoompan=z='{z}':x='{x}':y='{y}':d={n}:s={LARGURA}x{ALTURA}:fps={FPS}" \
        + (",noise=alls=6:allf=t,vignette=angle=PI/5" if textura else "") + ",format=yuv420p[v0]"
    entradas = ["-i", str(img), "-i", str(audio)]
    saida_v = "[v0]"
    if sobreposicao:
        entradas += ["-loop", "1", "-i", str(sobreposicao)]
        filtro += ";[v0][2:v]overlay=0:0:shortest=1[v1]"
        saida_v = "[v1]"
    rodar(["ffmpeg", "-y", "-v", "error", *entradas, "-filter_complex", filtro, "-map", saida_v, "-map", "1:a",
           "-t", f"{dur:.3f}", *X264, *AAC, str(saida)])
    return saida


def clipe_estatico(img: Path, audio: Path, dur: float, saida: Path) -> Path:
    rodar(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", str(FPS), "-i", str(img), "-i", str(audio),
           "-vf", "fade=in:st=0:d=0.25", "-t", f"{dur:.3f}", "-tune", "stillimage", *X264, *AAC,
           "-map", "0:v", "-map", "1:a", str(saida)])
    return saida


def clipe_quadros(padrao: str, n_quadros: int, audio: Path, dur: float, saida: Path) -> Path:
    """Animação curta (quadros PNG) seguida do último quadro congelado até o fim do áudio."""
    resto = max(0.0, dur - n_quadros / FPS)
    rodar(["ffmpeg", "-y", "-v", "error", "-framerate", str(FPS), "-i", padrao, "-i", str(audio),
           "-vf", f"tpad=stop_mode=clone:stop_duration={resto:.3f}", "-t", f"{dur:.3f}", *X264, *AAC,
           "-map", "0:v", "-map", "1:a", str(saida)])
    return saida


def concatenar(clipes: list[Path], saida: Path) -> Path:
    lista = saida.with_suffix(".txt")
    lista.write_text("".join(f"file '{c.resolve()}'\n" for c in clipes), encoding="utf-8")
    rodar(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lista), "-c", "copy", str(saida)])
    return saida


def escolher_musica(humor: str | None, semente: str) -> Path | None:
    if not humor:
        return None
    pasta = MUSICA / humor
    faixas = sorted(p for p in pasta.glob("*") if p.suffix.lower() in {".mp3", ".wav", ".m4a", ".ogg"}) if pasta.exists() else []
    if not faixas:
        log.info("sem trilha em musica/%s — vídeo sai só com narração", humor)
        return None
    rnd = random.Random(int(hashlib.sha1(semente.encode()).hexdigest(), 16))
    return rnd.choice(faixas)


def mixar_trilha(video: Path, musica: Path | None, volume_db: float, saida: Path) -> Path:
    if not musica:
        video.replace(saida)
        return saida
    from .comum import duracao_audio
    dur = duracao_audio(video)
    # a trilha abaixa sozinha quando a narração fala (ducking) e some nos 3 s finais
    filtro = (f"[0:a]asplit=2[voz][chave];"
              f"[1:a]volume={volume_db}dB,aformat=sample_rates=44100:channel_layouts=stereo[m];"
              f"[m][chave]sidechaincompress=threshold=0.04:ratio=5:attack=20:release=500[md];"
              f"[voz][md]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,"
              f"afade=t=out:st={max(0, dur - 3):.2f}:d=3[a]")
    rodar(["ffmpeg", "-y", "-v", "error", "-i", str(video), "-stream_loop", "-1", "-i", str(musica),
           "-filter_complex", filtro, "-map", "0:v", "-map", "[a]", "-c:v", "copy", *AAC, "-shortest", str(saida)])
    return saida
