"""Escolhe o próximo horário livre de publicação de cada canal."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from .comum import RAIZ

BRT = ZoneInfo("America/Sao_Paulo")
DIAS = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}


def _ocupados(canal: str) -> set[str]:
    out = set()
    for p in (RAIZ / "canais" / canal / "videos").glob("*/publicacao.json"):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            if d.get("publicar_em_utc"):
                out.add(d["publicar_em_utc"])
        except Exception:
            pass
    return out


def proximo_horario(cfg: dict, agora: datetime | None = None, folga_horas: float = 4) -> str:
    """Próximo horário da grade `youtube.publicar` (BRT) com ao menos `folga_horas` de antecedência."""
    agora = (agora or datetime.now(timezone.utc)).astimezone(BRT)
    minimo = agora + timedelta(hours=folga_horas)
    ocupados = _ocupados(cfg["canal"])
    grade = []
    for item in cfg["youtube"]["publicar"]:
        dia, hora = item.split()
        h, m = map(int, hora.split(":"))
        grade.append((DIAS[dia.lower()[:3]], h, m))
    for dias in range(0, 60):
        data = (agora + timedelta(days=dias)).date()
        for wd, h, m in sorted(grade, key=lambda g: (g[1], g[2])):
            if data.weekday() != wd:
                continue
            quando = datetime(data.year, data.month, data.day, h, m, tzinfo=BRT)
            iso = quando.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            if quando >= minimo and iso not in ocupados:
                return iso
    raise RuntimeError("Não achei horário livre nos próximos 60 dias")
