# Contrato `producao.json`

É o arquivo que os agentes escrevem depois do `/aprovar` e que o motor de produção lê para gerar o vídeo sozinho. Fica na pasta do vídeo (`canais/<canal>/videos/AAAA-MM-DD-slug/producao.json`). Valide sempre com:

```
python -m pipeline.validar canais/<canal>/videos/<pasta>
```

## Estrutura

```json
{
  "canal": "historia",
  "titulo": "Como o sal construiu o Império Romano",
  "descricao": "Duas primeiras linhas fortes...\n\nResumo...\n\nFontes:\n- ...",
  "tags": ["história", "roma antiga", "economia"],
  "hashtags": ["#história", "#roma", "#economia"],
  "playlist": "",
  "sintetico_realista": false,
  "musica_humor": "misterio",
  "thumbnail": {
    "texto": "PAGOS EM SAL",
    "imagem_busca": "Roman salt road ancient mosaic",
    "layout": "direita"
  },
  "blocos": [
    {
      "capitulo": "O tesouro branco",
      "cenas": [
        {
          "narracao": "Texto exatamente como deve ser falado, com números por extenso.",
          "visual": { "tipo": "imagem", "busca": "Via Salaria Roman road", "movimento": "zoom_in" }
        }
      ]
    }
  ]
}
```

## Campos

- `titulo` (≤ 100 caracteres; ideal ≤ 60), `descricao` (≤ 5000), `tags` (total ≤ 450 caracteres).
- `sintetico_realista`: `true` se houver imagem ou voz sintética realista de pessoa, lugar ou evento real.
- `playlist`: **nome** da playlist (o motor cria se não existir e põe o vídeo nela).
- `comentario_inicial` (opcional): pergunta que o canal publica como primeiro comentário.
- Cortes verticais (Shorts e Reels) ficam em outro arquivo, `cortes.json`, escrito pelo `clipador`.
- `musica_humor`: nome de uma pasta em `musica/` (se não existir, o vídeo sai sem trilha).
- `thumbnail.texto`: até 4 palavras. `layout`: `esquerda`, `direita` ou `centro` (lado onde fica o texto).
- `blocos[].capitulo`: vira capítulo na descrição (os tempos são calculados sozinhos). O primeiro bloco é o gancho e o capítulo "0:00".
- `cenas[].narracao`: 1 a 3 frases (6 a 20 segundos). Cada cena é um plano do vídeo.

## Tipos de `visual`

| tipo | campos | uso |
|---|---|---|
| `imagem` | `busca` (em inglês funciona melhor), `movimento`: `zoom_in` \| `zoom_out` \| `pan_esquerda` \| `pan_direita`, `legenda` (opcional) | foto ou pintura de domínio público / licença livre |
| `cartao` | `titulo`, `subtitulo` (opcional) | data, nome, conceito em destaque |
| `numero` | `valor`, `rotulo` | um número grande ("30 mil", "1453") |
| `citacao` | `texto` (curto), `autor` | citação curta com crédito |
| `lista` | `titulo`, `itens` (2–5 itens curtos) | resumo em tópicos |
| `mapa_mental` | `mapa` (objeto abaixo), `revelar` (quantos ramos mostrar) | **Mapeado**: o mapa vai se construindo |
| `comparacao` | `esquerda`, `direita` (cada um `{titulo, itens}`) | antes × depois, A × B |
| `mapa_animado` | `regiao` + `paises`, `areas`, `cidades`, `rotas`, `rotulos`, `camera_para`, `titulo_inferior` | **só canais com `estilo.animado`** (Ouro & Império): mapa que se desenha — ver `pipeline/animacao/FORMATO.md` |
| `contador` | `ate`, `de`, `prefixo`, `sufixo`, `rotulo`, `comparacao` | **animado**: valor em dinheiro contando |
| `linha_tempo` | `eventos` (`{ano, texto}`), `foco` | **animado**: datas em sequência |
| `cena_animada` | `cenario` (lugar sem pessoas, inglês), `personagens` (figurino, x, acoes, fala…) | **animado**: bonecos que andam, gesticulam e falam — ver `pipeline/animacao/FORMATO.md` |

Em canais animados, `ilustracao` e `imagem` também aceitam `titulo_inferior`, `particulas`, `neblina` e `luzes` (ver `pipeline/animacao/FORMATO.md`).

### `mapa`
```json
{ "centro": "Revolução Industrial",
  "ramos": [
    { "rotulo": "Causas", "filhos": ["Capital acumulado", "Carvão e ferro"] },
    { "rotulo": "Consequências", "filhos": ["Urbanização", "Proletariado"] }
  ] }
```
Use o mesmo `mapa` em todas as cenas de mapa do vídeo, aumentando `revelar` (1, 2, 3...). A última cena com o mapa completo deve ter `revelar` = número de ramos. Até 6 ramos e 3 filhos por ramo.
