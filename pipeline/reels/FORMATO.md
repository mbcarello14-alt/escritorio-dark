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
