"""Cliente mínimo da API de bots do Telegram."""
from __future__ import annotations

import os
from pathlib import Path

import requests

from .comum import log

LIMITE = 4000  # o Telegram aceita 4096 caracteres por mensagem


def _token() -> str:
    t = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not t:
        raise SystemExit("Segredo TELEGRAM_BOT_TOKEN não configurado.")
    return t


def chat_id() -> str:
    c = os.environ.get("TELEGRAM_CHAT_ID")
    if not c:
        raise SystemExit("Segredo TELEGRAM_CHAT_ID não configurado.")
    return c


def _api(metodo: str, **dados):
    r = requests.post(f"https://api.telegram.org/bot{_token()}/{metodo}", timeout=120, **dados)
    j = r.json()
    if not j.get("ok"):
        raise RuntimeError(f"Telegram {metodo}: {j.get('description')}")
    return j["result"]


def _partes(texto: str) -> list[str]:
    if len(texto) <= LIMITE:
        return [texto]
    partes, atual = [], ""
    for par in texto.split("\n\n"):
        if len(atual) + len(par) + 2 > LIMITE and atual:
            partes.append(atual)
            atual = ""
        while len(par) > LIMITE:
            partes.append(par[:LIMITE])
            par = par[LIMITE:]
        atual = f"{atual}\n\n{par}" if atual else par
    if atual:
        partes.append(atual)
    return partes


def enviar(texto: str, responder_a: int | None = None, html: bool = True) -> list[int]:
    """Envia (dividindo se for longo). Devolve os message_id enviados."""
    ids = []
    for i, p in enumerate(_partes(texto)):
        dados = {"chat_id": chat_id(), "text": p, "disable_web_page_preview": True}
        if html:
            dados["parse_mode"] = "HTML"
        if responder_a and i == 0:
            dados["reply_parameters"] = {"message_id": responder_a, "allow_sending_without_reply": True}
        try:
            ids.append(_api("sendMessage", json=dados)["message_id"])
        except RuntimeError as e:
            if html and "parse" in str(e).lower():
                dados.pop("parse_mode")
                ids.append(_api("sendMessage", json=dados)["message_id"])
            else:
                raise
    return ids


def enviar_foto(caminho: Path, legenda: str = "") -> int:
    with open(caminho, "rb") as f:
        return _api("sendPhoto", data={"chat_id": chat_id(), "caption": legenda[:1000], "parse_mode": "HTML"},
                    files={"photo": f})["message_id"]


def enviar_arquivo(caminho: Path, legenda: str = "") -> int:
    with open(caminho, "rb") as f:
        return _api("sendDocument", data={"chat_id": chat_id(), "caption": legenda[:1000], "parse_mode": "HTML"},
                    files={"document": f})["message_id"]


def enviar_audio(caminho: Path, legenda: str = "", titulo: str = "") -> int:
    with open(caminho, "rb") as f:
        return _api("sendAudio", data={"chat_id": chat_id(), "caption": legenda[:1000], "parse_mode": "HTML",
                                       "title": titulo or caminho.stem, "performer": "Escritório Dark"},
                    files={"audio": (caminho.name, f, "audio/mpeg")})["message_id"]


def baixar(file_id: str, destino: Path) -> Path:
    info = _api("getFile", json={"file_id": file_id})
    r = requests.get(f"https://api.telegram.org/file/bot{_token()}/{info['file_path']}", timeout=300)
    r.raise_for_status()
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(r.content)
    log.info("baixado %s (%d KB)", destino.name, len(r.content) // 1024)
    return destino


def reagir(message_id: int, emoji: str = "👍") -> None:
    try:
        _api("setMessageReaction", json={"chat_id": chat_id(), "message_id": message_id,
                                         "reaction": [{"type": "emoji", "emoji": emoji}]})
    except Exception as e:
        log.warning("reação falhou: %s", e)


def esc(t: str) -> str:
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
