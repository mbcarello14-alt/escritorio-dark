---
description: Pesquisa, escreve, checa e revisa o roteiro da pauta escolhida
argument-hint: <pasta>
---

Pasta do vídeo: $ARGUMENTS

Leia `estado.json` (campos `canal`, `ideia`, `nota_miguel`) e `pautas.json`/`01-pauta.md`. A pauta escolhida é a de número `ideia`. A `nota_miguel` é a opinião/ângulo do Miguel: ela **tem que aparecer no roteiro**.

Rode as etapas em sequência, sempre com os subagentes:
1. `pesquisador-pauta` → `02-dossie.md` (etapa 2).
2. `roteirista` → `03-roteiro.md` **e** `roteiro.json`.
3. `checador` → `04-checagem.md`. Se `CORRIGIR`, volte ao `roteirista` com a lista (no máximo 2 voltas).
4. `guardiao-originalidade` → `05-originalidade.md`. Se 🟡 ou 🔴, aplique as mudanças de maior impacto via `roteirista` (1 volta).
5. Confira você mesmo as **três chamadas de engajamento** (inscrição + like no bloco 1, pergunta para os comentários perto da metade, inscrição + like + comentário no último bloco). Faltou alguma → volte ao `roteirista`.

No fim, `roteiro.json` precisa estar assim (o texto dos blocos é EXATAMENTE o que o Miguel vai ler):
```json
{
  "titulo_provisorio": "...",
  "tese": "1 frase",
  "blocos": [{"capitulo": "nome curto", "texto": "texto corrido para gravar"}],
  "resumo_checagem": "1 frase: quantas afirmações, quantas corrigidas",
  "semaforo": "🟢|🟡|🔴",
  "resumo_originalidade": "1 frase",
  "pergunta_para_miguel": "1 pergunta opcional cuja resposta (opinião dele) deixaria o vídeo mais autoral"
}
```
Atualize `estado.json` com `"titulo": titulo_provisorio`. Não crie `producao.json` agora.
