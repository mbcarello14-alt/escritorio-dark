# Checagem do bloco 10 — Mercadores do Báltico e de Hedeby

**Veredito final (recheque): REPROVADO** (1 correção de fluidez, sem erro factual novo)

## Resultado da recheque
As 5 correções da primeira rodada foram aplicadas corretamente. Os ajustes opcionais também. O JSON é válido (inspeção linha a linha: chaves, vírgulas, aspas e `\n` escapados corretos; campos n, capitulo, texto, imagens, fontes e checado presentes). Não rodei parser, porque esta checagem não tinha acesso a shell.

| # | Correção pedida | Situação |
|---|---|---|
| 1 | Vinho "trazido provavelmente da região do Reno" (sem "em jarros") | Aplicada |
| 2 | "Hedeby também fazia as próprias moedas, a partir de cerca do ano oitocentos e vinte e cinco" (sem "entre as mais antigas") | Aplicada |
| 3 | Anel: "uma equipe de pesquisadores leu como para Alá. Outros acham que são só letras imitando o árabe, sem sentido. O debate segue aberto." | Aplicada |
| 4 | Ansgário: "formou-se ali uma pequena comunidade cristã, que não durou", com ressalva sobre a fonte cristã | Aplicada |
| 5 | Fontes: URL 404 trocada por Trade_during_the_Viking_Age e Hacksilver; Price et al. 2019 (doi 10.15184/aqy.2018.258) incluída | Aplicada |
| opc. | "passagens estreitas"; "trajeto curto por terra"; "dá para ler como o olhar de um estrangeiro" | Aplicados |

## Problema novo (fluidez), introduzido pela correção
- Parágrafo de Hedeby: "as mercadorias seguiam por terra, num trajeto curto por terra, até rios..." repete "por terra" duas vezes. Trocar por "as mercadorias seguiam por terra, num trajeto curto, até rios que levam ao mar do Norte".

## Erros factuais novos
Nenhum. Datas (804, c. 825, c. 965, c. 750-770, c. 830, 1878/2017, Unesco 2018 e 1993) conferem com as fontes da primeira rodada.

## Observações que não bloqueiam
- Frase "Uma viagem nos dá uma imagem curiosa." está meio solta. Sugestão: "Um viajante nos dá uma imagem curiosa."
- Britannica (3 URLs) e Wiley (ajpa.23308) deram 403 para robôs na primeira rodada. Seguem não verificadas por mim, e o DOI da Wiley parece ser o estudo de DNA de 2017 (não confirmado).
- Campo `"checado": false` fica como está até a aprovação.
- Nicho: nenhuma menção a ENEM, vestibular ou prova. Nenhum conselho de saúde, finanças ou direito. Nenhuma difamação.

## Lista exata para aprovar
1. Remover a repetição "por terra, num trajeto curto por terra" (ver acima). Depois disso, APROVADO sem nova checagem factual.
