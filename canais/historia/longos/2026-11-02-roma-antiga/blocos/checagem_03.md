# Checagem do bloco 3 (A República e o pequeno agricultor)

**Veredito (reverificação): DEVOLVER** (2 correções exatas: 1 erro de data introduzido pela correção anterior e 2 URLs em `fontes`)

## Reverificação das correções anteriores
| Correção da rodada 1 | Aplicada? | Observação |
|---|---|---|
| 1. Tribunos "representantes escolhidos entre os plebeus" | Sim | Texto atual: "Eram representantes escolhidos entre os plebeus, considerados invioláveis". |
| 2. Far = trigo antigo, parente da espelta, escândia/emmer | Sim | Texto correto. |
| 3. Ressalva de época e escala sobre Catão | Aplicada, mas com erro | Ver correção A abaixo. |
| 4. Campo de Marte | Sim | |
| 5. Trocar links por específicos | Parcial | Catão ok; Livy e Britannica quebrados. Ver correção B. |

## Erro novo (veio da correção 3 da rodada 1)
Texto: "Ele escreveu cerca de dois séculos depois do tempo que estamos descrevendo". Catão escreveu o De agri cultura por volta de 160 a.C. O tempo descrito vai de 509 a 450 a.C. A distância é de cerca de 290 a 350 anos. "Cerca de dois séculos" é impreciso. Esse erro nasceu da sugestão da rodada anterior, não do roteirista.

## Checagem de URLs (`fontes`)
| URL | Resultado |
|---|---|
| https://www.britannica.com/place/ancient-Rome | Retorna 403 ao WebFetch (bloqueio de bot). A página existe, pois a busca a indexa (subpágina /The-Senate). OK. |
| https://www.worldhistory.org/Roman_Republic/ | Abre. Título "Roman Republic". OK. |
| https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Livy/3*.html | **404, não abre.** Também deu 404 em Livy/home.html. |
| https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Cato/De_Agricultura/home.html | Abre. "LacusCurtius, Cato, De Agricultura". É o índice da obra, com links para os capítulos. OK. |
| https://www.britannica.com/topic/Twelve-Tables | **Slug errado.** O verbete é "Law of the Twelve Tables", em https://www.britannica.com/topic/Law-of-the-Twelve-Tables (aparece na busca; o WebFetch dá 403 por bloqueio de bot). A busca confirma o conteúdo: 451-450 a.C., 12 tábuas de bronze expostas no Fórum, texto não sobrevive, só fragmentos citados por Cícero e outros. Isso sustenta o que o roteiro diz sobre as tábuas. |

Texto de Lívio 3.26 (Cincinato) confirmado em https://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.02.0026:book=3:chapter=26 (abre).

## Demais afirmações
Sem alteração em relação à tabela da rodada 1: todas ✅ (509 a.C., cônsules, magistrados, Senado e Cúria, assembleias, patrícios e plebeus, secessão de 494 a.C., Doze Tábuas c. 450 a.C. em bronze, puls, calendário agrícola, Cincinato com ressalva). Nada novo errado além do item A. Sem conselho de saúde, finanças ou direito, nada difamatório, nenhuma citação inventada, tudo dentro do nicho (sem ENEM/vestibular).

## Correções exatas
A. Em `texto`: trocar "Ele escreveu cerca de dois séculos depois do tempo que estamos descrevendo" por "Ele escreveu quase três séculos depois do tempo que estamos descrevendo".
B. Em `fontes`:
   - Trocar `https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Livy/3*.html` (404) por `https://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.02.0026:book=3:chapter=26` (ou outro link de Lívio livro 3 que o roteirista confirme que abre).
   - Trocar `https://www.britannica.com/topic/Twelve-Tables` por `https://www.britannica.com/topic/Law-of-the-Twelve-Tables`.
