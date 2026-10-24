# SEO e embalagem: Brás Cubas (Marca-Página, sáb 31/10/2026, 11h)

## 1. Opções de título (até 60 caracteres)
| # | Título | Gatilho | Caracteres |
|---|--------|---------|-----------|
| 1 | Brás Cubas vale ler hoje? Resumo e crítica honesta (RECOMENDADO) | pergunta que o vídeo responde + promessa de opinião | 51 |
| 2 | O livro em que o morto narra e debocha de você | curiosidade (o defunto-autor) | 46 |
| 3 | Brás Cubas: 160 capítulos e um defunto sem filtro | número + curiosidade | 49 |
| 4 | Machado de Assis: o clássico que cansa? Eu explico | contradição (clássico que cansa) + nome forte | 50 |
| 5 | Brás Cubas cansa por culpa do leitor, não do defunto | contradição (tese do vídeo) | 52 |

Recomendado: a 1. Vem da busca real ("vale a pena ler Brás Cubas") e o vídeo entrega exatamente isso: veredito, crítica e como ler. A 5 é a mais ousada e combina com a tese, mas só funciona se a opinião do Miguel confirmar o ajuste do roteiro.

## 2. Título + thumbnail
O título faz a pergunta e a thumb deve dar a provocação ou a imagem, sem repetir "Brás Cubas" nem "vale ler". Sugestão para o agente `thumbnail`: texto curto tipo "DEFUNTO DEBOCHADO" (ou "MORTO E SINCERO") com a ilustração de um defunto sorrindo em caixão/poltrona; nada de capa de livro. Título pergunta, thumb deixa o motivo para clicar.

## 3. Descrição
Está pronta no `09-seo.json` (campo `descricao`). Estrutura: 2 primeiras linhas fortes, resumo, aviso de spoiler (sem tempos; o motor calcula capítulos), onde ler de graça, pergunta de comentário, fontes do dossiê, aviso de IA (ilustrações e voz), crédito de música. Sem capítulos/tempos.

## 4. Capítulos
O motor calcula pelos blocos.

## 5. Tags e hashtags
Tags: Brás Cubas; Memórias Póstumas de Brás Cubas; Machado de Assis; resumo de livro; resenha; crítica literária; vale a pena ler; clássicos da literatura; literatura brasileira; Unicamp 2027; leituras obrigatórias; Marca-Página.
Hashtags: #BrásCubas #MachadoDeAssis #ResumoDeLivro

## 6. Playlist
Clássicos e vestibular

## 7. Comentário inicial
Se você virasse defunto-autor amanhã, sem nada a perder, qual seria o título do primeiro capítulo das suas memórias póstumas?

## 8. Campos extras
- `sintetico_realista`: false (ilustrações cartoon editoriais; nenhuma imagem realista de pessoa ou evento real).
- `musica_humor`: calmo (padrão do canal em `livros.yaml`).

## Pendências e avisos
- Link de afiliado: o briefing manda o link do livro na primeira linha da descrição, mas não há link no dossiê nem no config. Não inventei um. Quando o Miguel tiver o link da Penguin-Companhia, colocar na primeira linha e declarar "link de afiliado" (a nota de originalidade também pede isso).
- Não consegui listar a pasta `musica/` (as ferramentas desta rodada só leem arquivos conhecidos; não achei o diretório nos caminhos testados). Usei `calmo`, o valor do `livros.yaml`. Pelo contrato, se a pasta não existir o vídeo sai sem trilha, sem erro. Confirmar o nome real da pasta.
- O crédito de música na descrição está genérico ("acervo livre usado pelo canal"). Se a trilha exigir atribuição específica, completar.
- O roteiro está em 🟡 (falta a opinião do Miguel). Se o roteiro mudar de tese depois do ajuste, rever a opção de título 1 e o resumo da descrição.
- A frase sobre a Unicamp vem do dossiê (fonte oficial). Não afirmo data de prova.
