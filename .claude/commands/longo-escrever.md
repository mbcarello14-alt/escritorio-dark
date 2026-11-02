---
description: Escreve e checa os próximos blocos de ~10 min de um vídeo longo
argument-hint: <pasta> [quantidade]
---

Argumentos: $ARGUMENTS (pasta e, opcional, quantos blocos escrever; padrão 3)

1. Leia `estado.json` e `plano.json`. Veja em `blocos/` quais `bloco_NN.json` já existem com `"checado": true`; os próximos a escrever são os números seguintes, na ordem do plano.
2. Chame o roteirista de longos **do canal** (`roteirista-longo-historia`, `roteirista-longo-livros` ou `roteirista-longo-vestibular`) para escrever esses blocos (etapa 2), um arquivo por bloco.
3. Para **cada** bloco novo, chame o `checador` para conferir os fatos do `texto` contra as `fontes` (e outras fontes sérias). Se ele pedir correção, volte ao roteirista com a lista (no máximo 2 voltas por bloco). Quando estiver certo, marque `"checado": true` no JSON do bloco e salve as observações do checador em `blocos/checagem_NN.md`.
4. Rode `python -m pipeline.longo validar <pasta>` e corrija o que for dos blocos novos.
Não escreva mais blocos do que o pedido: o limite existe para não estourar o plano do Claude.
