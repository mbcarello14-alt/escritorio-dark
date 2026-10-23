"""Cortes verticais (9:16) do vídeo longo: viram Shorts agendados no YouTube e arquivos para Reels/TikTok.

O `clipador` escolhe os trechos em `cortes.json` (cena de início e de fim). Aqui o motor:
1. recorta o trecho do vídeo pronto, monta a tela vertical (fundo desfocado + vídeo no meio),
   gancho fixo no topo e legenda grande palavra a palavra;
2. agenda cada corte como Short, um por dia depois do vídeo longo, às 12h;
3. manda os arquivos no Telegram, prontos para postar no Instagram/TikTok.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .comum import FONTES, carregar_config, fonte, hex_rgb, log, quebrar_linhas, rodar

W, H = 1080, 1920
MAX_S = 59.0
FONTE_LEGENDA = FONTES / "Poppins-ExtraBold.ttf"


def _topo(cfg: dict, gancho: str, destino: Path) -> Path:
    est = cfg["estilo"]
    escuro = est.get("modo") == "quadro_branco"
    fundo = hex_rgb(est["destaque2"] if escuro else est["fundo"])
    destaque = hex_rgb(est["destaque"])
    texto = (255, 255, 255) if escuro else hex_rgb(est.get("texto", "#FFFFFF"))
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = fonte(est["fonte_titulo"], int(78 * est.get("escala_fonte", 1.0)), est.get("fonte_titulo_variacao"))
    g = gancho.upper() if est.get("caixa_alta_titulo") else gancho
    linhas = quebrar_linhas(g, f, W - 160)[:3]
    alt_l = int(f.size * 1.18)
    caixa_h = alt_l * len(linhas) + 70
    y0 = 250
    d.rounded_rectangle((50, y0, W - 50, y0 + caixa_h), radius=34, fill=fundo + (235,), outline=destaque, width=6)
    for i, l in enumerate(linhas):
        d.text((W / 2, y0 + 35 + alt_l * i + alt_l / 2), l, font=f, fill=texto, anchor="mm")
    fn = fonte(est["fonte_texto"], 40, "SemiBold")
    d.text((W / 2, H - 150), cfg["nome"], font=fn, fill=(255, 255, 255, 210), anchor="mm")
    img.save(destino)
    return destino


def _grupos(palavras: list[dict], t0: float, t1: float) -> list[tuple[float, float, str]]:
    """Junta as palavras em grupos de até 3 (quebra na pontuação), com tempo relativo ao corte."""
    ws = [w for w in palavras if w["inicio"] >= t0 - 0.05 and w["inicio"] < t1 - 0.05]
    grupos, atual = [], []
    for w in ws:
        atual.append(w)
        if len(atual) == 3 or re.search(r"[.,!?;:]$", w["palavra"]):
            grupos.append(atual)
            atual = []
    if atual:
        grupos.append(atual)
    out = []
    for i, g in enumerate(grupos):
        ini = g[0]["inicio"] - t0
        fim = (grupos[i + 1][0]["inicio"] - t0) if i + 1 < len(grupos) else min(g[-1]["fim"] - t0 + 0.4, t1 - t0)
        texto = " ".join(w["palavra"] for w in g).strip(" ,;:")
        out.append((max(0.0, ini), max(ini + 0.2, fim), texto.upper()))
    return out


def _palavras_estimadas(tempos: list[dict]) -> list[dict]:
    """Sem marcação do Whisper: espalha as palavras de cada cena pela duração dela."""
    out = []
    for c in tempos:
        ws = c["narracao"].split()
        passo = c["duracao"] / max(1, len(ws))
        out += [{"palavra": w, "inicio": c["inicio"] + i * passo, "fim": c["inicio"] + (i + 1) * passo} for i, w in enumerate(ws)]
    return out


def renderizar(cfg: dict, video: Path, corte: dict, tempos: list[dict], palavras: list[dict], tmp: Path, n: int) -> Path | None:
    pos = {(c["bloco"], c["cena"]): c for c in tempos}
    a, b = pos.get(tuple(corte["de"])), pos.get(tuple(corte["ate"]))
    if not a or not b:
        log.warning("corte %d: cenas %s–%s não existem", n, corte["de"], corte["ate"])
        return None
    t0, t1 = a["inicio"], b["inicio"] + b["duracao"]
    if t1 <= t0:
        return None
    if t1 - t0 > MAX_S:   # corta no último fim de cena que cabe; se nenhum couber, corta seco
        fins = [c["inicio"] + c["duracao"] for c in tempos if t0 < c["inicio"] + c["duracao"] <= t0 + MAX_S]
        t1 = max(fins) if fins and max(fins) - t0 > 20 else t0 + MAX_S
    dur = round(t1 - t0, 3)
    pasta = tmp / f"corte_{n}"
    pasta.mkdir(parents=True, exist_ok=True)
    topo = _topo(cfg, corte.get("gancho", ""), pasta / "topo.png")
    textos = []
    for i, (ini, fim, txt) in enumerate(_grupos(palavras or _palavras_estimadas(tempos), t0, t1)):
        arq = pasta / f"l{i:03d}.txt"
        arq.write_text(txt, encoding="utf-8")
        tam = 84
        while tam > 50 and ImageFont.truetype(str(FONTE_LEGENDA), tam).getlength(txt) > W - 90:
            tam -= 4
        textos.append(f"drawtext=fontfile='{FONTE_LEGENDA}':textfile='{arq}':fontsize={tam}:fontcolor=white:"
                      f"borderw=9:bordercolor=black@0.95:x=(w-text_w)/2:y=1390:enable='between(t,{ini:.2f},{fim:.2f})'")
    filtro = ("[0:v]split[a][b];"
              "[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:2,eq=brightness=-0.18[bg];"
              "[b]scale=1080:-2[fg];[bg][fg]overlay=0:(H-h)/2+20[v1];[v1][1:v]overlay=0:0[v2]")
    filtro += ";[v2]" + (",".join(textos) if textos else "null") + "[v]"
    saida = pasta.parent / f"corte_{n}.mp4"
    rodar(["ffmpeg", "-y", "-v", "error", "-ss", f"{t0:.3f}", "-t", f"{dur:.3f}", "-i", str(video),
           "-loop", "1", "-t", f"{dur:.3f}", "-i", str(topo), "-filter_complex", filtro,
           "-map", "[v]", "-map", "0:a", "-af", f"afade=t=out:st={max(0, dur - 0.5):.2f}:d=0.5",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p", "-r", "30",
           "-c:a", "aac", "-b:a", "160k", "-shortest", str(saida)], timeout=1800)
    log.info("corte %d pronto (%.0fs)", n, dur)
    return saida


def _horarios(base_utc: str, qtd: int) -> list[str]:
    """Um Short por dia depois do vídeo longo, ao meio-dia de Brasília (15h UTC)."""
    base = datetime.fromisoformat(base_utc.replace("Z", "+00:00"))
    minimo = datetime.now(timezone.utc) + timedelta(hours=2)
    out = []
    for k in range(qtd):
        h = (base + timedelta(days=k + 1)).replace(hour=15, minute=0, second=0, microsecond=0)
        while h < minimo:
            h += timedelta(days=1)
        out.append(h.isoformat().replace("+00:00", "Z"))
    return out


def produzir_cortes(pasta: Path, cfg: dict, video: Path, tempos: list[dict], palavras: list[dict], tmp: Path,
                    pub: dict, enviar: bool = True) -> list[dict]:
    arq = pasta / "cortes.json"
    if not arq.exists():
        log.info("sem cortes.json — nenhum Short neste vídeo")
        return []
    cortes = json.loads(arq.read_text(encoding="utf-8")).get("cortes", [])[:3]
    feitos = []
    for n, c in enumerate(cortes, 1):
        try:
            mp4 = renderizar(cfg, video, c, tempos, palavras, tmp / "cortes", n)
        except Exception as e:
            log.warning("corte %d falhou: %s", n, e)
            continue
        if mp4:
            feitos.append((c, mp4))
    if not feitos:
        return []
    saida = []
    horarios = _horarios(pub.get("publicar_em_utc") or datetime.now(timezone.utc).isoformat(), len(feitos))
    for (c, mp4), quando in zip(feitos, horarios):
        reg = {"titulo": c["titulo"], "arquivo": mp4.name, "publicar_em_utc": quando}
        if enviar and pub.get("video_id"):
            from .youtube import publicar_short
            try:
                reg["video_id"] = publicar_short(cfg, c, mp4, quando, pub["video_id"])
                reg["url"] = f"https://youtube.com/shorts/{reg['video_id']}"
            except Exception as e:
                log.warning("Short '%s' não subiu: %s", c["titulo"], e)
        if enviar:
            try:
                from . import telegram as T
                legenda = (f"📱 <b>Corte para Reels/TikTok</b> — {T.esc(cfg['nome'])}\n\n{T.esc(c.get('legenda_reels', c['titulo']))}"
                           + (f"\n\n▶️ Short no YouTube: {reg['url']}" if reg.get("url") else ""))
                T.enviar_video(mp4, legenda)
            except Exception as e:
                log.warning("não mandei o corte no Telegram: %s", e)
        saida.append(reg)
    return saida


if __name__ == "__main__":   # teste: python -m pipeline.cortes <pasta>  (usa saida/video.mp4 e saida/tempos.json)
    import sys
    p = Path(sys.argv[1])
    prod = json.loads((p / "producao.json").read_text(encoding="utf-8"))
    t = json.loads((p / "saida" / "tempos.json").read_text(encoding="utf-8"))
    print(produzir_cortes(p, carregar_config(prod["canal"]), p / "saida" / "video.mp4", t["cenas"], t["palavras"],
                          p / "saida" / "tmp", {}, enviar=False))
