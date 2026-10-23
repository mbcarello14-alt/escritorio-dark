---
description: Aplica os ajustes pedidos pelo Miguel no roteiro
argument-hint: <pasta>
---

Pasta do vídeo: $ARGUMENTS

O Miguel pediu mudanças no roteiro. O último item de `ajustes` no `estado.json` é o pedido atual (os anteriores já foram aplicados).

1. Chame o `roteirista` para aplicar o pedido em `03-roteiro.md` e `roteiro.json`, mantendo o formato do `roteiro.json` (veja `.claude/commands/roteiro.md`). O pedido do Miguel manda: ele é o dono da linha editorial.
2. Se o ajuste trouxe fatos novos, rode o `checador` só nos trechos alterados e corrija o que ele apontar.
3. Confira que as três chamadas de engajamento (começo, meio e final) continuam no roteiro.
4. Atualize `resumo_checagem` no `roteiro.json` e `titulo` no `estado.json`.
