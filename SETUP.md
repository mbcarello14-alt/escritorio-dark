# Configuração única (~40 min)

Tudo abaixo é feito **uma vez**. Os valores secretos vão para o cofre do GitHub:
**repositório › Settings › Secrets and variables › Actions › New repository secret**.
Nunca cole tokens no chat nem em arquivos do repositório.

| Segredo | De onde vem |
|---|---|
| `TELEGRAM_BOT_TOKEN` | passo 1 |
| `TELEGRAM_CHAT_ID` | passo 4 |
| `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID` | passo 2 |
| `GH_PAT` | passo 3 |
| `CLAUDE_CODE_OAUTH_TOKEN` | passo 5 |
| `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_HISTORIA`, `YT_REFRESH_VESTIBULAR`, `YT_REFRESH_LIVROS` | passos 6 e 7 |
| `HF_API_KEY_ID`, `HF_API_KEY_SECRET` (opcional) | passo 8 |

## 1. Bot do Telegram
No Telegram, fale com **@BotFather** → `/newbot` → nome e usuário (terminado em `bot`). Salve o token como `TELEGRAM_BOT_TOKEN`.

## 2. Cloudflare (recepção instantânea, grátis)
1. Crie a conta em dash.cloudflare.com e abra **Workers & Pages** uma vez (cria o subdomínio `workers.dev`).
2. **Account ID:** na página inicial da conta, menu ⋯ ao lado do nome da conta › *Copy account ID* → `CLOUDFLARE_ACCOUNT_ID`.
3. **API token:** ícone de perfil › *My Profile* › *API Tokens* › *Create Token* › modelo **Edit Cloudflare Workers** › *Continue* › *Create* → `CLOUDFLARE_API_TOKEN`.

## 3. Token do GitHub para o Cloudflare
github.com › foto › *Settings* › *Developer settings* › *Personal access tokens* › **Fine-grained tokens** › *Generate new token*:
- Nome: `escritorio-dark-worker` · Expiração: 1 ano
- *Repository access*: **Only select repositories** → `escritorio-dark`
- *Permissions › Repository*: **Contents: Read and write** (Metadata: Read entra sozinho)

Salve como `GH_PAT`. Depois rode **Actions › Instalar bot › Run workflow**.

## 4. Seu chat
Mande `/start` para o seu bot. Ele responde com o número do chat → salve como `TELEGRAM_CHAT_ID` e rode **Instalar bot** de novo. Você recebe "Escritório Dark no ar!" com o link do escritório virtual.

## 5. Claude Code (os agentes)
No seu computador, no terminal (PowerShell): `claude setup-token`. Faça login, copie o token gerado → `CLAUDE_CODE_OAUTH_TOKEN`. Os agentes passam a usar a sua assinatura do Claude.

## 6. App do YouTube no Google Cloud
1. console.cloud.google.com → crie o projeto **escritorio-dark**.
2. *APIs e serviços › Biblioteca*: ative **YouTube Data API v3** e **YouTube Analytics API**.
3. *Tela de permissão OAuth* (Google Auth Platform): tipo **Externo**, nome `Escritório Dark`, seu e-mail. Em *Público-alvo*, clique **Publicar app** (em produção — em "teste" o acesso expira a cada 7 dias).
4. *Clientes › Criar cliente*: tipo **Aplicativo da Web**, em *URIs de redirecionamento autorizados* adicione `https://developers.google.com/oauthplayground`. Salve o **ID do cliente** → `YT_CLIENT_ID` e a **chave secreta** → `YT_CLIENT_SECRET`.

## 7. Autorizar cada canal (repita 3 vezes)
1. Abra developers.google.com/oauthplayground › engrenagem ⚙️ › marque **Use your own OAuth credentials** e cole o ID e a chave do passo 6.
2. Em *Input your own scopes*, cole:
   `https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.force-ssl https://www.googleapis.com/auth/yt-analytics.readonly`
3. **Authorize APIs** → entre com sua conta → **escolha o canal** (Ouro & Império, Mapeado ou Marca-Página) → na tela "app não verificado", *Avançado › Acessar Escritório Dark* → permita.
4. **Exchange authorization code for tokens** → copie o **Refresh token** → `YT_REFRESH_HISTORIA` (ou `_VESTIBULAR`, `_LIVROS`).
5. Para o próximo canal, clique na engrenagem de novo e repita (o Playground lembra as credenciais).

Antes, no YouTube Studio de cada canal, verifique o canal por telefone (youtube.com/verify) — sem isso a API não aplica thumbnails personalizadas nem vídeos com mais de 15 min.

## 8. Higgsfield (opcional)
console.higgsfield.ai → crie a conta de API, faça uma recarga (mínimo US$ 5) e gere uma chave. Salve o ID como `HF_API_KEY_ID` e o segredo como `HF_API_KEY_SECRET`. O teto de gasto fica em `pipeline/config/geral.yaml` (padrão: US$ 20/mês). Sem chave, os vídeos usam só imagens livres.

## 9. Conferir
**Actions › Diagnóstico › Run workflow.** O resultado chega no Telegram com ✅/❌ para cada item.

## 10. Primeiro vídeo
No Telegram, mande `/pauta vestibular` (ou espere domingo 10h). Escolha a pauta, aprove o roteiro, grave os blocos — e acompanhe no escritório virtual.

## Trilhas sonoras (opcional)
Baixe músicas da **Biblioteca de áudio do YouTube** (YouTube Studio › Biblioteca de áudio, filtre "Atribuição não necessária") e coloque em `musica/misterio/`, `musica/foco/` e `musica/calmo/`. Sem músicas, os vídeos saem só com a sua voz.
