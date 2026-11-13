"""Monta o vídeo explicativo do escritório com o HyperFrames.

python extras/explicativo/montar.py <pasta_projeto>
Narra cada cena (Gemini, voz do roteiro.json; sem chave → silêncio do tamanho estimado), mede, junta o áudio,
gera uma trilha ambiente suave e escreve o index.html do projeto HyperFrames a partir do modelo.html.
"""
from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
import sys
import wave
from pathlib import Path

AQUI = Path(__file__).parent
RAIZ = AQUI.parent.parent
sys.path.insert(0, str(RAIZ))
PAUSA = 0.6
SR = 44100


def dur(arq: Path) -> float:
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(arq)]))


def narrar(rot: dict, pasta: Path) -> dict[str, Path]:
    from pipeline.comum import carregar_config
    voz = pasta / "voz"
    voz.mkdir(parents=True, exist_ok=True)
    cfg = carregar_config("historia")
    out = {}
    for c in rot["cenas"]:
        wav = voz / f"{c['id']}.wav"
        if not wav.exists():
            if os.environ.get("GEMINI_API_KEY"):
                from pipeline import gemini_voz, narracao
                gemini_voz.sintetizar(c["texto"], rot["voz"], rot["tom"], wav)
                try:
                    narracao.limpar(wav, c["texto"], cfg)
                except Exception as e:
                    print("aviso: não conferi a instrução lida:", e)
            else:   # teste local: silêncio do tamanho da fala
                s = len(c["texto"].split()) / 2.5
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"anullsrc=r={SR}:cl=stereo", "-t", f"{s:.2f}", str(wav)], check=True)
        out[c["id"]] = wav
    return out


def trilha(total: float, destino: Path) -> None:
    """Cama ambiente: acordes lentos com fade, bem baixinha."""
    import numpy as np
    n = int(total * SR)
    t = np.arange(n) / SR
    acordes = [[220.0, 277.18, 329.63], [196.0, 246.94, 293.66], [174.61, 220.0, 261.63], [196.0, 246.94, 329.63]]
    y = np.zeros(n)
    passo = 6.0
    for k in range(int(total / passo) + 1):
        a = acordes[k % 4]
        ini = int(k * passo * SR)
        fim = min(n, int((k + 1) * passo * SR + 2 * SR))
        if ini >= n:
            break
        tt = t[ini:fim] - k * passo
        env = np.clip(tt / 1.5, 0, 1) * np.clip((passo + 2 - tt) / 2.0, 0, 1)
        for f in a:
            y[ini:fim] += env * (np.sin(2 * math.pi * f * tt) + 0.3 * np.sin(2 * math.pi * f * 2 * tt)) / 3
    y += 0.25 * np.sin(2 * math.pi * 55 * t) * (0.5 + 0.5 * np.sin(2 * math.pi * t / 8))
    y *= np.clip(t / 2, 0, 1) * np.clip((total - t) / 3, 0, 1)
    y = y / (np.abs(y).max() + 1e-9) * 0.07
    est = (np.stack([y, y], axis=1) * 32767).astype("<i2")
    with wave.open(str(destino), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(est.tobytes())


def html(rot: dict, cenas: dict, total: float) -> str:
    s = (AQUI / "modelo.html").read_text(encoding="utf-8")
    marca = "".join(f"<span>{'&nbsp;' if ch == ' ' else ch}</span>" for ch in "ESCRITÓRIO DARK")
    cargos = [("P", "Pesquisador", "#E9B44C"), ("R", "Roteirista", "#F59E0B"), ("C", "Checador", "#2FB57A"),
              ("D", "Diretor visual", "#3B82F6"), ("S", "SEO", "#8B5CF6"), ("T", "Thumbnail", "#EC4899"),
              ("Cl", "Clipador", "#F97316"), ("G", "Gestor de tráfego", "#06B6D4"), ("A", "Analista", "#A3E635")]
    html_cargos = ""
    for i, (ini, nome, cor) in enumerate(cargos):
        x, y = 170 + (i % 3) * 540, 260 + (i // 3) * 210
        html_cargos += (f'<div class="card cargo" style="left:{x}px; top:{y}px"><div class="bola" style="background:{cor}">{ini}</div>'
                        f'<div class="nome">{nome}</div></div>')
    linhas, risco_top = "", 0
    for i in range(14):
        top = 90 + i * 52
        larg = [470, 430, 490, 380, 460, 420, 470, 300, 450, 480, 400, 460, 350, 440][i]
        linhas += f'<div class="lin" style="top:{top}px; width:{larg}px"></div>'
        if i in (1, 4, 6, 9, 12):
            linhas += f'<div class="ok" style="top:{top - 13}px">✓</div>'
        if i == 10:
            risco_top = top + 6
    estacoes = [("V", "Voz", "#E9B44C"), ("I", "Imagens", "#EC4899"), ("A", "Animação", "#3B82F6"),
                ("M", "Montagem", "#2FB57A"), ("L", "Legendas", "#8B5CF6"), ("T", "Thumbnail", "#F97316")]
    html_est = ""
    for i, (ic, n, cor) in enumerate(estacoes):
        x = 160 + i * 1600 / 6 + (1600 / 6 - 260) / 2
        html_est += (f'<div class="card est" data-cor="{cor}" style="left:{x:.0f}px"><div class="ic">{ic}</div>'
                     f'<div class="n">{n}</div></div>')
    cores_cubo = [("#C9A24A", "#9C7A2C"), ("#3B82F6", "#1E3A8A"), ("#B23A4A", "#7A1F2B")]
    cubos = ""
    for i, (c1, c2) in enumerate(cores_cubo):
        faces = "".join(f'<div class="face" style="background:{c1 if k % 2 == 0 else c2}; transform:{tr} translateZ(80px)"></div>'
                        for k, tr in enumerate(["rotateY(0deg)", "rotateY(90deg)", "rotateY(180deg)", "rotateY(-90deg)", "rotateX(90deg)", "rotateX(-90deg)"]))
        cubos += f'<div class="palco3d" style="left:{1060 + i * 260}px"><div class="cubo">{faces}</div></div>'
    nos = ""
    for i in range(8):
        a = i / 8 * 2 * math.pi
        nos += f'<div class="no" style="left:{450 + 380 * math.cos(a) - 28:.0f}px; top:{450 + 230 * math.sin(a) - 28:.0f}px"></div>'
    s = (s.replace("{{MARCA}}", marca).replace("{{CARGOS}}", html_cargos).replace("{{LINHAS}}", linhas)
          .replace("{{RISCO_TOP}}", str(risco_top)).replace("{{ESTACOES}}", html_est).replace("{{CUBOS}}", cubos)
          .replace("{{NOS}}", nos).replace("{{TOTAL}}", f"{total:.3f}").replace("{{CENAS}}", json.dumps(cenas)))
    for cid, c in cenas.items():
        s = s.replace(f"{{{{INI_{cid}}}}}", f"{c['ini']:.3f}").replace(f"{{{{DUR_{cid}}}}}", f"{c['dur']:.3f}")
    return s


def main(proj: Path) -> None:
    rot = json.loads((AQUI / "roteiro.json").read_text(encoding="utf-8"))
    (proj / "assets" / "fonts").mkdir(parents=True, exist_ok=True)
    for f in ("Oswald-Bold.ttf", "Oswald-Medium.ttf", "Inter.ttf"):
        shutil.copy(RAIZ / "assets" / "fonts" / f, proj / "assets" / "fonts" / f)
    wavs = narrar(rot, proj)
    cenas, t, partes = {}, 0.0, []
    sil = proj / "voz" / "pausa.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"anullsrc=r={SR}:cl=stereo", "-t", str(PAUSA), str(sil)], check=True)
    for c in rot["cenas"]:
        d = dur(wavs[c["id"]])
        cenas[c["id"]] = {"ini": round(t, 3), "dur": round(d + PAUSA, 3)}
        t += d + PAUSA
        partes += [wavs[c["id"]], sil]
    lista = proj / "voz" / "lista.txt"
    lista.write_text("".join(f"file '{p.resolve()}'\n" for p in partes), encoding="utf-8")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lista),
                    "-ar", str(SR), "-ac", "2", str(proj / "assets" / "voz.wav")], check=True)
    total = round(t + 0.4, 3)
    trilha(total, proj / "assets" / "trilha.wav")
    (proj / "index.html").write_text(html(rot, cenas, total), encoding="utf-8")
    print(f"total {total:.1f}s", json.dumps(cenas))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
