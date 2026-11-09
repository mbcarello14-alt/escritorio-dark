# Escritório Dark 🎬

Um escritório de agentes de IA (Claude Code) que produz três canais do YouTube **sozinho** — você só escolhe a pauta, aprova o roteiro e grava a narração pelo Telegram.

| Canal | Estilo | Publica |
|---|---|---|
| **Ouro & Império** — histórias que mudaram o mundo | explicador bem-humorado, ilustrado | seg e sex 18h |
| **Mapeado** — o que mais cai, em mapas mentais | Draw My Life (quadro branco) | ter e qui 17h |
| **Marca-Página** — resumo + crítica de livros | explicador bem-humorado, ilustrado | qua 19h e sáb 11h |

## Como funciona
```
Domingo 10h / quarta 19h ─► pesquisador-pauta ─► 3 pautas no Telegram
você: "2, foca no imposto"  ─► pesquisador ─► roteirista ─► checador ─► guardião ─► roteiro no Telegram
você: "aprovar"             ─► diretor visual + SEO + thumbnail ─► blocos para gravar
você: 🎙️ um áudio por bloco ─► motor: limpa a voz, sincroniza, ilustra (Higgsfield), desenha,
                                renderiza, legenda e AGENDA no YouTube ─► link no Telegram
Todo dia                    ─► métricas; segunda ─► relatório do analista
```

## A equipe (`.claude/agents/`)
`pesquisador-pauta` · `roteirista` · `checador` · `guardiao-originalidade` · `diretor-visual` · `seo-embalagem` · `thumbnail` · `analista`
Os procedimentos de cada etapa estão em `.claude/commands/` (`/pautas`, `/roteiro`, `/ajustar`, `/producao`, `/relatorio`).

## Peças
- `pipeline/` — motor de produção (Python + FFmpeg) e o bot.
- `.github/workflows/` — Telegram, Pautas da semana, Produção, Rotina diária, Instalar bot, Diagnóstico.
- `worker/` — recepção instantânea do Telegram (Cloudflare, grátis) e o escritório virtual.
- `canais/` — briefings, histórico e uma pasta por vídeo.
- `assets/` — logos, banners, marcas d'água e fontes.

## Telegram
`/status` · `/lote` · `/pauta historia|vestibular|livros` · `/ajuda`. No dia a dia, só **responda** às mensagens.

## Mudar algo
Abra o Claude Code nesta pasta e peça ("muda o Mapeado para 18h", "cria um agente de Shorts"). Horários e estilos: `pipeline/config/*.yaml`. Gasto com Higgsfield: `pipeline/config/geral.yaml`.

Configuração inicial: **[SETUP.md](SETUP.md)**.
