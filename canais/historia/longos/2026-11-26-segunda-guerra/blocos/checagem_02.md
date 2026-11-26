# Checagem do bloco 02 — "Cadernetas, hortas e luzes apagadas" (volta 2)

**Veredito: DEVOLVIDO** (uma correção só, na lista `fontes`; o texto está aprovado)

O texto da volta 2 incorporou as correções da volta 1 (Potato Pete e Doctor Carrot, fosso sul, estrelas como relatos pessoais, março de 1940 para a carne, pão de 1946 a 1948, anedotas sem fonte removidas). Nesta volta conferi os links de `fontes` um a um.

Limite: as páginas do IWM, do National Archives e do Historic Royal Palaces devolveram HTTP 403 e não consegui abri-las. O que sei sobre elas vem de resultados de busca e de outras fontes.

## Links pedidos

| Link | Resultado | Ação |
|---|---|---|
| Hansard 1939, `written-answers/1939/oct/11/road-accidents` | ❌ NÃO sustenta. É a resposta escrita de 11/out/1939 (vol. 352, cc362-3W) e só diz que o ministro esperava publicar o número de setembro "na semana seguinte". Não traz 1.130 nem 554. | Trocar por `https://api.parliament.uk/historic-hansard/commons/1939/oct/18/road-accidents` |
| Hansard 1941, `commons/1941/dec/10/royal-parks-london-allotments` | ✅ Confere. 10/dez/1941, Mr Hicks, do Ministério de Obras: um quarto de Hyde Park e Kensington Gardens com usos de guerra, "of which 14 acres are allotments and 133 acres are devoted to defence purposes". | Manter. O texto diz "catorze acres ... ocupados por hortas comunitárias", o que está certo. Não generalizar para "os parques viraram hortas". |
| Oxford, `teachingresources.web.ox.ac.uk/node/1083126` | ✅ Sustenta, em parte. Página didática sobre racionamento de comida na Segunda Guerra: racionamento de alimentos em 1940, cupons e sistema de pontos, cadernetas variando por idade, ocupação e saúde, pão racionado a partir de 1946, fim do racionamento em 1954. Não trata de blecaute nem de Dig for Victory. | Manter, só para o racionamento (pão em 1946, fim em 1954). Não serve de fonte para hortas ou blecaute. |

## Outros links de `fontes`

| Link | Resultado |
|---|---|
| Hansard 18/out/1939 (o novo) | ✅ Capt. Euan Wallace, Ministro dos Transportes, 18/out/1939: 1.130 mortes reportadas em setembro de 1939 contra 554 em setembro de 1938, na Grã-Bretanha. Confirma o texto. |
| MERL, cadernetas | ✅ Cadernetas emitidas em janeiro de 1940; marrom (adultos), verde (grávidas, lactantes e menores de 5), azul (5 a 16). Cada pessoa tinha açougueiro e verdureiro registrados. Confirma "lojas escolhidas". Não traz a data 8 de janeiro. |
| Museum Wales, artigo 2166 | ✅ Racionamento a partir de janeiro de 1940, Dig for Victory em 1939, pão racionado até 1948, doces em 1953, carne e bacon em 1954, Potato Pete e Doctor Carrot. Não menciona o sistema de pontos nem dezembro de 1941. |
| Museum Wales, blog 1079 | ✅ Potato Pete e Doctor Carrot, Ministério da Alimentação, Food Facts desde 1940. Não fala de trocar pão por batata. |
| AWM C98058 | ✅ Cartaz do Potato Pete (c. 1941-45, HMSO), Ministério da Alimentação. Doctor Carrot só aparece na descrição. |
| HRP, fosso da Torre | ⚠️ 403 para mim. Busca indica que a página diz que os Yeoman Warders usaram o fosso sul para frutas e legumes na guerra. O ano de 1940 apareceu na busca numa página de fatos do HRP (provavelmente "50 facts"), e não de forma clara nesta URL. |
| IWM racionamento, IWM blecaute, National Archives ração | ⚠️ 403 para mim, sem confirmação direta. Os fatos que dependem deles (8/jan/1940, blecaute de 1/set/1939, faixas brancas, dezembro de 1941 para os pontos) foram conferidos por outras fontes. |

## Pontos de menor risco no texto

- "Pedro Batata também sugeria trocar um pouco de pão por batata": nenhuma fonte que abri confirma. Sugestão: "incentivava comer mais batata". Não bloqueia.
- Sistema de pontos em dezembro de 1941 e a data de 8 de janeiro de 1940: corretos, mas nenhum link aberto por mim traz as datas. O 1/dez/1941 ficou confirmado só por busca. O ideal é que a lista cite o National Archives ou o IWM, a reconferir num navegador.
- Fosso da Torre: o texto atribui ao HRP o ano de 1940. Se não for possível reabrir a página do HRP, trocar "em 1940" por "durante a guerra".

## Correções para o roteirista

1. Em `fontes`, trocar `https://api.parliament.uk/historic-hansard/written-answers/1939/oct/11/road-accidents` por `https://api.parliament.uk/historic-hansard/commons/1939/oct/18/road-accidents`. É a única correção obrigatória.
2. Manter o Hansard 1941 e a página de Oxford (esta apenas como fonte do racionamento).
3. Opcional: trocar "sugeria trocar um pouco de pão por batata" por "incentivava comer mais batata".
4. Opcional: se o HRP não for reconferido, trocar "em mil novecentos e quarenta" por "durante a guerra" na frase do fosso.
5. Nicho: nenhuma menção a ENEM, vestibular ou revisão. Sem conselho de saúde, finanças ou direito, e nada difamatório. Sem citações a pessoas reais.
6. Manter `checado: false` até a versão corrigida. Depois da troca do link, o bloco pode passar sem nova volta.

**DEVOLVIDO**
