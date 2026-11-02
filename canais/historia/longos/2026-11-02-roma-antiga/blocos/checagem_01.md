# Checagem do bloco 01 — "Uma aldeia à beira do Tibre"

**Veredito final (reverificação): APROVADO**

Todas as 7 correções obrigatórias e as 3 recomendadas da rodada anterior foram aplicadas em `bloco_01.json`. Nenhum erro novo foi encontrado. Ressalva só sobre uma URL em `fontes` (ver abaixo), que não bloqueia.

## Correções da rodada anterior

| # | Correção | Resultado |
|---|---|---|
| 1 | Cereais: escandra e espelta, além da cevada | Aplicada |
| 2 | Via Salária: sal vem da foz, chega às colinas e segue pela Salária rumo aos sabinos | Aplicada |
| 3 | Fórum: enterro como fato, pasto como "é provável" | Aplicada |
| 4 | "historiadores romanos mais tarde contaram os anos a partir dela" | Aplicada |
| 5 | "cerca de vinte e cinco quilômetros do mar em linha reta, um pouco mais seguindo as curvas do rio" | Aplicada (Britannica: cerca de 24 km) |
| 6 | Fórum Boário na margem do rio, entre Capitólio, Palatino e Aventino | Aplicada |
| 7 | Cidades gregas "com portos e comércio por mar" (sem moeda nem filósofos) | Aplicada |
| 8 | Ilha Tiberina "ajudava a travessia", sem "mais estreito" | Aplicada |
| 9 | Chamada de engajamento no início com "comente" | Aplicada. Meio e final continuam a cargo dos blocos 2 e 3 |
| 10 | `fontes` específicas | Aplicada (6 URLs, ver tabela) |

## Varredura por afirmações novas

Nada novo errado. Pontos observados, todos aceitáveis:
- "navios de piratas não chegassem fácil" é raciocínio sobre a localização (vantagem defensiva clássica), apresentado como explicação e não como fato datado. Aceitável.
- "a Cloaca Máxima ainda existe em parte" e "a tradição diz que foi obra dos reis": confirmado por Ancient Rome Live (atribuição ao último rei, Tarquínio; ampliada depois).
- Via Salária ligada ao sal e aos sabinos: confirmado pela Wikipedia (sabinos buscavam sal nas salinas da foz do Tibre, Campus Salinarum).
- Fórum: pântano drenado pelos Tarquínios, necrópole do séc. X a.C.: confirmado pela Wikipedia.
- Nicho: sem ENEM, vestibular ou prova. Sem conselho de saúde, finanças ou direito. Nada difamatório. Citação de pessoa real: nenhuma.

## Verificação das URLs em `fontes`

| URL | Resultado |
|---|---|
| https://www.britannica.com/place/ancient-Rome | Existe (retorna 403 ao WebFetch por bloqueio de bot; aparece nos resultados de busca da Britannica) |
| https://www.britannica.com/place/Tiber-River | Existe (mesmo caso: 403 ao WebFetch, aparece na busca) |
| https://en.wikipedia.org/wiki/Via_Salaria | Abre. Sustenta a rota do sal e os sabinos |
| https://digi.ub.uni-heidelberg.de/diglit/platner1929/0532 | **Não abriu**: bloqueio anti-bot (Anubis, "Access Denied"). A busca confirma que a obra (Platner/Ashby 1929) está no domínio, mas a página 0532 não apareceu nos resultados e não foi possível ver o conteúdo |
| https://en.wikipedia.org/wiki/Roman_Forum | Abre. Sustenta pântano, drenagem e necrópole |
| https://ancientromelive.org/?p=126 | Abre. Página sobre a Cloaca Máxima |

Recomendação não bloqueante: o link do Heidelberg não pôde ser confirmado nem quanto à existência da página nem quanto ao assunto. Se for citado na descrição do vídeo, conferir manualmente que a página 0532 trata de Salaria ou do Fórum, ou trocar por um link do Platner no LacusCurtius (Thayer). Os demais cinco links sustentam o conteúdo do bloco.

## Veredito: APROVADO
