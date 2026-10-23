---
description: Rodada do gestor de tráfego orgânico (comentários, títulos fracos, leitura do jogo)
---

Os dados já foram coletados em `canais/trafego/resumo.json` e `canais/trafego/pendentes.json`.

Chame o `gestor-trafego` para escrever `canais/trafego/acoes.json`. Depois confira:
- o JSON é válido e segue o formato do agente;
- cada `comentario_id` de `respostas` e `ignorar` existe em `pendentes.json`;
- nenhuma resposta dá conselho de saúde, finanças, direito ou política como especialista, nem promete algo;
- títulos novos têm até 100 caracteres e são honestos com o vídeo.
Não aplique nada você mesmo: o motor (`python -m pipeline.trafego aplicar`) faz isso.
