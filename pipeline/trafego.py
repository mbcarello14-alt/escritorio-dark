"""Gestor de tráfego orgânico: a parte mecânica (coletar dados e aplicar as decisões do agente).

  python -m pipeline.trafego coletar   → canais/trafego/resumo.json e pendentes.json (+ publica comentários iniciais)
  python -m pipeline.trafego aplicar   → executa canais/trafego/acoes.json (respostas e trocas de título) e avisa no Telegram

Nada de engajamento falso: só o próprio canal agindo (responder, organizar, reembalar).
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from .comum import RAIZ, carregar_config, log

PASTA = RAIZ / "canais" / "trafego"
ESTADO = PASTA / "estado.json"
CANAIS = ("historia", "vestibular", "livros")
MAX_RESPOSTAS = 15        # por canal, por rodada
MAX_TITULOS_DIA = 2       # trocas de título por canal, por dia


def _ler(arq: Path, padrao):
    return json.loads(arq.read_text(encoding="utf-8")) if arq.exists() else padrao


def _gravar(arq: Path, dados) -> None:
    arq.parent.mkdir(parents=True, exist_ok=True)
    arq.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")


def _agora() -> datetime:
    return datetime.now(timezone.utc)


def _publicacoes(canal: str) -> list[tuple[Path, dict]]:
    out = []
    for arq in sorted((RAIZ / "canais" / canal / "videos").glob("*/publicacao.json")):
        pub = _ler(arq, {})
        if pub.get("video_id"):
            out.append((arq, pub))
    return out


def coletar() -> bool:
    from googleapiclient.errors import HttpError
    from .youtube import comentar, servico

    estado = _ler(ESTADO, {"respondidos": [], "titulos": []})
    resumo, pendentes = {"gerado_em": _agora().isoformat(timespec="seconds"), "canais": {}}, []
    for canal in CANAIS:
        cfg = carregar_config(canal)
        if not cfg.get("ativo"):
            continue
        pubs = _publicacoes(canal)
        if not pubs:
            continue
        try:
            yt = servico(cfg["segredo_youtube"])
            ch = yt.channels().list(part="id,statistics", mine=True).execute()["items"][0]
        except BaseException as e:
            log.warning("%s: sem acesso ao YouTube (%s)", canal, e)
            continue
        # vídeos longos e Shorts conhecidos
        ids = {}
        for arq, pub in pubs:
            ids[pub["video_id"]] = {"tipo": "longo", "pasta": str(arq.parent.relative_to(RAIZ)), "titulo": pub["titulo"],
                                    "publicar_em_utc": pub.get("publicar_em_utc")}
            for c in pub.get("cortes", []):
                if c.get("video_id"):
                    ids[c["video_id"]] = {"tipo": "short", "pasta": str(arq.parent.relative_to(RAIZ)), "titulo": c["titulo"],
                                          "publicar_em_utc": c.get("publicar_em_utc"), "longo": pub["video_id"]}
        videos = []
        lista = list(ids)
        for i in range(0, len(lista), 50):
            r = yt.videos().list(part="snippet,statistics,status", id=",".join(lista[i:i + 50])).execute()
            for v in r.get("items", []):
                info = ids[v["id"]]
                publico = v["status"]["privacyStatus"] == "public"
                quando = info.get("publicar_em_utc") or v["snippet"]["publishedAt"]
                idade_h = round((_agora() - datetime.fromisoformat(quando.replace("Z", "+00:00"))).total_seconds() / 3600, 1)
                m7 = _ler(RAIZ / info["pasta"] / "metricas.json", {}).get("janelas", {}).get("7", {}).get("metricas", {})
                videos.append({"video_id": v["id"], "tipo": info["tipo"], "titulo_atual": v["snippet"]["title"],
                               "publico": publico, "idade_horas": idade_h, "pasta": info["pasta"],
                               "views": int(v["statistics"].get("viewCount", 0)), "likes": int(v["statistics"].get("likeCount", 0)),
                               "comentarios": int(v["statistics"].get("commentCount", 0)), "metricas_7d": m7,
                               "titulo_ja_trocado": any(t["video_id"] == v["id"] for t in estado["titulos"])})
                # comentário inicial que ficou para quando o vídeo abrisse
                if info["tipo"] == "longo" and publico:
                    arq = RAIZ / info["pasta"] / "publicacao.json"
                    pub = _ler(arq, {})
                    if pub.get("comentario_pendente") and pub.get("comentario_inicial"):
                        try:
                            comentar(yt, v["id"], pub["comentario_inicial"])
                            pub["comentario_pendente"] = False
                            _gravar(arq, pub)
                            log.info("comentário inicial publicado em %s", v["id"])
                        except HttpError as e:
                            log.warning("comentário inicial falhou (%s)", e.resp.status)
        resumo["canais"][canal] = {"nome": cfg["nome"], "inscritos": int(ch["statistics"].get("subscriberCount", 0)),
                                   "videos": videos}
        # comentários novos que o canal ainda não respondeu
        try:
            r = yt.commentThreads().list(part="snippet,replies", allThreadsRelatedToChannelId=ch["id"],
                                         order="time", maxResults=100, textFormat="plainText").execute()
        except HttpError as e:
            log.warning("%s: não li os comentários (%s)", canal, e.resp.status)
            continue
        for th in r.get("items", []):
            top = th["snippet"]["topLevelComment"]
            sn = top["snippet"]
            if th["id"] in estado["respondidos"] or sn.get("authorChannelId", {}).get("value") == ch["id"]:
                continue
            respostas = (th.get("replies") or {}).get("comments", [])
            if any(c["snippet"].get("authorChannelId", {}).get("value") == ch["id"] for c in respostas):
                continue
            pendentes.append({"canal": canal, "comentario_id": th["id"], "video_id": th["snippet"].get("videoId"),
                              "video_titulo": ids.get(th["snippet"].get("videoId"), {}).get("titulo", ""),
                              "autor": sn.get("authorDisplayName"), "texto": sn.get("textDisplay", "")[:1500],
                              "curtidas": sn.get("likeCount", 0), "publicado": sn.get("publishedAt")})
    _gravar(PASTA / "resumo.json", resumo)
    _gravar(PASTA / "pendentes.json", pendentes)
    tem = bool(pendentes) or any(v["publico"] for c in resumo["canais"].values() for v in c["videos"])
    log.info("tráfego: %d comentários para responder, %d canais com vídeos", len(pendentes), len(resumo["canais"]))
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"trabalho={'sim' if tem else ''}\n")
    return tem


def aplicar() -> None:
    from googleapiclient.errors import HttpError
    from .youtube import responder, servico

    acoes = _ler(PASTA / "acoes.json", {})
    estado = _ler(ESTADO, {"respondidos": [], "titulos": []})
    pendentes = {p["comentario_id"]: p for p in _ler(PASTA / "pendentes.json", [])}
    feitos = {"respostas": {}, "titulos": [], "alertas": acoes.get("alertas", [])}
    servicos = {}

    def yt_de(canal):
        if canal not in servicos:
            servicos[canal] = servico(carregar_config(canal)["segredo_youtube"])
        return servicos[canal]

    for a in acoes.get("respostas", []):
        p = pendentes.get(a.get("comentario_id"))
        if not p or not a.get("texto"):
            continue
        canal = p["canal"]
        if feitos["respostas"].get(canal, 0) >= MAX_RESPOSTAS:
            continue
        try:
            responder(yt_de(canal), p["comentario_id"], a["texto"])
            estado["respondidos"].append(p["comentario_id"])
            feitos["respostas"][canal] = feitos["respostas"].get(canal, 0) + 1
        except HttpError as e:
            log.warning("resposta falhou (%s)", e.resp.status)
    for c in acoes.get("ignorar", []):     # spam, ofensa: não responder e não mostrar de novo
        if c in pendentes:
            estado["respondidos"].append(c)

    hoje = _agora().date().isoformat()
    for t in acoes.get("titulos", []):
        canal, vid, novo = t.get("canal"), t.get("video_id"), (t.get("novo_titulo") or "").strip()
        if not (canal and vid and 10 <= len(novo) <= 100):
            continue
        if any(x["video_id"] == vid for x in estado["titulos"]):
            continue
        if sum(1 for x in estado["titulos"] if x["canal"] == canal and x["em"].startswith(hoje)) >= MAX_TITULOS_DIA:
            continue
        try:
            yt = yt_de(canal)
            v = yt.videos().list(part="snippet", id=vid).execute()["items"][0]
            sn = v["snippet"]
            antigo = sn["title"]
            corpo = {"id": vid, "snippet": {"title": novo, "categoryId": sn["categoryId"], "description": sn.get("description", ""),
                                            "tags": sn.get("tags", []), "defaultLanguage": sn.get("defaultLanguage", "pt-BR"),
                                            "defaultAudioLanguage": sn.get("defaultAudioLanguage", "pt-BR")}}
            yt.videos().update(part="snippet", body=corpo).execute()
            reg = {"canal": canal, "video_id": vid, "antes": antigo, "depois": novo, "motivo": t.get("motivo", ""),
                   "em": _agora().isoformat(timespec="seconds")}
            estado["titulos"].append(reg)
            feitos["titulos"].append(reg)
        except (HttpError, IndexError, KeyError) as e:
            log.warning("troca de título falhou: %s", e)

    estado["respondidos"] = estado["respondidos"][-3000:]
    _gravar(ESTADO, estado)
    (PASTA / "acoes.json").unlink(missing_ok=True)
    _avisar(feitos, acoes.get("resumo", ""))


def _avisar(feitos: dict, resumo: str) -> None:
    from . import telegram as T
    total = sum(feitos["respostas"].values())
    if not (total or feitos["titulos"] or feitos["alertas"] or resumo):
        return
    nomes = {c: carregar_config(c)["nome"] for c in CANAIS}
    linhas = ["📈 <b>Gestor de tráfego</b>"]
    if resumo:
        linhas.append(T.esc(resumo))
    if total:
        linhas.append("💬 Respondi " + ", ".join(f"{n} no {nomes[c]}" for c, n in feitos["respostas"].items()) + " comentários")
    for t in feitos["titulos"]:
        linhas.append(f"✏️ {nomes[t['canal']]}: título trocado\nde “{T.esc(t['antes'])}”\npara “{T.esc(t['depois'])}”\n"
                      f"<i>{T.esc(t['motivo'])}</i>")
    for a in feitos["alertas"]:
        linhas.append(f"⚠️ {T.esc(a)}")
    T.enviar("\n\n".join(linhas))


if __name__ == "__main__":
    {"coletar": coletar, "aplicar": aplicar}[sys.argv[1]]()
