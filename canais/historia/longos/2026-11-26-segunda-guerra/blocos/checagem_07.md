# Checagem do bloco 07 (Paris sob ocupação)

**Veredito final (2ª volta): APROVADO** (as 7 correções da 1ª volta foram aplicadas; nenhum erro novo no texto; uma observação não bloqueante sobre um link)

## Conferência das correções pedidas
| # | Correção pedida | Situação no bloco_07.json |
|---|---|---|
| 1 | Torre Eiffel: cabos cortados, torre fechada, elevadores só em 1946 | Aplicada ("Contam também que... os cabos dos elevadores... foram cortados e a torre ficou fechada ao público; ... só voltaram a funcionar em 1946"). Sem menção a Hitler nem a subir de escada. |
| 2 | Relógios: zona ocupada, junho de 1940, zona sul com outra hora até 1941 | Aplicada. "Uma hora adiante do horário de verão que já vigorava" confere com o tz database (França estava em horário de verão em jun/1940 e a zona ocupada passou a GMT+2). Zona sul até maio de 1941 confere. |
| 3 | "Racionamento generalizado" em setembro de 1940 | Aplicada. |
| 4 | Vel d'Hiv com data e número | Aplicada: 16 e 17/07/1942, mais de 12 mil judeus, mais de 4 mil crianças, maioria deportada para Auschwitz. Confere com USHMM e Prefeitura de Polícia (13.152 presos, 4.115 crianças). |
| 5 | Links: corrigir slug do Vel d'Hiv e trocar louvre.fr | Aplicada: slug `the-velodrome-dhiver-vel-dhiv-roundup` e Wikipedia sobre a evacuação do Louvre. |
| 6 | Estrela amarela "na zona ocupada" | Aplicada (junho de 1942, zona ocupada). |
| 7 | Êxodo "no norte do país e em Paris" | Aplicada. |
| extra | Suavizar cinema aquecido e metrô silencioso | Aplicada ("segundo relatos" nas duas frases). |

## Erros novos
Nenhum. Reconferidos: entrada alemã em Paris em 14/06/1940 (Britannica, WWII), armistício em 22/06/1940 (Britannica, Rethondes), divisão em zona ocupada e zona sob soberania francesa nominal (Britannica, Aftermath of the Battle of France), Louvre evacuado desde agosto de 1939.

## Links
- britannica.com/topic/Vichy-France e encyclopedia.ushmm.org/.../vichy-france: nova tentativa deu 403 e 502. Não foi possível abrir. Aceitos como fontes institucionais conhecidas, conforme orientação.
- britannica.com/place/Paris: não aberto (403). Aceito pelo mesmo critério.
- Busca confirmou que a Britannica tem páginas sobre a Batalha da França, mas sob o slug `event/Battle-of-France-World-War-II` (por exemplo `/The-fall-of-France-June-5-25-1940`). O link do JSON é `event/Battle-of-France`. Observação não bloqueante: trocar para `https://www.britannica.com/event/Battle-of-France-World-War-II` se quiser evitar link quebrado. Não afeta o texto narrado.
- encyclopedia.ushmm.org/.../the-velodrome-dhiver-vel-dhiv-roundup: URL que a busca mostra para o artigo. Aceito.

## Pendência de processo
O campo `checado` ainda está `false` no JSON. Quem fecha a etapa deve marcá-lo como `true` com base neste veredito.
