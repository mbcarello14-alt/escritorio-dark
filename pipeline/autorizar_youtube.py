"""Autorização ÚNICA de cada canal (rode no seu computador, uma vez por canal).

1. Baixe o client_secret.json do Google Cloud (veja SETUP.md) para esta pasta.
2. Rode:  python pipeline/autorizar_youtube.py
3. Faça login e, na tela de escolha, selecione O CANAL certo (Ouro & Império, Mapeado ou Marca-Página).
4. Copie o texto que aparecer e cole como segredo no GitHub (YT_TOKEN_HISTORIA, YT_TOKEN_VESTIBULAR ou YT_TOKEN_LIVROS).
"""
import json
import sys
from pathlib import Path

ESCOPOS = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]


def main():
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        sys.exit("Instale antes:  pip install google-auth-oauthlib google-api-python-client")
    segredo = Path(sys.argv[1] if len(sys.argv) > 1 else "client_secret.json")
    if not segredo.exists():
        sys.exit(f"Não achei {segredo}. Baixe o JSON do cliente OAuth no Google Cloud (SETUP.md, passo 3).")
    fluxo = InstalledAppFlow.from_client_secrets_file(str(segredo), ESCOPOS)
    cred = fluxo.run_local_server(port=0, prompt="consent", access_type="offline")

    from googleapiclient.discovery import build
    canal = build("youtube", "v3", credentials=cred).channels().list(part="snippet", mine=True).execute()
    nome = canal["items"][0]["snippet"]["title"] if canal.get("items") else "(nenhum canal)"
    print(f"\nAutorizado para o canal: {nome}\n")
    print("Cole o texto abaixo como segredo no GitHub (tudo, inclusive as chaves):\n")
    print(json.dumps({"client_id": cred.client_id, "client_secret": cred.client_secret,
                      "refresh_token": cred.refresh_token}))


if __name__ == "__main__":
    main()
