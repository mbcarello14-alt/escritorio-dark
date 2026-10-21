"""Coleta métricas dos vídeos publicados (YouTube Analytics) e salva em metricas.json de cada vídeo.

Uso: python -m pipeline.metricas            # todos os canais
     python -m pipeline.metricas historia   # um canal
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta, timezone

from .comum import RAIZ, carregar_config, log

BASICAS = "views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,subscribersGained,likes,comments,shares"
EXTRAS = "videoThumbnailImpressions,videoThumbnailImpressionsClickRate"


def _consulta(ana, inicio, fim, metricas, **kw):
    return ana.reports().query(ids="channel==MINE", startDate=inicio, endDate=fim, metrics=metricas, **kw).execute()


def _linha(resp) -> dict:
    cab = [c["name"] for c in resp.get("columnHeaders", [])]
    linhas = resp.get("rows") or []
    return dict(zip(cab, linhas[0])) if linhas else {}


def coletar_canal(canal: str) -> int:
    from googleapiclient.errors import HttpError
    from .youtube import servico

    cfg = carregar_config(canal)
    pastas = [p for p in (RAIZ / "canais" / canal / "videos").glob("*/publicacao.json")]
    if not pastas:
        log.info("%s: nenhum vídeo publicado ainda", canal)
        return 0
    ana = servico(cfg["segredo_youtube"], "youtubeAnalytics", "v2")
    yt = servico(cfg["segredo_youtube"])
    hoje = date.today()
    feitos = 0
    canal_stats = yt.channels().list(part="statistics", mine=True).execute()["items"][0]["statistics"]
    for arq in pastas:
        pub = json.loads(arq.read_text(encoding="utf-8"))
        vid, quando = pub.get("video_id"), pub.get("publicar_em_utc")
        if not vid or not quando:
            continue
        publicado = datetime.fromisoformat(quando.replace("Z", "+00:00")).date()
        idade = (hoje - publicado).days
        if idade < 2:
            continue
        saida = arq.parent / "metricas.json"
        dados = json.loads(saida.read_text(encoding="utf-8")) if saida.exists() else {"video_id": vid, "janelas": {}}
        for janela in (7, 28):
            if idade < janela or str(janela) in dados["janelas"]:
                continue
            fim = (publicado + timedelta(days=janela)).isoformat()
            filtro = f"video=={vid}"
            try:
                m = _linha(_consulta(ana, publicado.isoformat(), fim, f"{BASICAS},{EXTRAS}", filters=filtro))
            except HttpError:
                m = _linha(_consulta(ana, publicado.isoformat(), fim, BASICAS, filters=filtro))
            try:
                curva = _consulta(ana, publicado.isoformat(), fim, "audienceWatchRatio",
                                  dimensions="elapsedVideoTimeRatio", filters=filtro).get("rows", [])
            except HttpError:
                curva = []
            fontes = _consulta(ana, publicado.isoformat(), fim, "views", dimensions="insightTrafficSourceType",
                               filters=filtro, sort="-views").get("rows", [])
            dados["janelas"][str(janela)] = {"ate": fim, "metricas": m, "retencao": curva, "trafego": fontes}
            feitos += 1
        dados["parcial"] = _linha(_consulta(ana, publicado.isoformat(), hoje.isoformat(), BASICAS, filters=f"video=={vid}"))
        dados["canal"] = canal_stats
        dados["atualizado_em"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        saida.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    # horas assistidas nos últimos 365 dias (para acompanhar a meta do Programa de Parcerias)
    ano = _linha(_consulta(ana, (hoje - timedelta(days=365)).isoformat(), hoje.isoformat(), "estimatedMinutesWatched"))
    resumo = {"inscritos": int(canal_stats.get("subscriberCount", 0)),
              "horas_365d": round(float(ano.get("estimatedMinutesWatched", 0)) / 60, 1),
              "atualizado_em": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    (RAIZ / "canais" / canal / "metricas-canal.json").write_text(json.dumps(resumo, indent=2), encoding="utf-8")
    log.info("%s: %d janelas novas; %s", canal, feitos, resumo)
    return feitos


def main():
    canais = sys.argv[1:] or [p.stem for p in (RAIZ / "pipeline" / "config").glob("*.yaml")]
    for c in canais:
        try:
            coletar_canal(c)
        except SystemExit as e:
            log.warning("%s: %s", c, e)


if __name__ == "__main__":
    main()
