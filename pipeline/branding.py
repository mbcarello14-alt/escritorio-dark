"""Aplica a descrição, as palavras-chave e o banner do canal pela API do YouTube.

Uso: python -m pipeline.branding vestibular
(A foto de perfil não tem API: essa é trocada no YouTube Studio › Personalização › Branding.)
"""
from __future__ import annotations

import sys

from .comum import ASSETS, carregar_config, log
from .youtube import servico


def aplicar(canal: str) -> None:
    cfg = carregar_config(canal)
    marca = cfg.get("canal_youtube") or {}
    yt = servico(cfg["segredo_youtube"])
    item = yt.channels().list(part="brandingSettings,snippet", mine=True).execute()["items"][0]
    log.info("canal: %s (%s)", item["snippet"]["title"], item["id"])
    b = item.get("brandingSettings", {})
    ch = b.setdefault("channel", {})
    if marca.get("descricao"):
        ch["description"] = marca["descricao"].strip()
    if marca.get("palavras_chave"):
        ch["keywords"] = " ".join(f'"{p}"' if " " in p else p for p in marca["palavras_chave"])
    ch["country"] = "BR"
    ch["defaultLanguage"] = "pt"
    banner = ASSETS / canal / "banner.png"
    if banner.exists():
        from googleapiclient.http import MediaFileUpload
        url = yt.channelBanners().insert(media_body=MediaFileUpload(str(banner), mimetype="image/png")).execute()["url"]
        b.setdefault("image", {})["bannerExternalUrl"] = url
        log.info("banner enviado")
    yt.channels().update(part="brandingSettings", body={"id": item["id"], "brandingSettings": b}).execute()
    log.info("descrição e branding aplicados em %s", item["snippet"]["title"])


if __name__ == "__main__":
    for c in sys.argv[1:]:
        aplicar(c)
