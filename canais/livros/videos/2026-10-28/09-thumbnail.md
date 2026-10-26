# Thumbnail — Frankenstein (Marca-Página, 28/10)

Título: "Frankenstein: o livro é bem diferente do monstro que você conhece"

## Conceito 1 (escolhido): "O CRIADOR FUGIU"
- Texto à esquerda, 3 palavras, em DM Serif sobre o degradê bordô.
- Imagem à direita: criatura grande, triste, sem parafuso nem costura, sentada com um livro aberto (sem texto na página). Ao fundo, minúsculo, o cientista correndo por uma porta.
- Completa o título sem repeti-lo. O título desmonta o monstro de Halloween e a thumb mostra a tese do vídeo: o pecado é o abandono, não o experimento. A pergunta que fica é "fugiu de quê?".
- Honesta: a fuga acontece no bloco 3 e é a tese do vídeo.
- O rosto é de ilustração, sem pessoa real, sem logo e sem o monstro da Universal (sem cabeça quadrada e sem parafuso), então não copia personagem de terceiros.

## Conceito 2: "O MONSTRO LÊ MILTON"
- Criatura de perfil, lendo à luz de uma vela, texto à direita.
- Curiosidade forte, mas o nome "Milton" é pouco reconhecido no celular e depende do título para fazer sentido. Descartado.

## Diferença das últimas thumbs
O histórico do canal está vazio, então não há thumb anterior para evitar. Esta é a primeira.

## Objeto
```json
{"texto": "O CRIADOR FUGIU", "cena": "flat 2D editorial illustration, a large pale-green melancholic creature with long dark hair and a sad expressive face, no bolts, no stitches, sitting alone at the far right holding an open book, a tiny cartoon scientist silhouette running away through a doorway in the far background, big empty space on the left, burgundy, mustard and cream palette, soft paper texture", "imagem_busca": "Frankenstein 1818 frontispiece engraving", "layout": "esquerda"}
```

`cena` é suportado: `pipeline/produzir.py` chama `ctx.imagem(th.get("cena"), th.get("imagem_busca"))`. Se a IA falhar, cai para `imagem_busca` (gravura do frontispício de 1831 ou similar, domínio público).
