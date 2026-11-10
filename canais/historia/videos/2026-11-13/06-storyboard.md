# Storyboard — O dia em que o Brasil virou república sem perceber

Detalhe completo (narração e visual de cada cena) em `cenas.json`. Resumo por bloco (tipo de visual):

| # | Capítulo | Cenas | Visuais |
|---|----------|-------|---------|
| 0 | A fofoca que antecipou o fim de um império | 4 | mapa_animado (Rio), 3 ilustrações (a última é a chamada de inscrição/like) |
| 1 | O golpe com data marcada | 6 | ilustração, 2 imagens de arquivo (Benjamin Constant, Deodoro), 3 ilustrações |
| 2 | O boato na Rua do Ouvidor | 5 | mapa_animado, 3 ilustrações (major Sólon, áudio de família, quartel), linha_tempo (14 → 15 → 20) |
| 3 | O marechal sem fôlego | 5 | ilustrações (cama, mensageiro), mapa_animado (Campo de Santana), 2 ilustrações |
| 4 | Enquanto isso, em Petrópolis | 5 | mapa_animado (Rio → Petrópolis), 3 ilustrações, imagem de arquivo (Pedro II) |
| 5 | A manhã em que o governo caiu | 6 | 3 ilustrações, contador (1 ferido), 2 ilustrações |
| 6 | Viva quem, afinal? | 6 | 2 pinturas (Calixto, Bernardelli), ilustração, lista (3 versões), mapa_animado, ilustração |
| 7 | Fogo de palha | 6 | mapa_animado (Paço), 4 ilustrações, ilustração de comentário/like (pergunta da missa) |
| 8 | A República no papel | 6 | ilustração, imagem (Decreto nº 1), citação, 3 ilustrações |
| 9 | Demitido por carta | 5 | linha_tempo, citação, 2 ilustrações, contador (24 horas) |
| 10 | Madrugada no cais | 5 | 2 ilustrações, mapa_animado (rota Rio → Lisboa), ilustração, linha_tempo |
| 11 | Bestializados ou nem tanto? | 7 | cartão, 4 ilustrações, comparação, ilustração de pergunta final |
| 12 | O que fica do quinze de novembro | 5 | linha_tempo, 3 ilustrações, ilustração de inscrição/like/comentário |

Notas:
- Engajamento (inscrição, like, comentário): início (bloco 0, última cena), meio (bloco 7, última cena) e final (bloco 12, cena 4). A faixa animada entra sozinha sobre essas ilustrações.
- Mapas animados: Rio (bairros do centro), Petrópolis, Campo de Santana e rota do exílio no Atlântico. Coordenadas aproximadas; conferir com `python -m pipeline.validar` depois de montar o `producao.json`.
- Pinturas (Calixto, Bernardelli), documentos e retratos são imagens de arquivo de domínio público; se a busca falhar, o motor usa a ilustração reserva.
- Ilustrações de pessoas reais são desenhos estilizados, não realistas (`sintetico_realista` pode ficar `false`).
- Cena do bloco 3 sobre a madrugada de Deodoro é reconstituição declarada no próprio roteiro.
