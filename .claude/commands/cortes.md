---
description: Escolhe os cortes verticais (Shorts e Reels) de um vídeo que já tem producao.json
argument-hint: <pasta>
---

Pasta do vídeo: $ARGUMENTS

Chame o `clipador` para ler o `producao.json` desta pasta e escrever `cortes.json` (2 ou 3 cortes, formato no próprio agente). Depois confira você mesmo, para cada corte, que `de` e `ate` apontam para cenas que existem e que a soma das palavras das `narracao` do trecho fica entre 60 e 140. Corrija o que estiver fora.
