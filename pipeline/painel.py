"""Gera canais/painel-estado.json — o que o escritório virtual mostra."""
from __future__ import annotations

import json
from datetime import date, datetime, timezone

from . import estado as E
from .comum import RAIZ

# quem está trabalhando em cada etapa
QUEM = {
    "pauta": ["pesquisador_{canal}"],
    "roteiro": ["pesquisador_{canal}", "roteirista_{canal}", "checador", "guardiao"],
    "ajuste": ["roteirista_{canal}", "checador"],
    "producao_json": ["diretor_visual", "seo", "thumbnail"],
    "renderizando": ["narrador", "ilustrador", "editor", "clipador"],
    "aguardando_escolha": ["miguel"],
    "aguardando_aprovacao": ["miguel"],
    "aguardando_audio": ["miguel"],
}


def gerar() -> dict:
    agora = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    videos, ativos = [], {}
    for pasta, e in E.todos_videos():
        etapa = e.get("etapa", "")
        item = {"canal": e.get("canal"), "dia": e.get("dia"), "rotulo": e.get("rotulo"),
                "publicar_em_utc": e.get("publicar_em_utc"), "etapa": etapa,
                "etapa_txt": E.ETAPAS.get(etapa, etapa), "titulo": e.get("titulo", ""), "url": e.get("url", "")}
        if etapa == "aguardando_audio":
            item["audios"] = [len(E.blocos_com_audio(pasta)), E.total_blocos(pasta)]
        videos.append(item)
        for quem in QUEM.get(etapa, []):
            quem = quem.format(canal=e.get("canal", ""))
            ativos.setdefault(quem, []).append(f"{E.nome_canal(e['canal'])}: {e.get('titulo') or e.get('rotulo')}")
    for arq in sorted((RAIZ / "canais").glob("*/reels/*/estado.json")):
        r = json.loads(arq.read_text(encoding="utf-8"))
        quem = {"roteiro_reel": f"reels_{r.get('canal')}", "ajuste_reel": f"reels_{r.get('canal')}",
                "renderizando_reel": f"reels_{r.get('canal')}", "aguardando_aprovacao_reel": "miguel"}.get(r.get("etapa"))
        if quem:
            ativos.setdefault(quem, []).append(f"Reel {E.nome_canal(r.get('canal'))}: {r.get('titulo') or 'criando'}")
    for arq in sorted((RAIZ / "canais").glob("*/longos/*/estado.json")):
        lg = json.loads(arq.read_text(encoding="utf-8"))
        quem = {"planejando": f"roteirista_{lg.get('canal')}", "ajuste_plano": f"roteirista_{lg.get('canal')}",
                "escrevendo": f"roteirista_{lg.get('canal')}", "narrando": "narrador", "imagens": "ilustrador",
                "montando": "editor", "aguardando_plano": "miguel", "aguardando_aprovacao_longo": "miguel"}.get(lg.get("etapa"))
        if quem:
            ativos.setdefault(quem, []).append(f"Longo {E.nome_canal(lg.get('canal'))}: {lg.get('tema', '')}")
    canais = []
    for c in E.CANAIS:
        m = json.loads((RAIZ / "canais" / c / "metricas-canal.json").read_text()) \
            if (RAIZ / "canais" / c / "metricas-canal.json").exists() else {}
        canais.append({"id": c, "nome": E.nome_canal(c), "inscritos": m.get("inscritos", 0),
                       "horas": m.get("horas_365d", 0),
                       "publicados": sum(1 for v in videos if v["canal"] == c and v["etapa"] == "agendado"
                                         and (v["publicar_em_utc"] or "") <= agora)})
    g = json.loads((RAIZ / "canais" / "gastos-imagens.json").read_text()) \
        if (RAIZ / "canais" / "gastos-imagens.json").exists() else {}
    hoje = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    flux = g.get("flux", {}).get(hoje, {})
    hf = g.get("higgsfield", {}).get(date.today().strftime("%Y-%m"), {})
    geral = E.config_geral()
    teto_flux = geral.get("ilustracoes", {}).get("flux", {}).get("teto_diario_neurons", 9500)
    proximos = [v for v in videos if (v["publicar_em_utc"] or "") >= agora][:8]
    feitos = [v for v in videos if v["etapa"] == "agendado" and (v["publicar_em_utc"] or "") < agora][-6:]
    return {"atualizado_em": agora, "ativos": ativos, "proximos": proximos, "publicados": feitos,
            "canais": canais, "imagens": {"hoje": flux.get("imagens", 0), "neurons": flux.get("neurons", 0), "teto_neurons": teto_flux,
                        "higgsfield_usd": hf.get("usd", 0), "higgsfield_teto": geral["higgsfield"]["teto_mensal_usd"]}}


def main():
    dados = gerar()
    (RAIZ / "canais" / "painel-estado.json").write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"painel: {len(dados['proximos'])} próximos, ativos: {', '.join(dados['ativos']) or 'ninguém'}")


if __name__ == "__main__":
    main()
