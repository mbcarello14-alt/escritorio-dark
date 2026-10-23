"""Upload agendado e configuração do vídeo pela API oficial do YouTube."""
from __future__ import annotations

import json
import os
import time

from .comum import log

ESCOPOS = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]


def _do_repositorio(nome_segredo: str) -> str:
    """Acesso salvo pelo link "Autorizar canal" do worker: canais/credenciais/<canal>.json, criptografado."""
    import base64
    import hashlib
    from pathlib import Path
    canal = nome_segredo.replace("YT_REFRESH_", "").lower()
    arq = Path(__file__).resolve().parent.parent / "canais" / "credenciais" / f"{canal}.json"
    pat = os.environ.get("GH_PAT", "")
    if not (arq.exists() and pat):
        return ""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    d = json.loads(arq.read_text(encoding="utf-8"))
    chave = hashlib.sha256(f"{pat}:youtube".encode()).digest()
    return AESGCM(chave).decrypt(base64.b64decode(d["iv"]), base64.b64decode(d["dado"]), None).decode()


def credenciais(nome_segredo: str):
    """Aceita o refresh token puro (com YT_CLIENT_ID/YT_CLIENT_SECRET) ou o JSON do autorizar_youtube.py."""
    from google.oauth2.credentials import Credentials

    bruto = (os.environ.get(nome_segredo) or "").strip() or _do_repositorio(nome_segredo)
    if not bruto:
        raise SystemExit(f"Segredo {nome_segredo} não encontrado. Veja SETUP.md, passo do YouTube.")
    if bruto.startswith("{"):
        d = json.loads(bruto)
    else:
        d = {"refresh_token": bruto, "client_id": os.environ.get("YT_CLIENT_ID", "").strip(),
             "client_secret": os.environ.get("YT_CLIENT_SECRET", "").strip()}
        if not d["client_id"] or not d["client_secret"]:
            raise SystemExit("Faltam os segredos YT_CLIENT_ID e YT_CLIENT_SECRET.")
    return Credentials(token=None, refresh_token=d["refresh_token"], client_id=d["client_id"],
                       client_secret=d["client_secret"], token_uri="https://oauth2.googleapis.com/token",
                       scopes=ESCOPOS)


def servico(nome_segredo: str, api="youtube", versao="v3"):
    from googleapiclient.discovery import build
    return build(api, versao, credentials=credenciais(nome_segredo), cache_discovery=False)


def _enviar(req):
    from googleapiclient.errors import HttpError
    resposta, tentativas = None, 0
    while resposta is None:
        try:
            status, resposta = req.next_chunk()
            if status:
                log.info("upload %d%%", int(status.progress() * 100))
        except HttpError as e:
            if e.resp.status in (500, 502, 503, 504) and tentativas < 8:
                tentativas += 1
                time.sleep(2 ** tentativas)
                continue
            raise
        except (ConnectionError, TimeoutError, OSError):
            if tentativas >= 8:
                raise
            tentativas += 1
            time.sleep(2 ** tentativas)
    return resposta


def publicar(cfg: dict, pub: dict, video, thumb, srt) -> str:
    """Envia o vídeo como privado com publicação agendada. Devolve o ID do vídeo."""
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload

    yt = servico(cfg["segredo_youtube"])
    corpo = {
        "snippet": {
            "title": pub["titulo"][:100],
            "description": pub["descricao"][:5000],
            "tags": pub.get("tags", []),
            "categoryId": cfg["youtube"]["categoria_id"],
            "defaultLanguage": cfg["youtube"]["idioma"],
            "defaultAudioLanguage": cfg["youtube"]["idioma"],
        },
        "status": {
            "privacyStatus": "private",
            "publishAt": pub["publicar_em_utc"],
            "selfDeclaredMadeForKids": bool(cfg["youtube"].get("feito_para_criancas", False)),
            "containsSyntheticMedia": bool(pub.get("sintetico_realista", False)),
        },
    }
    media = MediaFileUpload(str(video), mimetype="video/mp4", chunksize=16 * 1024 * 1024, resumable=True)
    try:
        r = _enviar(yt.videos().insert(part="snippet,status", body=corpo, media_body=media))
    except HttpError as e:
        if "containsSyntheticMedia" not in str(e):
            raise
        log.warning("API recusou o campo de mídia sintética; enviando sem ele (marque no Studio se precisar)")
        corpo["status"].pop("containsSyntheticMedia")
        media = MediaFileUpload(str(video), mimetype="video/mp4", chunksize=16 * 1024 * 1024, resumable=True)
        r = _enviar(yt.videos().insert(part="snippet,status", body=corpo, media_body=media))
    vid = r["id"]
    log.info("vídeo enviado: https://youtu.be/%s (agendado para %s)", vid, pub["publicar_em_utc"])

    avisos = []
    try:
        yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(str(thumb), mimetype="image/jpeg")).execute()
    except HttpError as e:
        avisos.append(f"thumbnail não aplicada ({e.resp.status}). Verifique o canal por telefone em youtube.com/verify")
    try:
        yt.captions().insert(part="snippet", body={"snippet": {"videoId": vid, "language": "pt-BR", "name": "Português"}},
                             media_body=MediaFileUpload(str(srt), mimetype="application/octet-stream")).execute()
    except HttpError as e:
        avisos.append(f"legendas não enviadas ({e.resp.status})")
    if pub.get("playlist"):
        try:
            yt.playlistItems().insert(part="snippet", body={"snippet": {
                "playlistId": pub["playlist"], "resourceId": {"kind": "youtube#video", "videoId": vid}}}).execute()
        except HttpError as e:
            avisos.append(f"não entrou na playlist ({e.resp.status})")
    for a in avisos:
        log.warning(a)
    pub["avisos"] = avisos
    return vid
