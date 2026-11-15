# Formato do `reel.json` (Reels chamativos 3D)

Um Short vertical (1080×1920) de **15 a 30 segundos**: cena 3D low-poly feita por código (Three.js), narração da voz do canal,
legenda palavra por palavra, efeitos sonoros e o "comenta X" no fim. O agente escreve **só este JSON**; o motor
(`python -m pipeline.reel produzir <pasta>`) faz o resto. Os tempos das ações são **relativos ao começo de cada fala**:
o motor descobre sozinho quando cada fala começa na narração.

```json
{
  "canal": "historia",
  "titulo": "O pão de 200 bilhões de marcos",          // título do Short (até 70 caracteres; o motor põe #shorts)
  "descricao": "1–2 frases",
  "hashtags": ["#historia", "#economia", "#inflacao"],
  "legenda_reels": "texto para Instagram/TikTok (até 300 caracteres, 3–5 hashtags)",
  "isca": "Comenta PÃO",                                  // aparece na tela na última fala (e deve ser falado nela)
  "cenario": {"ceu": "#9ad0f5", "chao": "#86c06c", "cidade": true, "arvores": 3, "nuvens": true, "sol": true},
  "camera": {"pos": [0, 5, 15], "olha": [0, 3.2, 0]},
  "objetos": [ ... ],
  "falas": [ {"texto": "frase falada", "acoes": [ ... ]} ]
}
```

## Espaço da cena
- Chão em y = 0. Uma pessoa (boneco) tem ~3,3 de altura. Câmera padrão em [0, 5, 15] olhando [0, 3.2, 0].
- O vídeo é **vertical**: mantenha os objetos entre **x = −3 e x = 3** (fora disso sai da tela) e entre z = −4 e z = 3.
- Textos e números de tela usam `pos: [x, y]` em fração da tela: x de −1 (esquerda) a 1, y de −1 (baixo) a 1 (topo).
  Use y entre 0,45 e 0,85 (a parte de baixo é da legenda). `tam` 1 ≈ 7% da altura da tela.

## Objetos (`tipo`)
| tipo | campos extras | o que é |
|---|---|---|
| `boneco` | `cor`, `pele`, `cabelo`, `calca`, `chapeu: "cartola"`, `fala: true` (cabeça mexe) | pessoa de blocos |
| `predio` | `altura` (animável com `crescer`), `largura`, `cor` | prédio de cubo |
| `casa` | `cor`, `telhado` | casinha |
| `arvore` | — | árvore low-poly |
| `pilha_moedas` | `altura` = nº de moedas (0–`max_moedas`), `cor` (`dourado`, `prata`, `#hex`) | pilha que cresce |
| `moeda` | `cor`, `simbolo` | moeda grande em pé |
| `saco_dinheiro` | `cor`, `simbolo` | saco de dinheiro |
| `barra` | `altura`, `largura`, `cor` | barra de gráfico (cresce) |
| `seta` | `cor`, `rot` | seta para cima |
| `livro` | `cor`, `titulo` | livro deitado |
| `navio` | `cor` | navio |
| `lousa` | — | quadro negro com cavalete |
| `cubo` / `esfera` / `cilindro` | `tam` ([l,a,p] / diâmetro / [diâmetro, altura]), `cor` | formas básicas |
| `texto` | `texto` (pode ter `\n`), `cor`, `fundo`, `tam`, `pos` de 2 números = na tela | texto grande |
| `numero` | `valor`, `prefixo`, `sufixo`, `casas`, `cor`, `tam` | número que pode `contar` |

Campos comuns: `id` (único), `pos` [x, y, z], `rot` (graus em y), `escala`, `oculto: true` (só aparece com `aparecer`).

## Ações (`acoes` de cada fala)
Cada ação: `{"t": segundos desde o começo da fala, "alvo": "id", "acao": "...", "dur": opcional, "som": opcional}`.

| acao | campos | efeito |
|---|---|---|
| `aparecer` / `sumir` | — | entra com "pop" / some |
| `mover` | `para` [x,y,z] | anda até o ponto |
| `pular` | `altura` | pulinho |
| `girar` | `voltas` | gira no lugar |
| `olhar` | `para` (graus) | vira para um lado |
| `acenar` | — | boneco acena |
| `escalar` | `para` (ex.: 2 = dobro) | muda de tamanho com pulo |
| `crescer` | `para` (altura / nº de moedas) | prédio, barra ou pilha cresce |
| `contar` | `para` | número conta até o valor |
| `texto` | `texto` | troca o texto |
| `cor` | `cor` | muda a cor |
| `explodir` | — | explode em pedaços |
| `tremer` | `forca` (0,2–0,6) | câmera treme (sem `alvo`) |
| `camera` | `pos`, `olha` | câmera viaja (sem `alvo`) |

`som`: `boom` (impacto), `pop` (aparecer), `whoosh` (movimento rápido), `ding` (revelação), `caixa` (dinheiro), `tic`.

## Regras de ouro
1. **Gancho em 1,5 s:** a primeira fala é a frase mais absurda/curiosa do vídeo, com algo aparecendo na tela logo no início.
2. **Uma ideia só**, explicada com uma metáfora visual exagerada (pilha que cresce até o céu, prédio que dobra, boneco minúsculo ao lado de um número gigante).
3. **Algo muda na tela a cada 1–2 s** (ação, câmera, texto). Use `tremer` + `boom` no clímax, no máximo 2 vezes.
4. **4 a 7 falas**, 45 a 80 palavras no total (15–30 s). Números por extenso no `texto` falado; o `numero` na tela mostra em algarismos.
5. A última fala termina com a pergunta + a isca ("Comenta PÃO"), igual ao campo `isca`.
6. Só fatos com fonte (liste as fontes no `01-fontes.md` da pasta).

## Formato "construção passo a passo" (`"formato": "construcao"`)
Referência: vídeos virais em que a narração conversa com o espectador e a obra vai subindo etapa por etapa
("Primeiro, aplaine o terreno e espalhe a areia. Pronto, agora você tem uma base. Agora empilhe os blocos…").
O espectador fica até o fim para ver a obra pronta.

- **6 a 10 falas, 70 a 130 palavras (25–45 s).** Cada fala é **uma etapa**: a ordem no imperativo ("Primeiro, cave…",
  "Agora levante…", "Em cima disso, coloque…") + um fato curto que explica por que era feito assim.
- Fala com **`"pronto": "uma base sólida"`** → no fim dela o motor mostra o selo verde "✓ UMA BASE SÓLIDA" com "ding"
  (a frase falada deve terminar com "Pronto, agora você tem uma base sólida."). Pelo menos 3 etapas com `pronto`.
- Fala 1 = gancho que promete a obra inteira ("Vamos construir uma pirâmide do Egito do zero, do jeito que eles fizeram.").
  Última fala = obra pronta + pergunta + isca.
- Todas as peças começam com `"oculto": true` e entram com **`construir`**. A câmera **gira devagar** em volta da obra
  com `orbitar` (uma ação longa cobrindo o vídeo, ou várias), e se aproxima nos detalhes com `camera`.

### Peças de construção (além dos objetos da tabela de cima)
| tipo | campos | o que é |
|---|---|---|
| `terreno` | `tam` [largura, profundidade], `cor` | chão plano (grama, areia, terra batida, piso) |
| `agua` | `tam` [l, p], `cor` | lago, rio, fosso, piscina |
| `parede` | `tam` [comprimento, altura, espessura], `cor`, `rot` | parede, muro, muralha (gire 90° para os lados) |
| `telhado` | `tam` [largura, altura, profundidade], `cor` | telhado de duas águas, frontão |
| `cone` | `tam` [diâmetro, altura], `lados` | torre pontuda, tenda, vulcão (`lados` 4 = pirâmide) |
| `escada` | `tam` [l, a, p], `degraus` | degraus, arquibancada, zigurate, pirâmide em degraus |
| `arco` | `tam` [largura, altura, espessura] | arco romano, aqueduto, portão |
| `tunel` | `pontos` [[x,y],…] (y negativo = subsolo), `largura` | túnel escavado na parede de terra (com `cenario.corte`) |
| `camara` | `tam` [l, a], `pos` [x, y] | câmara/sala escavada no subsolo (com `cenario.corte`) |
Use também `cubo`, `cilindro`, `esfera`, `piramide`, `predio`, `casa`, `templo`, `castelo`, `torre`, `arvore`, `boneco` (operários com `escala` 0,5).
Para "trave", "cerca", "coluna", "rede" etc., combine `cubo` e `cilindro` (ex.: trave = 2 cilindros de pé + 1 deitado com `rot`).

**Cenário em corte** (`"cenario": {"corte": true}`): a terra aparece cortada de lado, com camadas, e dá para ver o
subsolo — formigueiro, mina, metrô, trincheira, raízes, camadas da Terra, fundação de prédio. Câmera em
`{"pos": [0, -1.5, 15], "olha": [0, -2.5, 0]}`; `tunel` e `camara` ficam na parede de terra (só `[x, y]`).
`cenario.camadas` (opcional) = cores das camadas de cima para baixo.

### Ações de construção
| acao | campos | efeito |
|---|---|---|
| `construir` | `modo`: `cresce` (padrão, sobe do chão esticando), `sobe` (emerge da terra), `cai` (despenca do céu e quica) | a peça entra com nuvem de poeira na base |
| `cavar` | `dur`, `ate` (0–1, padrão 1) | o túnel vai sendo escavado do primeiro ao último ponto |
| `orbitar` | `centro` [x,y,z], `raio`, `altura`, `de`, `ate` (graus), `dur` | a câmera gira em volta da obra (sem `alvo`) |
Sons: `pop` para peças pequenas, `boom` quando algo grande `cai`, `ding` já vem sozinho no selo "pronto".

Escala: a obra inteira cabe em x de −3 a 3 com a câmera padrão; para obras largas (estádio, cidade), afaste a câmera
(`pos` [0, 10, 24]) e use `orbitar` com `raio` 20–26.

## Jogos de pausa e de print (`"jogo"`) — substituem o antigo `desafio`
Dois jogos 2D por cima da cena (a cena 3D vira só o fundo; deixe poucos objetos, longe do centro). O motor desenha
o item, o molde e o movimento sozinho; o agente escolhe o item, os textos e os tempos.

**Encaixe** — um item cruza a tela rapidíssimo, várias vezes, em direções diferentes (algumas passadas raspando o molde,
para dar aflição) e encaixa no molde do tamanho exato **num único quadro**. "Pause quando o livro encaixar no quadrado."
```json
"jogo": {"tipo": "encaixe", "item": "livro", "texto": "Dom Casmurro", "sub": "Machado de Assis", "cor": "#7A1F2B",
         "pos": [0, 0.12], "inicio": {"fala": 1, "t": 1.0}, "momento": {"fala": 3, "t": 0.8}}
```
- `item`: `livro` (com `texto`/`sub` na capa), `caderno` (`texto` na etiqueta), `caneta`, `lingote` (barra de ouro, `texto`),
  `moeda` (`texto` = símbolo), `carta`. `cor` opcional. `pos` = centro do molde na tela (y 0 a 0,2).
- `momento` = o quadro do encaixe (fala + segundos dentro dela). Ponha no meio do vídeo, **nunca** na primeira nem na
  última fala, e não fale nada que entregue o momento. `ritmo` (opcional, padrão 0,62 s) = duração de cada passada.

**Print** — uma esteira de itens passa voando por uma moldura vermelha; o espectador tira print e comenta o que saiu.
```json
"jogo": {"tipo": "print", "item": "livro", "pos": [0, 0.1], "inicio": {"fala": 2, "t": 0},
         "itens": [{"texto": "Dom Casmurro", "sub": "Machado de Assis", "cor": "#7A1F2B"}, ...]}
```
- 8 a 24 itens, todos do mesmo `item` (`livro` ou `carta`; a `carta` aceita `emoji`, `texto`, `sub`, `cor`).
- A esteira roda do `inicio` até o fim do vídeo (`velocidade` padrão 2600 px/s).

Textos de tela do jogo (objeto `texto` com `pos` [0, 0.72]): curtos e em caixa alta ("PAUSE QUANDO ENCAIXAR!",
"TIRE PRINT AGORA!"). Falas: 4 a 6, 40 a 70 palavras: desafio na fala 1, provocação no meio ("quase ninguém consegue"),
isca no fim ("Comenta EU CONSEGUI" / "Comenta o livro que saiu no seu print").
