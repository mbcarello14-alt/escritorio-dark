---
description: Gera 3 pautas ranqueadas para cada pasta de vídeo informada
argument-hint: <pasta> [<pasta> ...]
---

Pastas de vídeo: $ARGUMENTS

Para **cada** pasta, em paralelo, chame o subagente `pesquisador-pauta` (etapa 1) passando:
- o canal (campo `canal` do `estado.json` da pasta) e o caminho da pasta;
- a `nota_miguel` do `estado.json`, se existir (é o pedido do Miguel e tem prioridade);
- o dia de publicação (`rotulo`), para considerar datas comemorativas, sazonalidade (ENEM, vestibulares) e notícias da semana.

O subagente deve escrever na pasta:
1. `01-pauta.md` — a análise completa das 3 ideias.
2. `pautas.json` — exatamente neste formato (3 itens, já ranqueados):
```json
[{"titulo": "até 60 caracteres", "angulo": "o ângulo próprio do canal em 1 frase", "porque": "prova de demanda/lacuna em 1 frase curta"}]
```

Antes de terminar, confira que todas as pastas têm `pautas.json` válido (JSON com 3 itens). Não edite mais nada.
