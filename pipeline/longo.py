"""Vídeos longos: "História para dormir" (Ouro & Império), "Livros para dormir" (Marca-Página) e
"Revisão para ouvir" (Mapeado). Produzidos em etapas, ao longo de alguns dias, para caber nas cotas grátis.

Etapas (estado.json → etapa):
  planejando → aguardando_plano (Miguel aprova no Telegram) → escrevendo (3 blocos de ~10 min por rodada, cada um
  checado) → narrando (partes de ~2 min, até a cota do dia) → imagens (escuras, até a cota) → montando →
  aguardando_aprovacao_longo (vídeo NÃO LISTADO para assistir) → "aprovar" → agendado.

  python -m pipeline.longo criar <canal> <tema...>      → cria a pasta (o bot usa)
  python -m pipeline.longo avancar <pasta>              → faz o que der da etapa atual (narração, imagens, montagem)
  python -m pipeline.longo validar <pasta>              → confere plano/blocos (os agentes usam)
  python -m pipeline.longo agendar <pasta>              → depois do "aprovar"
  python -m pipeline.longo status                       → resumo para o /longos
"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import time
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .comum import RAIZ, carregar_config, duracao_audio, log, rodar

FPS = 12          # zoom bem lento: 12 quadros/s bastam e a montagem de 2h30 fica ~5x mais rápida
PAUSA_PARTE, PAUSA_BLOCO = 0.8, 2.5
CANAL_ALIAS = {"ouro": "historia", "historia": "historia", "história": "historia", "imperio": "historia",
               "livros": "livros", "marca": "livros", "marca-pagina": "livros", "mapeado": "vestibular",
               "vestibular": "vestibular", "enem": "vestibular"}
ETAPAS = {
    "planejando": "🗺️ planejando os capítulos",
    "aguardando_plano": "👉 esperando você aprovar o plano",
    "ajuste_plano": "🗺️ ajustando o plano",
    "escrevendo": "✍️ escrevendo e checando os blocos",
    "narrando": "🎙️ narrando em partes (cota diária)",
    "imagens": "🎨 desenhando as imagens (cota diária)",
    "montando": "🎬 montando o vídeo",
    "aguardando_aprovacao_longo": "👉 esperando você assistir e aprovar",
    "agendado": "✅ agendado no YouTube",
    "cancelado": "🗑️ cancelado",
}


# ---------------------------------------------------------------- pastas e estado
def todas() -> list[Path]:
    return sorted(p.parent for p in (RAIZ / "canais").glob("*/longos/*/estado.json"))


def ler(pasta: Path) -> dict:
    return json.loads((pasta / "estado.json").read_text(encoding="utf-8"))


def salvar(pasta: Path, **mudar) -> dict:
    e = ler(pasta) if (pasta / "estado.json").exists() else {}
    e.update(mudar)
    e["atualizado_em"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    (pasta / "estado.json").write_text(json.dumps(e, ensure_ascii=False, indent=2), encoding="utf-8")
    return e


def _slug(t: str) -> str:
    t = unicodedata.normalize("NFD", t.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")[:40] or "tema"


def criar(canal: str, tema: str) -> Path:
    canal = CANAL_ALIAS.get(canal.lower(), canal.lower())
    cfg = carregar_config(canal)
    if "longos" not in cfg:
        raise SystemExit(f"o canal {canal} não tem vídeos longos configurados")
    hoje = datetime.now(timezone(timedelta(hours=-3))).date().isoformat()
    pasta = RAIZ / "canais" / canal / "longos" / f"{hoje}-{_slug(tema)}"
    pasta.mkdir(parents=True, exist_ok=True)
    salvar(pasta, canal=canal, tema=tema, formato=cfg["longos"]["formato"], etapa="planejando", ajustes=[],
           blocos_total=cfg["longos"]["blocos"], criado_em=hoje)
    return pasta


def rel(p: Path) -> str:
    return str(p.relative_to(RAIZ))


# ---------------------------------------------------------------- blocos
def plano(pasta: Path) -> dict:
    return json.loads((pasta / "plano.json").read_text(encoding="utf-8"))


def blocos(pasta: Path) -> list[dict]:
    out = []
    for a in sorted((pasta / "blocos").glob("bloco_*.json")):
        b = json.loads(a.read_text(encoding="utf-8"))
        if b.get("checado"):
            out.append(b)
    return out


def validar(pasta: Path) -> list[str]:
    erros = []
    cfg = carregar_config(ler(pasta)["canal"])["longos"]
    try:
        p = plano(pasta)
    except Exception as e:
        return [f"plano.json ilegível: {e}"]
    for c in ("titulo_youtube", "capitulos", "thumbnail", "descricao"):
        if not p.get(c):
            erros.append(f"plano.json sem '{c}'")
    if len(p.get("capitulos", [])) != cfg["blocos"]:
        erros.append(f"o plano tem {len(p.get('capitulos', []))} capítulos; precisam ser {cfg['blocos']} (um por bloco de ~10 min)")
    if len(p.get("titulo_youtube", "")) > 100:
        erros.append("titulo_youtube passa de 100 caracteres")
    alvo = cfg["palavras_por_bloco"]
    for a in sorted((pasta / "blocos").glob("bloco_*.json")):
        try:
            b = json.loads(a.read_text(encoding="utf-8"))
        except Exception as e:
            erros.append(f"{a.name} ilegível: {e}")
            continue
        n = len(b.get("texto", "").split())
        if not 0.75 * alvo <= n <= 1.3 * alvo:
            erros.append(f"{a.name}: {n} palavras (alvo {alvo}, aceito {int(0.75 * alvo)}–{int(1.3 * alvo)})")
        if len(b.get("imagens", [])) < cfg["imagens_por_bloco"]:
            erros.append(f"{a.name}: precisa de {cfg['imagens_por_bloco']} descrições em 'imagens'")
        if re.search(r"\d", b.get("texto", "")):
            erros.append(f"{a.name}: tem algarismos no texto falado (escreva números por extenso)")
    return erros


def _partes(texto: str, alvo: int = 300) -> list[str]:
    frases = re.split(r"(?<=[.!?…])\s+", texto.strip())
    out, atual = [], []
    for f in frases:
        atual.append(f)
        if len(" ".join(atual).split()) >= alvo:
            out.append(" ".join(atual))
            atual = []
    if atual:
        if out and len(" ".join(atual).split()) < alvo * 0.35:
            out[-1] += " " + " ".join(atual)
        else:
            out.append(" ".join(atual))
    return out


# ---------------------------------------------------------------- narração (em partes, ao longo dos dias)
def _midia(pasta: Path) -> Path:
    m = pasta / "midia"
    (m / "voz").mkdir(parents=True, exist_ok=True)
    return m


def _limpar_cabeca(wav: Path, texto: str, cfg: dict) -> None:
    """Procura a instrução lida nos primeiros 40 s (onde ela costuma aparecer) e corta."""
    from .gravacao import transcrever
    from .narracao import trechos
    cab = wav.with_suffix(".cab.wav")
    rodar(["ffmpeg", "-y", "-v", "error", "-i", str(wav), "-t", "40", str(cab)])
    achados = trechos(transcrever(cab), texto, cfg)
    cab.unlink(missing_ok=True)
    if achados:
        for a, b, t in achados:
            log.warning("instrução lida em %s (%.1f–%.1fs): '%s' — cortando", wav.name, a, b, t[:80])
        expr = "+".join(f"between(t,{a:.3f},{b:.3f})" for a, b, _ in achados)
        tmp = wav.with_suffix(".l.wav")
        rodar(["ffmpeg", "-y", "-v", "error", "-i", str(wav), "-af", f"aselect='not({expr})',asetpts=N/SR/TB", str(tmp)])
        tmp.replace(wav)


def narrar(pasta: Path, cfg: dict) -> bool:
    """Narra as partes que faltam até a cota acabar. Devolve True quando tudo estiver narrado."""
    from .gemini_voz import sintetizar
    lon = cfg["longos"]
    voz = cfg["voz"].get("gemini_voz", "Charon")
    m = _midia(pasta)
    manifesto = m / "voz.json"
    feito = json.loads(manifesto.read_text()) if manifesto.exists() else {}
    tmp = Path(tempfile.mkdtemp())
    pendentes = []
    for b in blocos(pasta):
        for i, t in enumerate(_partes(b["texto"]), 1):
            chave = f"b{b['n']:02d}_p{i:02d}"
            if chave not in feito or not (m / "voz" / f"{chave}.mp3").exists():
                pendentes.append((chave, t))
    for chave, texto in pendentes:
        wav = tmp / f"{chave}.wav"
        if os.environ.get("MOTOR_VOZ") == "teste":   # teste sem rede: um tom do tamanho da fala
            rodar(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"sine=f=200:d={len(texto.split()) / 2.1:.1f}", str(wav)])
            mp3 = m / "voz" / f"{chave}.mp3"
            rodar(["ffmpeg", "-y", "-v", "error", "-i", str(wav), "-ac", "1", "-b:a", "80k", str(mp3)])
            feito[chave] = round(duracao_audio(mp3), 3)
            manifesto.write_text(json.dumps(feito, indent=1))
            continue
        try:
            sintetizar(texto, voz, lon["tom"], wav, tentativas=10)
        except Exception as e:
            log.warning("narração parou (%s) — continua na próxima rodada; faltam %d partes", e,
                        sum(1 for c, _ in pendentes if c not in feito))
            return False
        _limpar_cabeca(wav, texto, cfg)
        mp3 = m / "voz" / f"{chave}.mp3"
        rodar(["ffmpeg", "-y", "-v", "error", "-i", str(wav), "-ac", "1", "-ar", "44100", "-b:a", "80k", str(mp3)])
        feito[chave] = round(duracao_audio(mp3), 3)
        manifesto.write_text(json.dumps(feito, indent=1))
        total = len(feito) + sum(1 for c, _ in pendentes if c not in feito)
        log.info("narrada %s (%.0fs) — %d de %d", chave, feito[chave], len(feito), total)
        pendentes_restantes = [p for p in pendentes if p[0] not in feito]
        if pendentes_restantes:
            time.sleep(22)
    return True


# ---------------------------------------------------------------- imagens
def _pedidos_imagens(pasta: Path) -> list[str]:
    return [d for b in blocos(pasta) for d in b.get("imagens", [])]


def _ilustrador(pasta: Path, cfg: dict):
    from .imagens_ia import Ilustrador
    c2 = json.loads(json.dumps(cfg))
    c2.setdefault("imagens", {})["estilo_ilustracao"] = cfg["longos"]["estilo_imagem"]
    return Ilustrador(_midia(pasta), c2)


def imagens(pasta: Path, cfg: dict) -> float:
    il = _ilustrador(pasta, cfg)
    pedidos = _pedidos_imagens(pasta)
    thumb = plano(pasta).get("thumbnail", {}).get("cena")
    if os.environ.get("SEM_REDE"):   # teste: imagens lisas
        from PIL import Image
        for i, d in enumerate(pedidos + ([thumb] if thumb else [])):
            Image.new("RGB", (1024, 576), (40 + i * 20 % 200, 50, 90)).save(il._destino(d), "JPEG")
    else:
        il.pre_gerar(pedidos + ([thumb] if thumb else []))
    prontas = sum(1 for d in pedidos if il._destino(d).exists())
    log.info("imagens: %d de %d prontas", prontas, len(pedidos))
    return prontas / max(1, len(pedidos))


# ---------------------------------------------------------------- montagem
def _clipe(img: Path, dur: float, saida: Path, k: int) -> Path:
    from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps
    # escurece e põe a vinheta UMA vez na imagem (fazer isso em cada quadro deixava a montagem 5x mais lenta)
    im = ImageOps.fit(ImageOps.exif_transpose(Image.open(img)).convert("RGB"), (2112, 1188), Image.LANCZOS)
    im = ImageEnhance.Color(ImageEnhance.Brightness(im).enhance(0.9)).enhance(0.88)
    mascara = Image.new("L", im.size, 0)
    ImageDraw.Draw(mascara).ellipse((-300, -250, im.width + 300, im.height + 250), fill=255)
    mascara = mascara.filter(ImageFilter.GaussianBlur(220))
    im = Image.composite(im, Image.new("RGB", im.size, (0, 0, 0)), mascara)
    base = saida.with_suffix(".jpg")
    im.save(base, quality=92)
    n = max(1, round(dur * FPS))
    passo = 0.07 / n
    z = f"1+{passo:.8f}*on" if k % 2 == 0 else f"1.07-{passo:.8f}*on"
    filtro = f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s=1920x1080:fps={FPS},format=yuv420p"
    rodar(["ffmpeg", "-y", "-v", "error", "-i", str(base), "-vf", filtro, "-frames:v", str(n), "-c:v", "libx264",
           "-preset", "ultrafast", "-crf", "23", "-tune", "stillimage", "-r", str(FPS), str(saida)], timeout=3600)
    return saida


def _hms(t: float) -> str:
    t = int(t)
    return f"{t // 3600}:{t % 3600 // 60:02d}:{t % 60:02d}" if t >= 3600 else f"{t // 60}:{t % 60:02d}"


def montar(pasta: Path, cfg: dict) -> Path:
    from . import cartoes
    m = _midia(pasta)
    feito = json.loads((m / "voz.json").read_text())
    p = plano(pasta)
    bl = blocos(pasta)
    il = _ilustrador(pasta, cfg)
    tmp = m / "tmp"
    tmp.mkdir(exist_ok=True)
    # 1) áudio: partes + pausas, e onde começa cada bloco/parte
    silencios = {}
    for d in (PAUSA_PARTE, PAUSA_BLOCO):
        s = tmp / f"sil_{d}.mp3"
        rodar(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=mono", "-t", str(d), "-b:a", "80k", str(s)])
        silencios[d] = s
    lista, t, inicio_bloco, legendas = [], 0.0, [], []
    for b in bl:
        inicio_bloco.append((t, b))
        partes = _partes(b["texto"])
        for i, texto in enumerate(partes, 1):
            chave = f"b{b['n']:02d}_p{i:02d}"
            lista.append(m / "voz" / f"{chave}.mp3")
            legendas.append((t, feito[chave], texto))
            t += feito[chave]
            pausa = PAUSA_BLOCO if i == len(partes) else PAUSA_PARTE
            lista.append(silencios[pausa])
            t += pausa
    total = t
    lst = tmp / "voz.txt"
    lst.write_text("".join(f"file '{a.resolve()}'\n" for a in lista))
    voz = tmp / "voz.m4a"
    rodar(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c:a", "aac", "-b:a", "128k", str(voz)],
          timeout=3600)
    # 2) vídeo: as imagens de cada bloco dividem o tempo do bloco
    clipes, k = [], 0
    disponiveis = [il._destino(d) for d in _pedidos_imagens(pasta) if il._destino(d).exists()]
    for j, (ini, b) in enumerate(inicio_bloco):
        fim = inicio_bloco[j + 1][0] if j + 1 < len(inicio_bloco) else total
        imgs = [il._destino(d) for d in b.get("imagens", [])]
        imgs = [x if x.exists() else disponiveis[(k + n) % len(disponiveis)] for n, x in enumerate(imgs)]
        cada = (fim - ini) / len(imgs)
        for x in imgs:
            k += 1
            clipes.append(_clipe(x, cada, tmp / f"c{k:03d}.mp4", k))
            log.info("clipe %d pronto (%.0f s)", k, cada)
    lv = tmp / "video.txt"
    lv.write_text("".join(f"file '{c.resolve()}'\n" for c in clipes))
    mudo = tmp / "mudo.mp4"
    rodar(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lv), "-c", "copy", str(mudo)], timeout=3600)
    saida = m / "video.mp4"
    if cfg["longos"]["formato"] == "dormir":   # fundo de ruído marrom bem baixinho (sem música, sem direitos)
        rodar(["ffmpeg", "-y", "-v", "error", "-i", str(mudo), "-i", str(voz), "-f", "lavfi", "-i",
               f"anoisesrc=c=brown:a=0.04:d={total + 3:.0f}", "-filter_complex",
               "[2:a]lowpass=f=500,volume=0.35[r];[1:a][r]amix=inputs=2:duration=first:normalize=0,afade=t=out:st="
               f"{max(0, total - 8):.0f}:d=8[a]", "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
               "-shortest", str(saida)], timeout=3600)
    else:
        rodar(["ffmpeg", "-y", "-v", "error", "-i", str(mudo), "-i", str(voz), "-map", "0:v", "-map", "1:a",
               "-c:v", "copy", "-c:a", "copy", "-shortest", str(saida)], timeout=3600)
    # 3) legendas proporcionais e capítulos
    srt, n = [], 1
    for ini, dur, texto in legendas:
        ws = texto.split()
        grupos = [ws[i:i + 12] for i in range(0, len(ws), 12)]
        for g_i, g in enumerate(grupos):
            a = ini + dur * g_i / len(grupos)
            b = ini + dur * (g_i + 1) / len(grupos)
            def ts(x):
                return f"{int(x // 3600):02d}:{int(x % 3600 // 60):02d}:{int(x % 60):02d},{int(x % 1 * 1000):03d}"
            srt.append(f"{n}\n{ts(a)} --> {ts(b)}\n{' '.join(g)}\n")
            n += 1
    (m / "legendas.srt").write_text("\n".join(srt), encoding="utf-8")
    capitulos = "\n".join(f"{_hms(ini)} {b['capitulo']}" for ini, b in inicio_bloco)
    # 4) thumbnail
    th = p["thumbnail"]
    img_th = il._destino(th["cena"]) if th.get("cena") and il._destino(th["cena"]).exists() else (disponiveis[0] if disponiveis else None)
    cartoes.thumbnail(cfg, th["texto"], img_th, th.get("layout", "direita"), m / "thumbnail.jpg")
    fontes = sorted({f for b in bl for f in b.get("fontes", [])} | set(p.get("fontes", [])))
    desc = p["descricao"].strip() + "\n\nCapítulos:\n" + capitulos
    if fontes:
        desc += "\n\nFontes:\n" + "\n".join(f"- {f}" for f in fontes[:40])
    desc += "\n\nIlustrações criadas com auxílio de IA. Narração com voz gerada por IA."
    if p.get("hashtags"):
        desc += "\n\n" + " ".join(p["hashtags"][:3])
    (m / "descricao.txt").write_text(desc[:5000], encoding="utf-8")
    salvar(pasta, duracao_s=round(total, 1))
    log.info("vídeo longo montado: %s (%s)", saida, _hms(total))
    return saida


# ---------------------------------------------------------------- YouTube
def _enviar_nao_listado(pasta: Path, cfg: dict) -> dict:
    from googleapiclient.http import MediaFileUpload
    from .youtube import _enviar, playlist_id, servico
    m, p = _midia(pasta), plano(pasta)
    yt = servico(cfg["segredo_youtube"])
    corpo = {"snippet": {"title": p["titulo_youtube"][:100], "description": (m / "descricao.txt").read_text(encoding="utf-8"),
                         "tags": p.get("tags", [])[:30], "categoryId": cfg["youtube"]["categoria_id"],
                         "defaultLanguage": cfg["youtube"]["idioma"], "defaultAudioLanguage": cfg["youtube"]["idioma"]},
             "status": {"privacyStatus": "unlisted", "selfDeclaredMadeForKids": False}}
    media = MediaFileUpload(str(m / "video.mp4"), mimetype="video/mp4", chunksize=32 * 1024 * 1024, resumable=True)
    vid = _enviar(yt.videos().insert(part="snippet,status", body=corpo, media_body=media))["id"]
    avisos = []
    for acao in ("thumb", "leg", "playlist"):
        try:
            if acao == "thumb":
                yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(str(m / "thumbnail.jpg"), mimetype="image/jpeg")).execute()
            elif acao == "leg":
                yt.captions().insert(part="snippet", body={"snippet": {"videoId": vid, "language": "pt-BR", "name": "Português"}},
                                     media_body=MediaFileUpload(str(m / "legendas.srt"), mimetype="application/octet-stream")).execute()
            else:
                pid = playlist_id(yt, cfg["longos"]["nome_formato"], cfg)
                yt.playlistItems().insert(part="snippet", body={"snippet": {"playlistId": pid,
                                          "resourceId": {"kind": "youtube#video", "videoId": vid}}}).execute()
        except Exception as e:
            avisos.append(f"{acao}: {str(e)[:120]}")
    pub = {"video_id": vid, "url": f"https://youtu.be/{vid}", "avisos": avisos}
    (pasta / "publicacao.json").write_text(json.dumps(pub, ensure_ascii=False, indent=2), encoding="utf-8")
    return pub


def _proximo_slot(cfg: dict) -> str:
    from .agenda import BRT, DIAS
    ocupados = {ler(p).get("publicar_em_utc") for p in todas() if ler(p).get("etapa") == "agendado"}
    agora = datetime.now(timezone.utc).astimezone(BRT)
    for dias in range(1, 60):
        d = (agora + timedelta(days=dias)).date()
        for s in cfg["longos"]["publicar"]:
            dia, hora = s.split()
            if d.weekday() != DIAS[dia[:3]]:
                continue
            h, mi = map(int, hora.split(":"))
            iso = datetime(d.year, d.month, d.day, h, mi, tzinfo=BRT).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            if iso not in ocupados:
                return iso
    raise RuntimeError("sem horário livre")


def agendar(pasta: Path) -> dict:
    from .agenda import BRT
    from .youtube import servico
    from . import telegram as T
    e = ler(pasta)
    cfg = carregar_config(e["canal"])
    pub = json.loads((pasta / "publicacao.json").read_text(encoding="utf-8"))
    quando = _proximo_slot(cfg)
    servico(cfg["segredo_youtube"]).videos().update(part="status", body={"id": pub["video_id"], "status": {
        "privacyStatus": "private", "publishAt": quando, "selfDeclaredMadeForKids": False}}).execute()
    pub["publicar_em_utc"] = quando
    (pasta / "publicacao.json").write_text(json.dumps(pub, ensure_ascii=False, indent=2), encoding="utf-8")
    salvar(pasta, etapa="agendado", publicar_em_utc=quando, url=pub["url"])
    q = datetime.fromisoformat(quando.replace("Z", "+00:00")).astimezone(BRT)
    T.enviar(f"✅ Vídeo longo agendado — {T.esc(cfg['nome'])}\n<b>{T.esc(plano(pasta)['titulo_youtube'])}</b>\n"
             f"📅 {q:%d/%m às %Hh%M}\n🔗 {pub['url']}\n\n"
             "Dica: em vídeos para dormir, deixe poucos anúncios no meio (YouTube Studio › vídeo › Monetização › Intervalos de anúncios).")
    return pub


# ---------------------------------------------------------------- avançar (rodadas automáticas)
def avancar(pasta: Path) -> str:
    from . import estado as E
    from . import telegram as T
    e = ler(pasta)
    cfg = carregar_config(e["canal"])
    etapa = e["etapa"]
    if etapa == "escrevendo" and len(blocos(pasta)) >= e["blocos_total"]:
        etapa = salvar(pasta, etapa="narrando")["etapa"]
    if etapa == "narrando":
        if not narrar(pasta, cfg):
            return etapa
        etapa = salvar(pasta, etapa="imagens")["etapa"]
    if etapa == "imagens":
        # a cota grátis de imagens é dividida com os vídeos da rotina: eles têm prioridade
        from . import estado as E2
        if any(ev.get("etapa") in ("producao_json", "renderizando", "aguardando_cota") for _, ev in E2.todos_videos()):
            log.info("um vídeo da rotina está usando a cota de imagens — o longo espera a próxima rodada")
            return etapa
        fracao = imagens(pasta, cfg)
        if fracao < 0.9 and not os.environ.get("FORCAR_SEM_IMAGEM"):
            log.info("imagens em %.0f%% — espera a cota voltar", fracao * 100)
            return etapa
        etapa = salvar(pasta, etapa="montando")["etapa"]
    if etapa == "montando":
        montar(pasta, cfg)
        pub = _enviar_nao_listado(pasta, cfg)
        salvar(pasta, etapa="aguardando_aprovacao_longo", url=pub["url"])
        p = plano(pasta)
        ids = T.enviar(f"🌙 <b>Vídeo longo pronto — {T.esc(cfg['nome'])}</b>\n<b>{T.esc(p['titulo_youtube'])}</b>\n"
                       f"⏱️ {_hms(ler(pasta).get('duracao_s', 0))}\n🔗 {pub['url']} (não listado: só quem tem o link vê)\n\n"
                       "Assista um pouco e <b>responda aprovar</b> para agendar, ou <b>cancelar</b>."
                       + ("".join(f"\n⚠️ {T.esc(a)}" for a in pub.get("avisos", []))))
        E.registrar_msgs(ids[:1], pasta, "longo_video")
        etapa = "aguardando_aprovacao_longo"
    return etapa


def status() -> str:
    linhas = ["🌙 <b>Vídeos longos</b>\n"]
    for p in todas():
        e = ler(p)
        if e.get("etapa") in ("cancelado",):
            continue
        nome = carregar_config(e["canal"])["nome"]
        extra = ""
        if e["etapa"] in ("escrevendo", "narrando", "imagens"):
            extra = f" · blocos {len(blocos(p))}/{e['blocos_total']}"
            vj = p / "midia" / "voz.json"
            if vj.exists():
                total_partes = sum(len(_partes(b["texto"])) for b in blocos(p))
                extra += f" · narração {len(json.loads(vj.read_text()))}/{total_partes}"
        titulo = plano(p).get("titulo_youtube") if (p / "plano.json").exists() else e.get("tema")
        linhas.append(f"• <b>{nome}</b>: {titulo}\n   {ETAPAS.get(e['etapa'], e['etapa'])}{extra}"
                      + (f"\n   🔗 {e['url']}" if e.get("url") else ""))
    if len(linhas) == 1:
        linhas.append("Nenhum em produção. Comece com /longo ouro <tema>, /longo livros <tema> ou /longo mapeado <matéria>.")
    return "\n".join(linhas)


def para_escrever() -> Path | None:
    """O vídeo longo que deve ganhar blocos nesta rodada (um por rodada, para poupar o plano do Claude)."""
    for p in todas():
        e = ler(p)
        if e.get("etapa") == "escrevendo" and len(blocos(p)) < e["blocos_total"]:
            return p
    return None


def sugerir_quem() -> str | None:
    """Canal que deve receber 3 sugestões de tema nesta rodada (vídeo longo semanal automático)."""
    from .agenda import BRT, DIAS
    agora = datetime.now(timezone.utc).astimezone(BRT)
    semana = agora.strftime("%G-W%V")
    for cfg_arq in sorted((RAIZ / "pipeline" / "config").glob("*.yaml")):
        canal = cfg_arq.stem
        if canal == "geral":
            continue
        cfg = carregar_config(canal)
        auto = (cfg.get("longos") or {}).get("automatico") or {}
        if not auto.get("ligado") or not cfg.get("ativo", True):
            continue
        if agora.weekday() < DIAS[auto.get("dia_sugestao", "mon")[:3]]:
            continue   # ainda não chegou o dia desta semana
        arq = RAIZ / "canais" / canal / "longos" / "sugestoes.json"
        if arq.exists() and json.loads(arq.read_text(encoding="utf-8")).get("semana") == semana:
            continue   # já sugeriu nesta semana
        ocupado = [p for p in todas() if ler(p).get("canal") == canal
                   and ler(p).get("etapa") not in ("agendado", "cancelado", "publicado")]
        if ocupado:
            continue   # ainda tem um longo andando: não empilha
        return canal
    return None


def cancelar(pasta: Path) -> None:
    pub = pasta / "publicacao.json"
    if pub.exists():
        from .youtube import servico
        cfg = carregar_config(ler(pasta)["canal"])
        try:
            servico(cfg["segredo_youtube"]).videos().update(part="status", body={
                "id": json.loads(pub.read_text())["video_id"], "status": {"privacyStatus": "private"}}).execute()
        except Exception as e:
            log.warning("não consegui deixar privado: %s", e)
    salvar(pasta, etapa="cancelado")


def _saida(**kv):
    arq = os.environ.get("GITHUB_OUTPUT")
    if arq:
        with open(arq, "a") as f:
            for k, v in kv.items():
                f.write(f"{k}={v}\n")


def main():
    acao = sys.argv[1]
    if acao == "para-escrever":
        p = para_escrever()
        _saida(escrever=rel(p) if p else "")
        print(rel(p) if p else "nenhum")
        return
    if acao == "em-andamento":
        ps = [rel(p) for p in todas() if ler(p).get("etapa") in ("escrevendo", "narrando", "imagens", "montando")]
        _saida(andamento=" ".join(ps))
        print(" ".join(ps))
        return
    if acao == "sugerir-quem":
        c = sugerir_quem()
        _saida(sugerir=c or "")
        print(c or "nenhum")
        return
    if acao == "criar":
        print(rel(criar(sys.argv[2], " ".join(sys.argv[3:]))))
    elif acao == "status":
        print(status())
    else:
        pasta = Path(sys.argv[2])
        pasta = pasta if pasta.is_absolute() else RAIZ / pasta
        if acao == "validar":
            er = validar(pasta)
            print("OK" if not er else "Corrija:\n- " + "\n- ".join(er))
            sys.exit(1 if er else 0)
        elif acao == "avancar":
            print(avancar(pasta))
        elif acao == "agendar":
            agendar(pasta)
        elif acao == "cancelar":
            cancelar(pasta)
        elif acao == "montar-teste":
            cfg = carregar_config(ler(pasta)["canal"])
            print(montar(pasta, cfg))


if __name__ == "__main__":
    main()
