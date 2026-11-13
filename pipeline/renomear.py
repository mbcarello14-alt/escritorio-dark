"""Troca o título de vídeos já agendados/publicados (lista em canais/renomear.json) e registra no repositório.

[{"pasta": "canais/historia/videos/2026-11-13", "titulo": "Novo título"}]
"""
from __future__ import annotations

import json

from .comum import RAIZ, carregar_config, log
from .youtube import servico


def main() -> None:
    arq = RAIZ / "canais" / "renomear.json"
    for item in json.loads(arq.read_text(encoding="utf-8")):
        pasta = RAIZ / item["pasta"]
        pub = json.loads((pasta / "publicacao.json").read_text(encoding="utf-8"))
        est = json.loads((pasta / "estado.json").read_text(encoding="utf-8"))
        yt = servico(carregar_config(est["canal"])["segredo_youtube"])
        sn = yt.videos().list(part="snippet", id=pub["video_id"]).execute()["items"][0]["snippet"]
        antigo, novo = sn["title"], item["titulo"].strip()[:100]
        yt.videos().update(part="snippet", body={"id": pub["video_id"], "snippet": {
            "title": novo, "categoryId": sn["categoryId"], "description": sn.get("description", ""), "tags": sn.get("tags", []),
            "defaultLanguage": sn.get("defaultLanguage", "pt-BR"), "defaultAudioLanguage": sn.get("defaultAudioLanguage", "pt-BR")}}).execute()
        pub["titulo"] = novo
        (pasta / "publicacao.json").write_text(json.dumps(pub, ensure_ascii=False, indent=2), encoding="utf-8")
        est["titulo"] = novo
        (pasta / "estado.json").write_text(json.dumps(est, ensure_ascii=False, indent=2), encoding="utf-8")
        log.info("título trocado: '%s' → '%s'", antigo, novo)
        print(f"✅ {antigo}  →  {novo}")
    arq.unlink()


if __name__ == "__main__":
    main()
