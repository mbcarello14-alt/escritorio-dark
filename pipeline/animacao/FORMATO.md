# Cenas animadas em código (canais com `estilo.animado: true` — hoje o Ouro & Império)

Estilo de referência: documentário animado (mapas de papel antigo com mar azul, marcadores laranja que brilham,
rotas tracejadas que se desenham, títulos grandes com linha dourada, grão de papel). Tudo é desenhado por
`cena.html` quadro a quadro; o motor põe os efeitos sonoros sozinho (whoosh na entrada, "pop" nos marcadores,
"cha-ching" no contador, batida grave no título).

**Tempos:** todo campo `em` é a **fração da cena** (0 = começo, 1 = fim) em que o item aparece. Pode omitir:
os itens entram escalonados sozinhos, na ordem da lista. Use `em` para casar com a palavra da narração
(ex.: a cidade citada no fim da frase → `"em": 0.7`).

## `mapa_animado`
```json
{ "tipo": "mapa_animado",
  "regiao": "mediterraneo",                 // nome pronto ou [lon_min, lat_min, lon_max, lat_max]
  "camera_para": "italia",                  // opcional: a câmera viaja até aqui (zoom)
  "camera_em": 0.4,                         // opcional: quando a câmera começa (fração)
  "paises": [ { "nomes": ["Itália"], "cor": "ouro", "rotulo": "Roma", "em": 0.1 } ],
  "areas":  [ { "pontos": [[-9,36],[3,51],[29,46],[36,30],[10,32]], "cor": "vermelho", "rotulo": "Império Romano" } ],
  "cidades": [ { "nome": "Alexandria", "lon": 29.9, "lat": 31.2, "destaque": true, "lado": "esquerda" } ],
  "rotas":  [ { "pontos": [[29.9,31.2],[22,34.5],[12.3,41.7]], "carga": "navio" } ],
  "rotulos": [ { "texto": "Mar Mediterrâneo", "lon": 18, "lat": 34.2, "tipo": "mar" },
               { "texto": "trigo do Egito", "lon": 31, "lat": 28.5, "tipo": "destaque" } ],
  "titulo_inferior": { "titulo": "Roma, 100 d.C.", "subtitulo": "O império que vivia de trigo" } }
```
- **Regiões prontas:** mundo, europa, mediterraneo, oriente_medio, america_sul, brasil, america_norte, asia, africa,
  china, india, atlantico, escandinavia, caribe, italia, iberia, gra_bretanha, egito, grecia, rota_seda, indico, japao.
- **paises:** fronteiras de HOJE (Natural Earth). Nomes em português comum ("Itália", "Reino Unido", "Pérsia" = Irã)
  ou em inglês do Natural Earth ("Italy"). Servem para "onde fica hoje". **Para impérios e reinos antigos use `areas`**
  (polígono aproximado em [lon, lat], 5 a 15 pontos; o motor recorta no litoral sozinho e a área cresce do centro).
- **cores:** ouro, cinza, vermelho, verde, azul, roxo, laranja, marrom (ou um rgba). Cinza = ocupado/inimigo,
  ouro = o protagonista do vídeo, vermelho/azul = dois lados de uma disputa.
- **cidades:** ponto preto com nome; `destaque: true` = brilho laranja pulsando (a cidade de que a narração fala).
  `lado: "esquerda"` põe o nome à esquerda (cidade perto da borda direita).
- **rotas:** linha tracejada que se desenha; `carga`: navio, moeda, caravana (ou nada = seta no fim).
  `duracao` (fração, padrão 0.4) = quanto tempo leva para desenhar.
- **rotulos:** `tipo`: pais (grande, padrão), mar (espaçado, azul-claro), destaque (laranja, curto: o recurso/fato).
- **Continuidade:** como o mapa mental do Mapeado, repita o MESMO mapa em cenas seguidas acrescentando itens
  (cena 1: só a região; cena 2: + a cidade; cena 3: + a rota). Fica parecendo um mapa só que vai se construindo.

## `contador`
```json
{ "tipo": "contador", "de": 0, "ate": 300000000, "prefixo": "", "sufixo": " denários",
  "rotulo": "O custo do exército por ano", "comparacao": "≈ metade de tudo que Roma arrecadava" }
```
O número conta subindo, dá um pulso e um brilho ao terminar, com moedas caindo ao fundo. `casas` (opcional) = casas decimais.

## `linha_tempo`
```json
{ "tipo": "linha_tempo", "foco": 2,
  "eventos": [ { "ano": "27 a.C.", "texto": "Augusto vira imperador" }, { "ano": "64", "texto": "O grande incêndio" },
               { "ano": "301", "texto": "Diocleciano tabela os preços" } ] }
```
Mostra os eventos até o `foco`, e a câmera desliza do anterior para o foco. Repita a mesma lista nas cenas seguintes
aumentando `foco` (0, 1, 2…) — a linha vai andando com a narração.

## Extras em `ilustracao` e `imagem` (a imagem ganha vida)
Qualquer `ilustracao`/`imagem` aceita, junto com os campos normais:
- `titulo_inferior`: `{ "titulo": "Winston Churchill", "subtitulo": "As memórias da guerra · 1949" }` — o título grande
  com linha dourada (apresentar pessoa, lugar ou data). `"pequeno": true` = versão discreta. A `legenda` antiga vira
  um título pequeno sozinha.
- `particulas`: folhas | poeira | neve | brasas | moedas | chuva.
- `neblina`: true (névoa suave passando).
- `luzes`: `[{ "x": 0.42, "y": 0.6, "raio": 0.15 }]` — brilho tremulando (lampião, vela, fogueira) em fração da tela.
- `movimento`: zoom_in | zoom_out | pan_esquerda | pan_direita | sobe (suave, com aceleração).

Sem nenhum extra, a imagem sai com o zoom de sempre + grão e vinheta (mais rápido de renderizar).
