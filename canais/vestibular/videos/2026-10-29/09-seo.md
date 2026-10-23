# SEO e embalagem — Mapeado — quinta 29/10/2026, 17h

## 1. Títulos (até 60 caracteres)

| # | Título | Caracteres | Gatilho |
|---|--------|-----------|---------|
| 1 (RECOMENDADO) | Era Vargas no ENEM: 3 governos em 1 mapa mental | 47 | número + palavra de busca ("Era Vargas", "ENEM") logo no início |
| 2 | Vargas: o mapa que resolve a questão do ENEM 2010 | 49 | promessa concreta (o vídeo resolve a questão de verdade) |
| 3 | Vargas: presente ou conquista? Como o ENEM cobra | 48 | contradição / pergunta (o debate que a prova explora) |
| 4 | Era Vargas: 15 anos, 3 governos, 1 mapa para o ENEM | 51 | número (Vargas ficou quinze anos, dito no roteiro) |
| 5 | Era Vargas no ENEM: o mapa dos 3 governos em 1 desenho | 54 | número (título provisório, mantido como reserva) |

Por que a 1: tem a busca principal no começo, é curta (não corta no celular) e entrega exatamente o que o vídeo mostra (3 governos, 1 mapa mental). Nenhuma opção promete nota ou "macete".

## 2. Título + thumbnail

O título diz o que é (3 governos, 1 mapa). A thumb deve levantar a dúvida que o vídeo resolve, sem repetir o título. Sugestão de texto (até 4 palavras): **PRESENTE OU CONQUISTA?**, com o mapa colorido (azul, verde, vermelho, amarelo) ao fundo. A thumb dá a tensão (o debate do bloco 5 e a questão de 2010) e o título dá o conteúdo. A decisão final é do agente `thumbnail`.

## 3. Descrição

Está em `_seo.json` (campo `descricao`, cerca de 3.900 caracteres, sem `<` ou `>`). Estrutura:
- Linhas 1 e 2 (aparecem antes do "mais"): o gancho dos 81 anos da deposição de Vargas (fato 23 do dossiê: 29/10/1945, Forças Armadas) e a promessa do mapa com os 4 galhos + questão do ENEM 2010.
- Resumo em tópicos do que o vídeo cobre.
- Aviso de que não promete nota e lembrete da prova de Humanas em 8/11.
- Chamada para inscrição e comentário.
- Declaração de IA: ilustrações geradas por IA (estilo quadro branco) e narração por voz sintética.
- Fontes do dossiê (links oficiais primeiro: Câmara, Senado, TSE, TRT; depois fontes secundárias).
- Capítulos, créditos de imagem de acervo e legendas: o motor acrescenta.

Pendências para o Miguel:
- **Link do produto:** o briefing diz que o pacote de mapas mentais em PDF (Kiwify) vai linkado em todo vídeo, mas não há URL no briefing nem no yaml. Não inventei link. Quando houver, entra na 3ª linha da descrição.
- **Crédito de música:** não há nome de faixa no material; fica a cargo do motor (pasta `musica/foco`).
- **Questão do ENEM:** a descrição cita "ENEM 2010, 1º dia, caderno azul" sem o número da questão, conforme a checagem (o "32" só aparece em uma fonte e o PDF do Inep não foi aberto).

## 4. Capítulos

Não escritos: o motor calcula pelos 9 blocos do roteiro.

## 5. Tags (14) e hashtags

Tags: era vargas, getúlio vargas, enem 2026, história enem, estado novo, governo provisório, governo constitucional, mapa mental história, resumo era vargas, revisão enem, questão enem 2010, história do brasil, enem humanas, CLT

Hashtags: #enem #eravargas #mapamental

## 6. Shorts

Com o `clipador`.

## 7. Playlist

**História** (matéria do vídeo; o motor cria se não existir).

## 8. Comentário inicial

"Pergunta que a prova adora: as leis trabalhistas da Era Vargas foram um presente do governo ou uma conquista dos trabalhadores? Responda "presente", "conquista" ou "os dois" e diga qual fase mais te confunde."

Retoma a pergunta do meio do roteiro (bloco 5) e a do fechamento.

## 9. Campos para o producao.json

Salvos em `canais/vestibular/videos/2026-10-29/_seo.json`: `titulo`, `descricao`, `tags`, `hashtags`, `playlist`, `comentario_inicial`, `musica_humor` ("foco", conforme o yaml), `sintetico_realista` (false: as ilustrações são doodles de quadro branco, sem imagem realista de pessoa ou evento real).

Observação: "81 anos" e a data 29/10/1945 são fato do dossiê (fato 23, Câmara, confiança alta) e foram conferidos pelo `checador`. Só valem se o vídeo sair mesmo em 29/10.
