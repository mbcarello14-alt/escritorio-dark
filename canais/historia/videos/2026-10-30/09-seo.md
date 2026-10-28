# SEO e embalagem — Templários (Ouro & Império, sex 30/10/2026 18h)

## 1. Opções de título

| # | Título | Caracteres | Gatilho |
|---|--------|-----------|---------|
| 1 (recomendada) | Templários: o rei sem dinheiro e o banco que ele quebrou | 56 | contradição + nome forte (o banco quebrou o rei ou o contrário?) |
| 2 | O rei que devia ao banco e mandou prender o gerente | 51 | curiosidade (imagem do gerente preso) |
| 3 | Templários: a dívida do rei foi mesmo o motivo? | 47 | contradição com a versão popular |
| 4 | 1307: o dia em que um rei sem caixa prendeu um banco | 52 | número/data + curiosidade |
| 5 | Sexta 13 não é culpa dos Templários (e o rei sabe) | 50 | mito derrubado + nome forte |

Recomendada: a 1. É o título já registrado no `estado.json`, promete o ângulo econômico e é honesta: o vídeo diz que o calote é hipótese e entrega o caixa apertado do rei, que está documentado. A 2 e a 4 sugerem dívida provada, então ficam em segundo plano. A 5 foge do eixo do vídeo.

## 2. Título + thumbnail
O título carrega "rei sem dinheiro" e "banco". A thumb não deve repetir: texto sugerido de 2 a 3 palavras, "CALOTE OU FÉ?" ou "QUEM PAGOU?", com a imagem de um rei de coroa segurando um cofre vazio diante de um cavaleiro com bolsa de moedas (ilustração, estilo do canal). Texto e título se completam: o título dá o contexto, a thumb dá a dúvida. Nada de fogueira ou imagem gráfica. Definição final com o agente `thumbnail`.

## 3. Descrição
Está no `seo.tmp.json` (campo `descricao`). As duas primeiras linhas são o gancho do gerente preso e a ressalva do calote. Traz resumo, aviso de honestidade, aviso de ilustrações geradas por IA (mais voz sintética), pergunta e fontes do dossiê. Sem link de afiliado: o briefing prevê afiliados de livros, mas não há link cadastrado. Quando houver, entra na 3ª linha.

## 4. Capítulos
Calculados pelo motor a partir dos blocos.

## 5. Tags e hashtags
Tags: templários, cavaleiros templários, ordem dos templários, filipe o belo, jacques de molay, sexta-feira 13, história medieval, idade média, história econômica, banco medieval, história da frança, pergaminho de Chinon, ordem de cristo, ouro e império.
Hashtags: #templários #históriamedieval #históriaeconômica

## 6. Playlist
Idade Média.

## 7. Comentário inicial
O que pesou mais na cabeça de Filipe IV para prender os Templários: o cofre vazio, a fé ou o poder sobre o papa? Deixe sua aposta e a razão em uma frase. Eu volto nela no final do vídeo.

## 8. Campos técnicos
- `musica_humor`: misterio (padrão do canal em `pipeline/config/historia.yaml`; não consegui listar a pasta `musica/` aqui, então confirme se existe).
- `sintetico_realista`: false (ilustrações em estilo desenho, sem imagem realista de pessoa ou evento real; sem voz clonada de pessoa real).
