---
description: Transforma o roteiro aprovado no producao.json que o motor renderiza sozinho
argument-hint: <pasta>
---

Pasta do vídeo: $ARGUMENTS

O roteiro foi **aprovado** pelo Miguel. Monte o `producao.json` seguindo `pipeline/CONTRATO.md` à risca.

1. Chame em paralelo:
   - `diretor-visual` → divide cada bloco do `roteiro.json` em cenas e escolhe o visual de cada uma (`06-storyboard.md` + a lista de blocos/cenas).
   - `seo-embalagem` → título, descrição (com fontes do dossiê), tags, hashtags (`09-seo.md`).
   - `thumbnail` → texto, `cena`/`imagem_busca` e layout da thumbnail (`09-thumbnail.md`).
2. Junte tudo em `producao.json`.

Regras que o motor exige:
- `blocos` = os mesmos blocos do `roteiro.json`, na mesma ordem e com o mesmo `capitulo`. Cada bloco vira **um áudio** gravado pelo Miguel.
- Dentro de um bloco, a concatenação das `narracao` das cenas deve ser **idêntica** ao `texto` do bloco (só dividida). Não reescreva nada.
- `canal` = campo `canal` do `estado.json`.

Valide e corrija até passar:
```
python -m pipeline.validar $ARGUMENTS
```
Por fim, atualize `titulo` no `estado.json` com o título final.
