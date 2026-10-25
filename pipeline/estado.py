"""Estado dos vídeos e mapa de mensagens do Telegram.

- canais/<canal>/videos/<AAAA-MM-DD>/estado.json  → etapa do vídeo
- canais/mensagens/<message_id>.json             → a que vídeo/etapa uma mensagem do bot pertence
- canais/<canal>/videos/<pasta>/audio/bloco_NN.json → file_id do áudio gravado

Um arquivo por coisa: assim execuções simultâneas nunca brigam no git.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

from .comum import RAIZ, carregar_config

BRT = ZoneInfo("America/Sao_Paulo")
CANAIS = ["historia", "vestibular", "livros"]
DIAS = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
NOMES_DIA = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]
MSG = RAIZ / "canais" / "mensagens"

ETAPAS = {
    "pauta": "🔎 pesquisando pautas",
    "aguardando_escolha": "👉 esperando você escolher a pauta",
    "roteiro": "✍️ escrevendo e checando o roteiro",
    "aguardando_aprovacao": "👉 esperando você aprovar o roteiro",
    "ajuste": "✍️ ajustando o roteiro",
    "producao_json": "🎨 planejando cenas, título e thumbnail",
    "aguardando_audio": "🎙️ esperando seus áudios",
    "renderizando": "🎬 montando o vídeo",
    "aguardando_cota": "🎨 esperando a cota de imagens para desenhar",
    "agendado": "✅ agendado no YouTube",
    "erro": "⚠️ deu erro",
}


def _ler(p: Path, padrao=None):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else padrao


def _gravar(p: Path, dados) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------------------------------------------------------------- vídeos
def pasta_video(canal: str, dia: str) -> Path:
    return RAIZ / "canais" / canal / "videos" / dia


def rel(p: Path) -> str:
    return str(p.relative_to(RAIZ)).replace("\\", "/")


def ler_estado(pasta: Path) -> dict:
    return _ler(pasta / "estado.json", {})


def salvar_estado(pasta: Path, **mudancas) -> dict:
    e = ler_estado(pasta)
    e.update(mudancas)
    e["atualizado_em"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    _gravar(pasta / "estado.json", e)
    return e


def todos_videos() -> list[tuple[Path, dict]]:
    out = []
    for c in CANAIS:
        for p in sorted((RAIZ / "canais" / c / "videos").glob("*/estado.json")):
            out.append((p.parent, _ler(p, {})))
    return sorted(out, key=lambda x: x[1].get("publicar_em_utc", ""))


def nome_canal(canal: str) -> str:
    return carregar_config(canal)["nome"]


# ---------------------------------------------------------------- agenda
def grade() -> list[tuple[int, int, int, str]]:
    """[(dia_semana, hora, minuto, canal)] da rotina de todos os canais."""
    out = []
    for c in CANAIS:
        cfg = carregar_config(c)
        if not cfg.get("ativo", True):
            continue
        for item in cfg["youtube"]["publicar"]:
            d, h = item.split()
            hh, mm = map(int, h.split(":"))
            out.append((DIAS[d.lower()[:3]], hh, mm, c))
    return out


def proximos_slots(dias: int = 4, inicio: date | None = None) -> list[dict]:
    """Slots da rotina nos próximos `dias` dias (a partir de amanhã) que ainda não têm vídeo."""
    hoje = inicio or datetime.now(BRT).date()
    comeco = date.fromisoformat(str(config_geral().get("producao", {}).get("inicio_rotina", "2000-01-01")))
    ocupados = {e.get("publicar_em_utc") for _, e in todos_videos()}
    out = []
    for k in range(1, dias + 1):
        d = hoje + timedelta(days=k)
        for wd, hh, mm, c in sorted(grade(), key=lambda g: (g[1], g[2])):
            if d.weekday() != wd:
                continue
            pasta = pasta_video(c, d.isoformat())
            if (pasta / "estado.json").exists() or d < comeco:
                continue
            quando = datetime(d.year, d.month, d.day, hh, mm, tzinfo=BRT)
            if quando.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") in ocupados:
                continue
            out.append({"canal": c, "dia": d.isoformat(), "pasta": pasta,
                        "publicar_em_utc": quando.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "rotulo": f"{NOMES_DIA[d.weekday()]} {d.strftime('%d/%m')} {hh:02d}h{mm:02d}"})
    return out


# ---------------------------------------------------------------- mensagens
def registrar_msgs(ids: list[int], pasta: Path, tipo: str, **extra) -> None:
    for i in ids:
        _gravar(MSG / f"{i}.json", {"pasta": rel(pasta), "tipo": tipo, **extra})


def msg_info(message_id: int) -> dict | None:
    return _ler(MSG / f"{message_id}.json")


# ---------------------------------------------------------------- áudios
def registrar_audio(pasta: Path, bloco: int, file_id: str, message_id: int, duracao: int) -> None:
    _gravar(pasta / "audio" / f"bloco_{bloco:02d}.json",
            {"file_id": file_id, "message_id": message_id, "duracao": duracao,
             "recebido_em": datetime.now(timezone.utc).isoformat(timespec="seconds")})


def blocos_com_audio(pasta: Path) -> set[int]:
    return {int(p.stem.split("_")[1]) for p in (pasta / "audio").glob("bloco_*.json")}


def total_blocos(pasta: Path) -> int:
    prod = _ler(pasta / "producao.json", {})
    return len(prod.get("blocos", []))


def config_geral() -> dict:
    return yaml.safe_load((RAIZ / "pipeline" / "config" / "geral.yaml").read_text(encoding="utf-8"))
