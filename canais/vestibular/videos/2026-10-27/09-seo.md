# SEO e embalagem: Mapeado, terça 27/10/2026, 17h00
Tema: regra de três e porcentagem (Matemática). Playlist: Matemática.

## 1. Opções de título (até 60 caracteres)
| # | Título | Caracteres | Gatilho |
|---|--------|-----------|---------|
| 1 | **10% + 10% não dá 20%: o mapa da porcentagem no Enem** (recomendada) | 51 | contradição + número |
| 2 | Regra de três e porcentagem em um mapa só | 41 | promessa direta, palavra de busca |
| 3 | Regra de três: o teste de 1 pergunta antes da conta | 51 | curiosidade + número |
| 4 | A resposta errada já vinha impressa no Enem 2019 | 48 | curiosidade (gancho do bloco 7) |
| 5 | Enem 2026: regra de três e porcentagem em um mapa | 49 | urgência + nome forte (Enem) |

Honestidade: o título 1 é entregue no bloco 4 (21%, e 98,01 na abertura). Os títulos não prometem "o assunto que mais cai", porque o dossiê e o roteiro dizem que geometria ficou na frente em 2024.

## 2. Título e thumbnail juntos
O título carrega a contradição (10% + 10% não dá 20%). A thumb não deve repetir isso. Sugestão ao `thumbnail`: texto curto sobre o gancho da loja ("VOLTA PRA 100?" ou "R$ 98,01") com a etiqueta de preço desenhada. Título e thumb se completam: um mostra a regra, o outro mostra o enigma.

## 3. Descrição
Está em `09-seo.json` (campo `descricao`, cerca de 2.900 caracteres, sem `<` ou `>`). Pontos de cuidado:
- Duas primeiras linhas: o enigma da loja (R$ 98,01) e a pergunta única do mapa.
- A Tessat aparece como levantamento de um site de preparação, com classificação própria, não do Inep.
- Os números 1.200, 1.080 e 17,2% estão marcados como cálculo nosso.
- Fontes do dossiê: Inep, Tessat, CNN Brasil/SAS, Estratégia (datas), Descomplica, Plataforma Assaad. Fuvest, Unicamp e os percentuais de 37% ficam fora, pois o roteiro não os usa.
- Créditos: ilustrações de IA, voz sintética e trilha da categoria "foco". Não incluí nome de artista da música porque não encontrei o registro dos créditos no repositório; o motor ou o Miguel devem completar se a faixa exigir atribuição.
- O briefing cita o pacote de mapas mentais na Kiwify, mas não traz o link. Por isso a 3ª linha não tem link de produto. Quando o Miguel passar a URL, ela entra na 3ª linha.
- Capítulos: o motor calcula.
- Aviso de que o canal não promete aprovação (regra "proibido" do briefing).

## 4. Tags (15) e hashtags
Tags: enem 2026, regra de três, porcentagem, aumentos sucessivos, matemática enem, mapa mental, regra de três composta, grandezas inversamente proporcionais, revisão enem, questões do enem resolvidas, matemática básica, enem 2019 questão 153, fator multiplicativo, vestibular, mapeado.
Hashtags: #enem #matematica #regradetres

## 5. Playlist
Matemática (matéria do vídeo, no conjunto por matéria do canal).

## 6. Comentário inicial
"Na regra de três, você prefere o multiplicar cruzado ou o teste dobra ou cai pela metade? E qual ramo mais te derruba: balança, gangorra, engrenagens ou etiqueta de preço?" (cerca de 170 caracteres)

## 7. Campos de produção
- `sintetico_realista`: false (só doodles de quadro branco, sem pessoa ou evento real).
- `musica_humor`: foco (padrão do canal em `pipeline/config/vestibular.yaml`; não consegui confirmar se a pasta `musica/foco` existe. Se não existir, o vídeo sai sem trilha).

Os campos prontos para o `producao.json` estão em `09-seo.json`.
