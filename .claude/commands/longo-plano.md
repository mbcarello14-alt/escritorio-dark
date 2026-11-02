---
description: Planeja os capítulos de um vídeo longo (2h30 para dormir ou revisão de 1h–1h30)
argument-hint: <pasta>
---

Pasta do vídeo longo: $ARGUMENTS

Leia o `estado.json` (campos `canal`, `tema`, `ajustes`). Chame o roteirista de longos **do canal**: `roteirista-longo-historia`, `roteirista-longo-livros` ou `roteirista-longo-vestibular`. Ele faz a etapa 1 e escreve `plano.json`.

Confira você mesmo: o número de capítulos bate com `longos.blocos` do config do canal, o tema está no nicho do canal (Ouro & Império = narrativa e curiosidades, nunca ENEM; Mapeado = o que cai na prova, nunca "aprenda dormindo"; Marca-Página = 4 ou 5 livros), e o `titulo_youtube` tem até 100 caracteres. Rode `python -m pipeline.longo validar $ARGUMENTS` e ignore só os erros sobre blocos (ainda não existem).
