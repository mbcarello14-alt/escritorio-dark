"""Recupera o registro de um vídeo que subiu para o YouTube mas não foi salvo no projeto.

Uso: python -m pipeline.reparar canais/historia/videos/2026-10-26
Procura nos envios recentes do canal um vídeo com o mesmo título do producao.json.
"""
import json
import sys
from pathlib import Path

from . import estado as E
from .comum import RAIZ, carregar_config
from .youtube import servico


def main():
    pasta = RAIZ / sys.argv[1]
    prod = json.loads((pasta / "producao.json").read_text(encoding="utf-8"))
    cfg = carregar_config(prod["canal"])
    yt = servico(cfg["segredo_youtube"])
    uploads = yt.channels().list(part="contentDetails", mine=True).execute()["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    itens = yt.playlistItems().list(part="snippet,contentDetails", playlistId=uploads, maxResults=25).execute()["items"]
    achados = [i for i in itens if i["snippet"]["title"].strip() == prod["titulo"].strip()]
    print(f"{len(achados)} vídeo(s) com esse título no canal")
    if not achados:
        raise SystemExit("não achei o vídeo no canal")
    ids = [a["contentDetails"]["videoId"] for a in achados]
    st = yt.videos().list(part="status,contentDetails", id=",".join(ids)).execute()["items"]
    for v in st:
        print(v["id"], v["status"].get("privacyStatus"), v["status"].get("publishAt"), v["contentDetails"].get("duration"))
    v = st[0]
    pub = {"titulo": prod["titulo"], "video_id": v["id"], "url": f"https://youtu.be/{v['id']}",
           "publicar_em_utc": v["status"].get("publishAt") or E.ler_estado(pasta).get("publicar_em_utc"),
           "duracao_s": 0, "cenas": sum(len(b["cenas"]) for b in prod["blocos"]), "recuperado": True,
           "duplicados": ids[1:]}
    (pasta / "publicacao.json").write_text(json.dumps(pub, ensure_ascii=False, indent=2), encoding="utf-8")
    E.salvar_estado(pasta, etapa="agendado", url=pub["url"], titulo=prod["titulo"])
    print("registro recuperado:", pub["url"])


if __name__ == "__main__":
    main()
