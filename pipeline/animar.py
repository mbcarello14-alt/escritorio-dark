"""Cenas animadas feitas em código (mapas, contadores, linha do tempo, ilustração viva) + efeitos sonoros.

O desenho é feito por `pipeline/animacao/cena.html` (canvas 2D, quadro a quadro, no Chromium sem tela) e o
servidor `pipeline/animacao/render.mjs` fica aberto durante o vídeo inteiro, renderizando uma cena por vez.
Formato das cenas: `pipeline/animacao/FORMATO.md`.

Teste: python -m pipeline.animar teste <saida.mp4>   (renderiza uma amostra de cada modelo com efeitos)
"""
from __future__ import annotations

import atexit
import json
import math
import re
import shutil
import subprocess
import sys
import wave
from pathlib import Path

from .comum import FPS, RAIZ, log, rodar

DIR = RAIZ / "pipeline" / "animacao"
PARTICULAS = ("folhas", "poeira", "neve", "brasas", "moedas", "chuva")
MODELOS = {"mapa_animado": "mapa", "contador": "contador", "linha_tempo": "linha_tempo"}
AAC = ["-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2"]


# ---------------------------------------------------------------- servidor de render
class Animador:
    def __init__(self):
        self.proc = None
        self.falhou = False

    def _iniciar(self):
        if self.proc and self.proc.poll() is None:
            return
        if not shutil.which("node"):
            raise RuntimeError("node não instalado")
        self.proc = subprocess.Popen(["node", str(DIR / "render.mjs")], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     text=True, bufsize=1)
        primeira = self.proc.stdout.readline().strip()
        if primeira != "PRONTO":
            self.fechar()
            raise RuntimeError(f"render de animação não abriu: {primeira or 'sem resposta'}")
        atexit.register(self.fechar)

    def video(self, cena: dict, saida: Path) -> Path:
        """Renderiza só a imagem (mp4 sem som) da cena."""
        if self.falhou:
            raise RuntimeError("render de animação indisponível nesta execução")
        try:
            self._iniciar()
        except Exception:
            self.falhou = True
            raise
        self.proc.stdin.write(json.dumps({"cena": cena, "saida": str(saida.resolve()), "fps": FPS}, ensure_ascii=False) + "\n")
        self.proc.stdin.flush()
        resp = self.proc.stdout.readline().strip()
        if not resp.startswith("OK"):
            if not resp:   # o processo morreu
                self.fechar()
            raise RuntimeError(resp or "render de animação parou")
        return saida

    def fechar(self):
        if self.proc:
            try:
                self.proc.stdin.close()
                self.proc.wait(timeout=20)
            except Exception:
                self.proc.kill()
            self.proc = None


# ---------------------------------------------------------------- efeitos sonoros (sintetizados, sem licença)
def _gravar(nome: Path, amostras) -> Path:
    import numpy as np
    a = np.clip(amostras, -1, 1)
    est = (np.stack([a, a], axis=1) * 32767).astype("<i2")
    with wave.open(str(nome), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(44100)
        w.writeframes(est.tobytes())
    return nome


def _efeitos(pasta: Path) -> dict[str, Path]:
    import numpy as np
    pasta.mkdir(parents=True, exist_ok=True)
    sr = 44100
    out = {}
    rng = np.random.default_rng(3)

    def arq(nome):
        return pasta / f"{nome}.wav"

    if not arq("whoosh").exists():   # ar passando: ruído filtrado com o "brilho" subindo e descendo
        n = int(0.75 * sr)
        x = rng.standard_normal(n)
        env = np.sin(np.linspace(0, math.pi, n)) ** 2
        alfa = 0.02 + 0.22 * np.sin(np.linspace(0, math.pi, n)) ** 1.5
        y = np.zeros(n)
        for i in range(1, n):
            y[i] = y[i - 1] + alfa[i] * (x[i] - y[i - 1])
        y = y - np.convolve(y, np.ones(200) / 200, mode="same")
        _gravar(arq("whoosh"), y / (np.abs(y).max() + 1e-9) * env * 0.8)
    if not arq("pop").exists():      # marcador aparecendo
        n = int(0.14 * sr)
        t = np.arange(n) / sr
        f = 900 * np.exp(-t * 18) + 380
        y = np.sin(2 * math.pi * np.cumsum(f) / sr) * np.exp(-t * 34)
        _gravar(arq("pop"), y * 0.8)
    if not arq("moeda").exists():    # "cha-ching": dois toques metálicos
        n = int(1.1 * sr)
        t = np.arange(n) / sr
        y = np.zeros(n)
        for t0, base in ((0.0, 2637.0), (0.085, 3136.0)):
            tt = np.clip(t - t0, 0, None)
            on = (t >= t0).astype(float)
            for mult, amp, dec in ((1, 1.0, 5.5), (2.76, 0.5, 9), (5.4, 0.25, 14)):
                y += on * amp * np.sin(2 * math.pi * base * mult * tt) * np.exp(-tt * dec)
        _gravar(arq("moeda"), y / np.abs(y).max() * 0.7)
    if not arq("impacto").exists():  # batida grave do título
        n = int(0.9 * sr)
        t = np.arange(n) / sr
        f = 70 * np.exp(-t * 3) + 38
        y = np.sin(2 * math.pi * np.cumsum(f) / sr) * np.exp(-t * 5.5)
        ruido = rng.standard_normal(n) * np.exp(-t * 40) * 0.25
        ruido = np.convolve(ruido, np.ones(30) / 30, mode="same")
        _gravar(arq("impacto"), (y + ruido) * 0.9)
    for nome in ("whoosh", "pop", "moeda", "impacto"):
        out[nome] = arq(nome)
    return out


def _entrada(it: dict, i: int, base: float, passo: float) -> float:
    return it["em"] if it.get("em") is not None else min(0.8, base + i * passo)


def eventos(cena: dict, dur: float) -> list[tuple[float, str, float]]:
    """(segundo, efeito, volume em dB) — os mesmos tempos que o cena.html usa."""
    ev = []
    m = cena.get("modelo")
    if m in ("mapa", "contador", "linha_tempo"):
        ev.append((0.0, "whoosh", -15))
    if m == "mapa":
        pops = [_entrada(c, i, 0.12, 0.09) for i, c in enumerate(cena.get("cidades", []))]
        pops += [_entrada(c, i, 0.1, 0.1) for i, c in enumerate(cena.get("rotulos", []))]
        for x in sorted(pops)[:6]:
            ev.append((x * dur, "pop", -17))
        for i, r in enumerate(cena.get("rotas", [])):
            ev.append((_entrada(r, i, 0.15, 0.15) * dur, "whoosh", -21))
    elif m == "contador":
        ev.append((0.12 * dur + min(4.0, max(1.0, 0.5 * dur)), "moeda", -9))
    elif m == "linha_tempo":
        ev.append((0.2 * dur, "pop", -14))
    ti = cena.get("titulo_inferior")
    if ti and ti.get("titulo") and not ti.get("pequeno"):
        ev.append(((ti.get("em") if ti.get("em") is not None else 0.12) * dur, "impacto", -13))
    return [(t, n, v) for t, n, v in ev if t < dur - 0.2]


def mixar(audio: Path, evs: list, saida: Path, pasta_sfx: Path) -> Path:
    if not evs:
        return audio
    sons = _efeitos(pasta_sfx)
    ent, filt, rot = ["-i", str(audio)], [], []
    for k, (t, nome, db) in enumerate(evs, 1):
        ent += ["-i", str(sons[nome])]
        ms = int(t * 1000)
        filt.append(f"[{k}:a]adelay={ms}|{ms},volume={db}dB[s{k}]")
        rot.append(f"[s{k}]")
    filt.append(f"[0:a]{''.join(rot)}amix=inputs={len(evs) + 1}:normalize=0:duration=first[a]")
    rodar(["ffmpeg", "-y", "-v", "error", *ent, "-filter_complex", ";".join(filt), "-map", "[a]",
           "-ar", "44100", "-ac", "2", str(saida)])
    return saida


# ---------------------------------------------------------------- visual do producao.json → cena
def cena_de(v: dict, imagem: Path | None = None) -> dict:
    t = v["tipo"]
    if t in MODELOS:
        cena = {k: x for k, x in v.items() if k != "tipo"}
        cena["modelo"] = MODELOS[t]
        return cena
    cena = {"modelo": "imagem", "imagem": str(imagem.resolve()) if imagem else None, "movimento": v.get("movimento") or "zoom_in"}
    for k in ("particulas", "neblina", "luzes", "titulo_inferior"):
        if v.get(k):
            cena[k] = v[k]
    return cena


def tem_extras(v: dict) -> bool:
    return any(v.get(k) for k in ("particulas", "neblina", "luzes", "titulo_inferior"))


def numero_para_contador(v: dict) -> dict | None:
    """Um cartão `numero` com valor numérico puro vira contador animado."""
    s = str(v.get("valor", "")).strip()
    m = re.fullmatch(r"([^\d]*?)\s*([\d][\d.,]*)\s*(.*)", s)
    if not m:
        return None
    pre, num, suf = m.groups()
    bruto = num.replace(".", "").replace(",", ".") if ("," in num or re.search(r"\.\d{3}(\D|$)", num)) else num
    try:
        valor = float(bruto)
    except ValueError:
        return None
    if valor < 10 or (1000 <= valor <= 2100 and "." not in num and "," not in num and not pre and not suf):
        return None   # anos ("1453") e números pequenos ficam como cartão
    return {"tipo": "contador", "de": 0, "ate": valor, "prefixo": (pre + " ") if pre and not pre.endswith(" ") else pre,
            "sufixo": (" " + suf) if suf else "", "rotulo": v.get("rotulo", ""), "casas": 0 if valor.is_integer() else 1}


def clipe(anim: Animador, cena: dict, audio: Path, dur: float, saida: Path, tmp: Path) -> Path:
    cena = {**cena, "duracao": dur}
    mudo = saida.with_name(saida.stem + "_anim.mp4")
    anim.video(cena, mudo)
    som = mixar(audio, eventos(cena, dur), saida.with_name(saida.stem + "_sfx.wav"), tmp / "sfx")
    rodar(["ffmpeg", "-y", "-v", "error", "-i", str(mudo), "-i", str(som), "-map", "0:v", "-map", "1:a",
           "-c:v", "copy", *AAC, "-t", f"{dur:.3f}", str(saida)])
    mudo.unlink(missing_ok=True)
    return saida


# ---------------------------------------------------------------- validação (usada pelo validar.py)
_NOMES = None


def nomes_validos() -> tuple[set[str], dict]:
    global _NOMES
    if _NOMES is None:
        topo = json.loads((DIR / "vendor" / "countries-50m.json").read_text(encoding="utf-8"))
        en = {g["properties"]["name"].lower() for g in topo["objects"]["countries"]["geometries"]}
        pt = {k.strip().lower(): v.lower() for k, v in json.loads((DIR / "nomes-pt.json").read_text(encoding="utf-8")).items()}
        _NOMES = (en, pt)
    return _NOMES


def erros_cena(v: dict, onde: str) -> list[str]:
    erros = []
    t = v.get("tipo")
    if t == "mapa_animado":
        en, pt = nomes_validos()
        reg = v.get("regiao")
        if isinstance(reg, list) and (len(reg) != 4 or not (-180 <= reg[0] < reg[2] <= 360 and -85 <= reg[1] < reg[3] <= 85)):
            erros.append(f"{onde}: regiao deve ser [lon_min, lat_min, lon_max, lat_max]")
        for p in v.get("paises", []):
            for n in p.get("nomes") or [p.get("nome")]:
                if not n or (n.lower() not in en and pt.get(n.strip().lower()) not in en):
                    erros.append(f"{onde}: país desconhecido '{n}' (use o nome do Natural Earth em inglês ou português comum)")
        for a in v.get("areas", []):
            if len(a.get("pontos", [])) < 3:
                erros.append(f"{onde}: área precisa de 3+ pontos [lon, lat]")
        for c in v.get("cidades", []):
            if not (-180 <= c.get("lon", 999) <= 360 and -90 <= c.get("lat", 999) <= 90):
                erros.append(f"{onde}: cidade '{c.get('nome')}' sem lon/lat válidos")
        for r in v.get("rotas", []):
            if len(r.get("pontos", [])) < 2:
                erros.append(f"{onde}: rota precisa de 2+ pontos [lon, lat]")
    elif t == "contador":
        try:
            float(v["ate"])
        except (KeyError, TypeError, ValueError):
            erros.append(f"{onde}: contador precisa de 'ate' numérico")
    elif t == "linha_tempo":
        ev = v.get("eventos") or []
        if not 1 <= len(ev) <= 12:
            erros.append(f"{onde}: linha_tempo precisa de 1 a 12 eventos")
        if not 0 <= int(v.get("foco", len(ev) - 1)) < max(1, len(ev)):
            erros.append(f"{onde}: 'foco' fora da lista de eventos")
    if v.get("particulas") and v["particulas"] not in PARTICULAS:
        erros.append(f"{onde}: particulas deve ser uma de {', '.join(PARTICULAS)}")
    for item in ("paises", "areas", "cidades", "rotas", "rotulos"):
        for x in v.get(item, []):
            if x.get("em") is not None and not 0 <= x["em"] <= 1:
                erros.append(f"{onde}: 'em' é fração da cena (0 a 1)")
    return erros


if __name__ == "__main__" and len(sys.argv) > 2 and sys.argv[1] == "teste":
    exemplos = json.loads((DIR / "exemplos.json").read_text(encoding="utf-8"))
    tmp = Path(sys.argv[2]).parent / "tmp_anim"
    tmp.mkdir(parents=True, exist_ok=True)
    a = Animador()
    clipes = []
    for i, (cena, dur) in enumerate(exemplos):
        silencio = tmp / f"sil_{i}.wav"
        rodar(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", str(dur), str(silencio)])
        clipes.append(clipe(a, cena, silencio, dur, tmp / f"c_{i}.mp4", tmp))
        log.info("amostra %d pronta", i)
    a.fechar()
    from .render import concatenar
    concatenar(clipes, Path(sys.argv[2]))
    print(sys.argv[2])
