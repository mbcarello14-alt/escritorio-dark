---
description: Aplica o pedido do Miguel num reel chamativo já feito
argument-hint: <pasta>
---

Pasta do reel: $ARGUMENTS

O último item de `ajustes` no `estado.json` é o pedido do Miguel. Chame o agente do canal (`reels-historia`, `reels-vestibular` ou `reels-livros`, conforme o `canal`) para aplicar o pedido no `reel.json`, sem mudar o que não foi pedido. Se o pedido mexer em fatos, ele confere a fonte. Depois rode `python -m pipeline.reel validar $ARGUMENTS` e corrija até passar.
