"""Confere a configuração (segredos, Telegram, YouTube, Higgsfield) e manda o resultado no Telegram.

Rodado pelo workflow "Diagnóstico". Nunca imprime o valor de nenhum segredo.
"""
from __future__ import annotations

import os

import requests

from .comum import carregar_config

SEGREDOS = {
    "CLAUDE_CODE_OAUTH_TOKEN": "Claude Code (agentes)",
    "TELEGRAM_BOT_TOKEN": "bot do Telegram",
    "TELEGRAM_CHAT_ID": "seu chat no Telegram",
    "YT_CLIENT_ID": "app do YouTube (Google Cloud)",
    "YT_CLIENT_SECRET": "app do YouTube (Google Cloud)",
    "YT_REFRESH_HISTORIA": "acesso ao canal Ouro & Império",
    "YT_REFRESH_VESTIBULAR": "acesso ao canal Mapeado",
    "YT_REFRESH_LIVROS": "acesso ao canal Marca-Página",
    "GOOGLE_TTS_API_KEY": "narrador de IA do Google",
    "HF_API_KEY_ID": "Higgsfield (opcional)",
    "HF_API_KEY_SECRET": "Higgsfield (opcional)",
    "CLOUDFLARE_API_TOKEN": "Cloudflare (recepção instantânea do Telegram)",
    "GH_PAT": "token do GitHub para o Cloudflare",
}


def main():
    linhas = ["🩺 <b>Diagnóstico do escritório</b>\n"]
    for nome, desc in SEGREDOS.items():
        ok = bool((os.environ.get(nome) or "").strip())
        linhas.append(f"{'✅' if ok else '❌'} {desc} <code>{nome}</code>")

    linhas.append("")
    for canal in ("historia", "vestibular", "livros"):
        cfg = carregar_config(canal)
        if not cfg.get("ativo", True):
            linhas.append(f"⏸️ YouTube {cfg['nome']}: em pausa")
            continue
        try:
            from .youtube import servico
            r = servico(cfg["segredo_youtube"]).channels().list(part="snippet,statistics", mine=True).execute()
            item = r["items"][0]
            nome = item["snippet"]["title"]
            alerta = "" if nome.lower().replace("&", "e")[:4] == cfg["nome"].lower().replace("&", "e")[:4] else \
                " ⚠️ nome diferente — autorizou o canal certo?"
            linhas.append(f"✅ YouTube {cfg['nome']} → canal <b>{nome}</b> ({item['statistics'].get('subscriberCount', '?')} inscritos){alerta}")
        except BaseException as e:  # SystemExit incluso
            linhas.append(f"❌ YouTube {cfg['nome']}: {str(e)[:160]}")

    if os.environ.get("HF_API_KEY_ID") and os.environ.get("HF_API_KEY_SECRET"):
        try:
            r = requests.get("https://api.higgsfield.ai/requests/00000000-0000-0000-0000-000000000000/status",
                             headers={"Authorization": f"Key {os.environ['HF_API_KEY_ID']}:{os.environ['HF_API_KEY_SECRET']}"},
                             timeout=30)
            linhas.append("❌ Higgsfield: chave recusada" if r.status_code in (401, 403) else "✅ Higgsfield: chave aceita")
        except Exception as e:
            linhas.append(f"⚠️ Higgsfield: não consegui testar ({e})")
    else:
        linhas.append("➖ Higgsfield desligado: os vídeos usam só imagens livres")

    texto = "\n".join(linhas)
    resumo = os.environ.get("GITHUB_STEP_SUMMARY")
    if resumo:
        with open(resumo, "a", encoding="utf-8") as f:
            f.write(texto.replace("<b>", "**").replace("</b>", "**").replace("<code>", "`").replace("</code>", "`") + "\n")
    print(texto)
    if os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID"):
        from . import telegram
        telegram.enviar(texto)


if __name__ == "__main__":
    main()
