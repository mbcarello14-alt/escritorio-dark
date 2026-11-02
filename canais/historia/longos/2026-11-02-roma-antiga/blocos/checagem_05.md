# Checagem do bloco 5: "Estradas, portos e o mar que virou nosso"

**Veredito atual (2ª volta): APROVADO** (ver seção "2ª volta" no fim). O veredito da 1ª volta foi CORRIGIR e está preservado abaixo como histórico.

## 1ª volta (histórico). Veredito: CORRIGIR (3 correções obrigatórias, 3 recomendadas)

### Correções necessárias

1. **Édito de Diocleciano, "trezentas milhas" (obrigatória).** O número "300 milhas de carroça custa mais que cruzar o Mediterrâneo" não foi confirmado em fonte. O que se achou:
   - Duncan-Jones: 100 milhas romanas por terra custam cerca de 55% do valor do trigo, contra cerca de 1,3% por mar.
   - Fórmula clássica atribuída a A.H.M. Jones (*The Later Roman Empire*): carregar trigo por cerca de 75 milhas por terra sairia mais caro que levá-lo de uma ponta à outra do Mediterrâneo. Não consegui abrir o texto de Jones.
   - O Édito (301 d.C.) fixa tetos de preço, não preços reais. Foi pouco cumprido, e o texto é reconstruído de fragmentos.
   - Redação sugerida: "Séculos mais tarde, o Édito de Preços de Diocleciano, que fixava preços máximos, traz tarifas que levam muitos historiadores a concluir que o frete por terra era várias vezes mais caro que o frete por mar. Em certas contas, carregar trigo algumas dezenas de milhas de carroça custava tanto quanto levá-lo de navio pelo Mediterrâneo inteiro." Se quiser número, cite só com fonte aberta (Jones/Duncan-Jones/Arnaud) e inclua a fonte em `fontes`.
   - Observação: a menção ao Édito era uma antecipação. Confirmar que o bloco 6 ou posterior trata do Édito, senão a promessa fica solta.
2. **"Mare Nostrum" atribuído a Salústio (obrigatória, ou suavizar).** Nenhuma fonte da lista nem a pesquisa confirmaram a passagem. Sugestão: remover o nome de Salústio ("A expressão aparece em autores latinos") ou só mantê-lo com a referência exata verificada. Wikipedia (sem citação) diz que o termo começou valendo para o Tirreno e só cobriu o Mediterrâneo todo por volta de 30 a.C.
3. **Distância Roma-Cápua.** Trocar por "cerca de duzentos quilômetros" (132 milhas romanas ≈ 195 km; outras fontes dão 115 a 120 milhas).

### Recomendadas

4. **Brindisi.** Não citar data (fontes divergem, cerca de 264 a 190 a.C.).
5. **Óstia a "cerca de trinta quilômetros".** Britannica dá cerca de 24 km. Usar "cerca de vinte e cinco quilômetros".
6. **Mosaicos da Praça das Corporações.** Atribuir a leitura "placas de identificação" aos arqueólogos e situar no tempo (século II d.C.).

## 2ª volta (recheque após correções). Veredito: APROVADO

Releitura integral de `bloco_05.json`. Bloco não foi editado por mim.

### As 5 correções pedidas foram aplicadas?

| Correção pedida | Aplicada? | Trecho atual no bloco |
|---|---|---|
| Édito de Diocleciano sem número de milhas | Sim | "traz tarifas que levam muitos historiadores a concluir que o frete por terra era várias vezes mais caro... Em certas contas, carregar trigo algumas dezenas de milhas de carroça custava tanto quanto levá-lo de navio pelo Mediterrâneo inteiro". Também ganhou "fixava tetos de preço e foi pouco cumprido", correto. A antecipação "vamos falar adiante" não existe mais, então não há promessa solta. |
| Mare Nostrum sem Salústio | Sim | "A expressão aparece em autores latinos. Não era um título oficial, era um modo de falar". Genérico e verdadeiro. |
| Roma-Cápua ~200 km | Sim | "a cerca de duzentos quilômetros" |
| Óstia ~25 km | Sim | "a cerca de vinte e cinco quilômetros de Roma" (coerente com o bloco 1, que dá ~25 km de Roma ao mar) |
| Mosaicos atribuídos aos arqueólogos | Sim | "Segundo os arqueólogos, os mosaicos funcionavam como placas de identificação", com "século segundo depois de Cristo" |

Também confirmado: a recomendação 4 foi seguida (Brindisi sem data). A referência interna "o rio que vimos no começo, com o sal e o gado" confere: o bloco 1 trata de sal (salinas na foz, Via Salária) e de gado (pecus/pecunia, Fórum Boário).

### Erro novo?

Nenhum erro factual novo. Revisão dos pontos que mudaram ou poderiam ter mudado:

| Afirmação | Status | Observação |
|---|---|---|
| Édito "fixava tetos de preço e foi pouco cumprido" | ✅ | Édito de 301 d.C. fixou preços máximos; aplicação fraca. |
| Frete terrestre várias vezes mais caro que o marítimo; "algumas dezenas de milhas" de carroça equivalem a cruzar o Mediterrâneo | ✅ | Consistente com Duncan-Jones (55% vs 1,3% por 100 milhas) e a fórmula atribuída a Jones (~75 milhas). Redação hedgeada ("em certas contas"). |
| Cápua a ~200 km | ✅ | 132 milhas romanas ≈ 195 km. |
| Óstia a ~25 km de Roma | ✅ | Britannica ~24 km. |
| Mare Nostrum "em autores latinos", não oficial | ✅ | Sem nome nem data. |
| Mosaicos do século II d.C., "segundo os arqueólogos" | ✅ | Ver nota abaixo. |

### Notas não bloqueantes (opcionais)

- **Mosaicos:** a Praça das Corporações tem mosaicos de fins do séc. II e do séc. III d.C. "Do século segundo" não é falso, mas "dos séculos segundo e terceiro" seria mais exato. Opcional.
- **Fontes:** a lista `fontes` continua sem fonte específica para o Édito de Diocleciano/frete (Duncan-Jones, Jones ou Arnaud). Como a afirmação agora é genérica e hedgeada, não bloqueia, mas vale acrescentar uma fonte aberta para rastreabilidade.
- **Campo `checado`:** continua `false` no JSON. Quem orquestra deve marcá-lo `true` conforme o fluxo do `/longo-escrever`; não editei o bloco, como pedido.

### Outros pontos (reverificados)

- Citações a pessoas reais: nenhuma inventada (Estácio, *regina viarum*, autêntica).
- Sem conselho de saúde, finanças ou direito, e nada difamatório.
- Nicho: nenhuma menção a ENEM, vestibular ou prova. Dentro do nicho de Ouro & Império.
- Pedido de inscrição, like e comentário está no bloco 1 (abertura), não neste bloco; regra de meio e final cabe ao plano geral do longo, fora do escopo desta checagem.

## Tabela (1ª volta, com status atualizado na 2ª)

| Afirmação | Status | Fonte | Correção / situação |
|---|---|---|---|
| Via Ápia iniciada em 312 a.C. por Ápio Cláudio, censor | ✅ | Britannica; Tito Lívio 9.29 | nenhuma |
| Apelido "Cego" (Caecus) dado "mais tarde" | ✅ | Britannica | nenhuma |
| Roma a Cápua | ✅ (corrigido) | 132 milhas romanas ≈ 195 km | "cerca de 200 km" aplicado |
| Prolongada até Brindisi | ✅ | Britannica | sem data, ok |
| Estácio: "regina viarum" | ✅ | Estácio, *Silvae* 2.2.12 | nenhuma |
| Construção em camadas, abaulada, valas laterais | ✅ | WorldHistory, Britannica | nenhuma |
| Basalto na superfície | ✅ | Britannica | nenhuma |
| Trechos ainda existem, mais de 2 mil anos | ✅ | Britannica | nenhuma |
| Milha romana = mil passos duplos, ~1,5 km | ✅ | WorldHistory | nenhuma |
| Paradas e correio do Estado | ✅ | WorldHistory | nenhuma |
| ~80 mil km pavimentados (aproximado, discutido) | ✅ | WorldHistory/Wikipedia | nenhuma |
| Terra mais cara que mar | ✅ | Duncan-Jones | nenhuma |
| Édito de Diocleciano | ✅ (corrigido) | Duncan-Jones / Jones | número removido |
| Cartago fundada por fenícios | ✅ | Britannica | nenhuma |
| Guerras púnicas 264-241, 218-201, 149-146 a.C. | ✅ | Britannica | nenhuma |
| "Púnico" = nome latino dos cartagineses | ✅ | Punicus, de Poenus | nenhuma |
| Sicília, Sardenha, Córsega, Hispânia, África | ✅ | Britannica/WorldHistory | resumido, correto |
| Província, governador, impostos; Sicília celeiro | ✅ | WorldHistory | nenhuma |
| Mare Nostrum | ✅ (corrigido) | consenso | Salústio removido |
| Marinha patrulhava, menos piratas | ✅ | contexto (Pompeu, 67 a.C.) | nenhuma |
| Óstia na foz do Tibre | ✅ (corrigido) | Britannica (~24 km) | "cerca de 25 km" aplicado |
| Óstia nasceu como pequeno forte na República | ✅ | Britannica | nenhuma |
| Cláudio abriu bacia no séc. I d.C.; Trajano a hexagonal; Portus | ✅ | Britannica | nenhuma |
| Horrea; barcaças puxadas da margem | ✅ | Óstia/Portus; WorldHistory/Thayer | nenhuma |
| Praça com mosaicos; leitura dos arqueólogos | ✅ (corrigido) | Britannica Ostia | atribuição aplicada |
| Referência ao rio, sal e gado | ✅ | bloco 1 | confere |
| Cena final | ✅ | licença narrativa | nenhuma |

**Resumo final: APROVADO.** Nenhuma correção obrigatória restante. Apenas duas sugestões opcionais (mosaicos "séculos segundo e terceiro"; acrescentar fonte do Édito em `fontes`).
