---
description: Cria o reel.json dos reels chamativos 3D (um por pasta)
argument-hint: <pasta> [<pasta> ...]
---

Pastas de reel: $ARGUMENTS

Para **cada** pasta, em paralelo, chame o agente do canal da pasta (campo `canal` do `estado.json`): `reels-historia`, `reels-vestibular` ou `reels-livros`. Nunca use o de outro canal. Ele escreve `reel.json` e `01-fontes.md` na pasta.

Antes de terminar, rode `python -m pipeline.reel validar <pasta>` para cada pasta e corrija o que falhar. Confira também que cada reel está no nicho do canal (Ouro & Império sem ENEM/vestibular; Mapeado é conceito de prova; Marca-Página é sobre um livro).
