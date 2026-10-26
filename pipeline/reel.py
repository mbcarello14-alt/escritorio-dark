"""Reels chamativos: Shorts com cena 3D low-poly feita por código, montados a partir de um reel.json.

  python -m pipeline.reel planejar                → cria canais/<canal>/reels/<data>/ para cada canal ativo
  python -m pipeline.reel produzir <pasta>        → narração → cena 3D → legenda, sons, faixa → saida/reel.mp4 → Telegram
  python -m pipeline.reel publicar <pasta>       → agenda como Short no YouTube (depois do "aprovar")
  python -m pipeline.reel produzir <pasta> --sem-envio --voz teste   → teste local

Formato do reel.json: pipeline/reels/FORMATO.md
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .comum import FONTES, RAIZ, carregar_config, duracao_audio, log, rodar

FPS = 30
W, H = 1080, 1920
SONS = {   # efeitos sonoros gerados na hora (sem arquivo e sem direitos autorais)
    "boom": "sine=f=55:d=0.9,volume=3.5,afade=t=out:st=0.05:d=0.85[a];anoisesrc=d=0.5:c=brown:a=0.6,lowpass=f=300,afade=t=out:st=0:d=0.5[b];[a][b]amix=inputs=2",
    "pop": "sine=f=880:d=0.09,volume=1.4,afade=t=out:st=0.02:d=0.07",
    "whoosh": "anoisesrc=d=0.6:c=pink:a=0.5,bandpass=f=1200:width_type=o:w=2,afade=t=in:st=0:d=0.3,afade=t=out:st=0.3:d=0.3",
    "ding": "sine=f=1320:d=0.7,volume=0.9,afade=t=out:st=0.05:d=0.65",
    "caixa": "sine=f=1568:d=0.25,volume=0.8,afade=t=out:st=0.03:d=0.22[a];sine=f=2093:d=0.45,volume=0.7,adelay=120,afade=t=out:st=0.15:d=0.3[b];[a][b]amix=inputs=2",
    "tic": "sine=f=2400:d=0.04,volume=0.6",
}


def _pastas_reels(canal: str) -> list[Path]:
    return sorted((RAIZ / "canais" / canal / "reels").glob("*/estado.json"))


# ---------------------------------------------------------------- planejamento
def planejar() -> list[Path]:
    hoje = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-3))).date().isoformat()
    novas = []
    for canal in ("historia", "vestibular", "livros"):
        cfg = carregar_config(canal)
        if not cfg.get("ativo") or not (cfg.get("reels") or {}).get("ligado", True):
            continue
        pasta = RAIZ / "canais" / canal / "reels" / hoje
        if (pasta / "estado.json").exists():
            continue
        pasta.mkdir(parents=True, exist_ok=True)
        (pasta / "estado.json").write_text(json.dumps({"canal": canal, "dia": hoje, "etapa": "roteiro_reel",
                                                       "ajustes": []}, ensure_ascii=False, indent=2), encoding="utf-8")
        novas.append(pasta)
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write("pastas=" + " ".join(str(p.relative_to(RAIZ)) for p in novas) + "\n")
    return novas


def _estado(pasta: Path, **mudar) -> dict:
    arq = pasta / "estado.json"
    e = json.loads(arq.read_text(encoding="utf-8")) if arq.exists() else {}
    if mudar:
        e.update(mudar)
        e["atualizado_em"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        arq.write_text(json.dumps(e, ensure_ascii=False, indent=2), encoding="utf-8")
    return e


# ---------------------------------------------------------------- narração e tempos
def _narrar(pasta: Path, reel: dict, cfg: dict, tmp: Path, motor: str | None) -> tuple[Path, list[float], list[dict]]:
    """Narra todas as falas de uma vez e acha onde cada fala começa. Devolve (áudio, inícios, palavras)."""
    from . import gravacao
    textos = [f["texto"] for f in reel["falas"]]
    (pasta / "audio").mkdir(exist_ok=True)
    wav = pasta / "audio" / "bloco_01.wav"
    if motor == "teste" or os.environ.get("MOTOR_VOZ") == "teste":
        # teste sem rede: tom no lugar da voz, palavras espalhadas por proporção
        ws = " ".join(textos).split()
        dur = len(ws) / 2.6
        limpo = tmp / "bloco_01_limpo.wav"
        rodar(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"sine=f=220:d={dur:.2f}",
               "-af", "volume='0.3*(1+sin(2*PI*t*4))':eval=frame", "-ar", "44100", str(limpo)])
        passo, palavras, inicios, i = dur / len(ws), [], [], 0
        for t in textos:
            inicios.append(i * passo)
            for w in t.split():
                palavras.append({"palavra": w, "inicio": i * passo, "fim": (i + 0.9) * passo}); i += 1
        return limpo, inicios, palavras
    if not wav.exists():
        from .gemini_voz import aparar_fora_do_roteiro, sintetizar
        from .narracao import limpar
        v = cfg["voz"]
        tom = (v.get("gemini_tom", "") + " Este é um vídeo curto para redes sociais: fale com energia, ritmo rápido, "
               "sem pausas longas, como quem conta uma curiosidade incrível para um amigo.")
        try:
            sintetizar(" ".join(textos), v.get("gemini_voz", "Puck"), tom, wav)
            aparar_fora_do_roteiro(wav, " ".join(textos))
            limpar(wav, " ".join(textos), cfg)
        except Exception as e:
            log.warning("Gemini indisponível (%s) — usando a voz reserva", e)
            from .voz import escolher_motor, narrar
            m = escolher_motor(cfg, tmp, [x for x in cfg["voz"]["motor"] if x != "gemini"])
            narrar(" ".join(textos), cfg, wav, m)
    _, palavras, inicios = gravacao.preparar_bloco(pasta, 1, textos, tmp)
    limpo = tmp / "bloco_01_limpo.wav"
    return limpo, inicios[:-1], palavras


# ---------------------------------------------------------------- linha do tempo
def _timeline(reel: dict, inicios: list[float], dur_total: float) -> dict:
    acoes = []
    for f, t0 in zip(reel["falas"], inicios):
        for a in f.get("acoes", []):
            acoes.append({**a, "t": round(t0 + float(a.get("t", 0)), 3)})
    objetos = list(reel.get("objetos", []))
    if reel.get("isca"):   # "comenta X": aparece na última fala e fica até o fim
        objetos.append({"id": "_isca", "tipo": "texto", "texto": reel["isca"].upper(), "pos": [0, 0.36], "tam": 0.9,
                        "fundo": "#E63946", "cor": "#ffffff", "oculto": True})
        acoes.append({"t": round(inicios[-1], 3), "alvo": "_isca", "acao": "aparecer", "som": "pop"})
    return {"cenario": reel.get("cenario", {}), "camera": reel.get("camera", {}), "objetos": objetos,
            "acoes": sorted(acoes, key=lambda a: a["t"]), "duracao": dur_total}


def _trilha_sons(timeline: dict, dur: float, tmp: Path) -> Path | None:
    eventos = [(a["t"], a["som"]) for a in timeline["acoes"] if a.get("som") in SONS]
    if not eventos:
        return None
    arquivos = {}
    for nome in {s for _, s in eventos}:
        arq = tmp / f"som_{nome}.wav"
        rodar(["ffmpeg", "-y", "-v", "error", "-filter_complex",
               SONS[nome] + ",aformat=sample_rates=44100:channel_layouts=stereo[o]", "-map", "[o]", str(arq)])
        arquivos[nome] = arq
    entradas, filtros = [], []
    for i, (t, nome) in enumerate(eventos[:60]):
        entradas += ["-i", str(arquivos[nome])]
        ms = int(t * 1000)
        filtros.append(f"[{i}:a]adelay={ms}|{ms}[s{i}]")
    n = len(filtros)
    filtro = ";".join(filtros) + ";" + "".join(f"[s{i}]" for i in range(n)) + \
        f"amix=inputs={n}:normalize=0,apad=whole_dur={dur:.2f},atrim=0:{dur:.2f},volume=0.55[o]"
    saida = tmp / "sons.wav"
    rodar(["ffmpeg", "-y", "-v", "error", *entradas, "-filter_complex", filtro, "-map", "[o]", str(saida)])
    return saida


def _render_quadros(timeline_json: Path, pasta_q: Path, dur: float) -> None:
    script = RAIZ / "pipeline" / "reels" / "render.mjs"
    r = subprocess.run(["node", str(script), str(timeline_json), str(pasta_q), f"{dur:.2f}", str(FPS), str(W), str(H)],
                       capture_output=True, text=True, timeout=3600)
    for linha in (r.stdout + r.stderr).splitlines()[-6:]:
        log.info("render 3D: %s", linha)
    if r.returncode != 0:
        raise RuntimeError("render 3D falhou: " + r.stderr[-1500:])


def produzir(pasta: Path, enviar: bool = True, motor: str | None = None) -> Path:
    from . import cortes, engajamento
    reel = json.loads((pasta / "reel.json").read_text(encoding="utf-8"))
    cfg = carregar_config(reel.get("canal") or _estado(pasta)["canal"])
    tmp = pasta / "saida" / "tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    _estado(pasta, etapa="renderizando_reel")

    voz, inicios, palavras = _narrar(pasta, reel, cfg, tmp, motor)
    dur_voz = duracao_audio(voz)
    dur = round(dur_voz + 1.4, 2)                      # respiro final com a isca na tela
    tl = _timeline(reel, inicios, dur)
    arq_tl = tmp / "timeline.json"
    arq_tl.write_text(json.dumps(tl, ensure_ascii=False), encoding="utf-8")

    pasta_q = tmp / "quadros"
    if pasta_q.exists():
        for q in pasta_q.glob("*.jpg"):
            q.unlink()
    _render_quadros(arq_tl, pasta_q, dur)

    # legenda palavra a palavra (grupos de até 3) + faixa "Inscreva-se" no fim
    textos = []
    for i, (ini, fim, txt) in enumerate(cortes._grupos(palavras, 0.0, dur_voz + 0.3)):
        a = tmp / f"leg{i:03d}.txt"
        a.write_text(txt, encoding="utf-8")
        from PIL import ImageFont
        tam = 86
        while tam > 50 and ImageFont.truetype(str(FONTES / "Poppins-ExtraBold.ttf"), tam).getlength(txt) > W - 100:
            tam -= 4
        textos.append(f"drawtext=fontfile='{FONTES / 'Poppins-ExtraBold.ttf'}':textfile='{a}':fontsize={tam}:fontcolor=white:"
                      f"borderw=10:bordercolor=black:x=(w-text_w)/2:y=1420:enable='between(t,{ini:.2f},{fim:.2f})'")
    sons = _trilha_sons(tl, dur, tmp)
    mudo = tmp / "reel_mudo.mp4"
    rodar(["ffmpeg", "-y", "-v", "error", "-framerate", str(FPS), "-i", str(pasta_q / "q%05d.jpg"),
           "-vf", ",".join(textos) if textos else "null", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
           "-pix_fmt", "yuv420p", "-r", str(FPS), str(mudo)], timeout=1800)
    saida = pasta / "saida" / "reel.mp4"
    entradas = ["-i", str(mudo), "-i", str(voz)] + (["-i", str(sons)] if sons else [])
    mix = "[1:a]apad,atrim=0:%.2f,aformat=sample_rates=44100:channel_layouts=stereo[v]" % dur
    mix += (";[2:a]aformat=sample_rates=44100:channel_layouts=stereo[s];[v][s]amix=inputs=2:normalize=0[a]" if sons else ";[v]anull[a]")
    rodar(["ffmpeg", "-y", "-v", "error", *entradas, "-filter_complex", mix, "-map", "0:v", "-map", "[a]",
           "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-t", f"{dur:.2f}", str(saida)])
    png = tmp / "chamada.png"
    engajamento.arte(cfg, W, H, vertical=True).save(png)
    com_faixa = tmp / "reel_faixa.mp4"
    engajamento.aplicar(saida, png, max(0.0, dur - 3.2), 3.2, com_faixa)
    com_faixa.replace(saida)
    log.info("reel pronto: %s (%.1fs)", saida, dur)

    _estado(pasta, etapa="pronto_reel", titulo=reel.get("titulo", ""), duracao_s=dur)
    if enviar:
        # agenda na hora (o vídeo existe nesta máquina) e manda no Telegram; o Miguel pode cancelar ou pedir ajuste
        from . import estado as E
        from . import telegram as T
        from .agenda import BRT
        despublicar(pasta)                      # versão anterior (ajuste) sai da agenda
        pub = publicar(pasta, avisar=False)
        q = datetime.fromisoformat(pub["publicar_em_utc"].replace("Z", "+00:00")).astimezone(BRT)
        legenda = (f"🎬 <b>Reel — {T.esc(cfg['nome'])}</b>\n<b>{T.esc(reel.get('titulo', ''))}</b>\n"
                   f"📅 Agendado no YouTube Shorts: {q:%d/%m às %Hh%M}\n\n"
                   "Não precisa fazer nada. Para mudar, <b>responda</b> dizendo o quê; para tirar da agenda, responda <b>cancelar</b>.\n\n"
                   f"📱 Reels/TikTok: {T.esc(reel.get('legenda_reels', ''))}")
        mid = T.enviar_video(saida, legenda[:1000])
        E.registrar_msgs([mid], pasta, "reel")
    return saida


def despublicar(pasta: Path) -> None:
    """Tira da agenda a versão já enviada (fica privada no canal, sem data). Não apaga nada."""
    arq = pasta / "publicacao.json"
    if not arq.exists():
        return
    pub = json.loads(arq.read_text(encoding="utf-8"))
    if not pub.get("video_id"):
        return
    from .youtube import servico
    cfg = carregar_config(_estado(pasta)["canal"])
    try:
        servico(cfg["segredo_youtube"]).videos().update(part="status", body={
            "id": pub["video_id"], "status": {"privacyStatus": "private"}}).execute()
        log.info("versão anterior tirada da agenda: %s", pub["video_id"])
    except Exception as e:
        log.warning("não consegui tirar %s da agenda: %s", pub["video_id"], e)
    antigos = pub.get("anteriores", []) + [pub["video_id"]]
    arq.write_text(json.dumps({"anteriores": antigos}, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------------------------------------------------------------- validação
ACOES_OK = {"aparecer", "sumir", "mover", "pular", "girar", "olhar", "acenar", "escalar", "crescer", "contar", "texto",
            "cor", "explodir", "tremer", "camera"}
TIPOS_OK = {"boneco", "predio", "casa", "arvore", "pilha_moedas", "moeda", "saco_dinheiro", "barra", "seta", "livro", "navio",
            "lousa", "cubo", "esfera", "cilindro", "texto", "numero"}


def validar(pasta: Path) -> list[str]:
    erros = []
    try:
        r = json.loads((pasta / "reel.json").read_text(encoding="utf-8"))
    except Exception as e:
        return [f"reel.json ilegível: {e}"]
    for c in ("canal", "titulo", "falas", "objetos", "isca"):
        if not r.get(c):
            erros.append(f"falta o campo '{c}'")
    if len(r.get("titulo", "")) > 90:
        erros.append("título longo demais (máx. 90)")
    falas = r.get("falas", [])
    palavras = sum(len(f.get("texto", "").split()) for f in falas)
    if not 3 <= len(falas) <= 8:
        erros.append(f"{len(falas)} falas (use 4 a 7)")
    if not 35 <= palavras <= 95:
        erros.append(f"{palavras} palavras (use 45 a 80)")
    ids = set()
    for o in r.get("objetos", []):
        if o.get("tipo") not in TIPOS_OK:
            erros.append(f"objeto '{o.get('id')}' com tipo desconhecido '{o.get('tipo')}'")
        if o.get("id") in ids:
            erros.append(f"id repetido '{o.get('id')}'")
        ids.add(o.get("id"))
        pos = o.get("pos") or [0, 0, 0]
        if len(pos) == 3 and abs(pos[0]) > 3.6:
            erros.append(f"'{o.get('id')}' em x={pos[0]} sai da tela vertical (use −3 a 3)")
    for i, f in enumerate(falas, 1):
        for a in f.get("acoes", []):
            if a.get("acao") not in ACOES_OK:
                erros.append(f"fala {i}: ação desconhecida '{a.get('acao')}'")
            elif a.get("acao") not in ("tremer", "camera") and a.get("alvo") not in ids:
                erros.append(f"fala {i}: alvo '{a.get('alvo')}' não existe")
            if a.get("som") and a["som"] not in SONS:
                erros.append(f"fala {i}: som desconhecido '{a['som']}'")
    if r.get("isca") and r["isca"].split()[-1].lower().strip(".!") not in falas[-1].get("texto", "").lower():
        erros.append("a última fala precisa falar a isca (ex.: 'Comenta OURO')")
    return erros


# ---------------------------------------------------------------- publicação
def _proximo_slot(cfg: dict) -> str:
    from .agenda import BRT, DIAS
    slots = (cfg.get("reels") or {}).get("publicar") or ["sun 19:00"]
    ocupados = {_estado(p.parent).get("publicar_em_utc") for p in _pastas_reels(cfg["canal"])
                if _estado(p.parent).get("etapa") == "agendado"}
    agora = datetime.now(timezone.utc).astimezone(BRT)
    for dias in range(0, 30):
        d = (agora + timedelta(days=dias)).date()
        for s in slots:
            dia, hora = s.split()
            if d.weekday() != DIAS[dia[:3]]:
                continue
            h, m = map(int, hora.split(":"))
            q = datetime(d.year, d.month, d.day, h, m, tzinfo=BRT)
            iso = q.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            if q > agora + timedelta(hours=2) and iso not in ocupados:
                return iso
    return (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")


def publicar(pasta: Path, avisar: bool = True) -> dict:
    from .youtube import publicar_short
    reel = json.loads((pasta / "reel.json").read_text(encoding="utf-8"))
    cfg = carregar_config(reel["canal"])
    quando = _proximo_slot(cfg)
    corte = {"titulo": reel["titulo"], "descricao": reel.get("descricao", ""), "hashtags": reel.get("hashtags", [])}
    vid = publicar_short(cfg, corte, pasta / "saida" / "reel.mp4", quando, None)
    antes = json.loads((pasta / "publicacao.json").read_text(encoding="utf-8")).get("anteriores", []) \
        if (pasta / "publicacao.json").exists() else []
    pub = {"video_id": vid, "url": f"https://youtube.com/shorts/{vid}", "publicar_em_utc": quando, "titulo": reel["titulo"],
           "anteriores": antes}
    (pasta / "publicacao.json").write_text(json.dumps(pub, ensure_ascii=False, indent=2), encoding="utf-8")
    _estado(pasta, etapa="agendado", publicar_em_utc=quando, url=pub["url"])
    if not avisar:
        return pub
    from . import telegram as T
    from .agenda import BRT
    q = datetime.fromisoformat(quando.replace("Z", "+00:00")).astimezone(BRT)
    T.enviar(f"✅ Reel agendado — {T.esc(cfg['nome'])}\n<b>{T.esc(reel['titulo'])}</b>\n📅 {q:%d/%m às %Hh%M}\n🔗 {pub['url']}\n\n"
             f"📱 Para Reels/TikTok: {T.esc(reel.get('legenda_reels', ''))}")
    return pub


if __name__ == "__main__":
    acao = sys.argv[1]
    if acao == "planejar":
        print(" ".join(str(p) for p in planejar()))
    else:
        p = Path(sys.argv[2])
        p = p if p.is_absolute() else RAIZ / p
        if acao == "produzir":
            produzir(p, enviar="--sem-envio" not in sys.argv, motor="teste" if "teste" in sys.argv else None)
        elif acao == "publicar":
            publicar(p)
        elif acao == "cancelar":
            despublicar(p)
            _estado(p, etapa="cancelado_reel", publicar_em_utc=None)
            from . import telegram as T
            T.enviar("🗑️ Reel tirado da agenda (ficou privado no canal; nada foi apagado).")
        elif acao == "validar":
            er = validar(p)
            print("OK" if not er else "Corrija:\n- " + "\n- ".join(er))
            sys.exit(1 if er else 0)
