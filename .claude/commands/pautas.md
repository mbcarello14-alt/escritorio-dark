---
description: Gera 3 pautas ranqueadas para cada pasta de vídeo informada
argument-hint: <pasta> [<pasta> ...]
---

Pastas de vídeo: $ARGUMENTS

Para **cada** pasta, em paralelo, chame o pesquisador **do canal da pasta** (campo `canal` do `estado.json`): `pesquisador-historia` (canal historia), `pesquisador-vestibular` (canal vestibular) ou `pesquisador-livros` (canal livros). Nunca use o pesquisador de outro canal. Passe para ele (etapa 1):
- o canal (campo `canal` do `estado.json` da pasta) e o caminho da pasta;
- a `nota_miguel` do `estado.json`, se existir (é o pedido do Miguel e tem prioridade);
- o dia de publicação (`rotulo`), para considerar datas comemorativas, sazonalidade (ENEM, vestibulares) e notícias da semana.

O subagente deve escrever na pasta:
1. `01-pauta.md` — a análise completa das 3 ideias.
2. `pautas.json` — exatamente neste formato (3 itens, já ranqueados):
```json
[{"titulo": "até 60 caracteres", "angulo": "o ângulo próprio do canal em 1 frase", "porque": "prova de demanda/lacuna em 1 frase curta"}]
```

Antes de terminar, confira que todas as pastas têm `pautas.json` válido (JSON com 3 itens) e que **cada ideia é do nicho do canal**: nada de ENEM/vestibular no Ouro & Império, nada de história de entretenimento no Mapeado (e no Mapeado, as 3 ideias de matérias diferentes), só livros no Marca-Página. Ideia fora do nicho volta ao pesquisador. Não edite mais nada.
