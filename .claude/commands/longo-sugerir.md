---
description: Sugere 3 temas para o vídeo longo da semana de um canal
argument-hint: <canal>
---

Canal: $ARGUMENTS (pasta `canais/$ARGUMENTS/`).

Chame o roteirista de longos **do canal** (`roteirista-longo-historia`, `roteirista-longo-livros` ou `roteirista-longo-vestibular`) para propor **3 temas** para o próximo vídeo longo (formato e duração em `longos` de `pipeline/config/$ARGUMENTS.yaml`).

Regras para os 3 temas:
- No nicho do canal (veja `canais/$ARGUMENTS/briefing.md`). Ouro & Império: história geral, qualquer era; temas com material para 2h30 de narração calma (uma civilização, uma cidade, uma era, uma grande viagem, a vida cotidiana de uma época).
- **Não repetir** nenhum tema dos longos já feitos (`canais/$ARGUMENTS/longos/*/estado.json`, campo `tema`) nem dos vídeos normais recentes (`canais/$ARGUMENTS/videos/*/estado.json`, campo `titulo`).
- Os 3 bem diferentes entre si (épocas e regiões diferentes).
- Cada um com uma frase de "por que funciona" (curiosidade, apelo para dormir, quantidade de histórias boas).

Grave `canais/$ARGUMENTS/longos/sugestoes.json` exatamente assim (a `semana` é a semana ISO de hoje no fuso de Brasília, ex.: `2026-W47`; rode `python3 -c "from datetime import datetime,timezone,timedelta; print((datetime.now(timezone.utc)-timedelta(hours=3)).strftime('%G-W%V'))"` para saber):
```json
{"semana": "2026-W47", "opcoes": [{"tema": "Egito dos faraós", "por_que": "..."}, {"tema": "...", "por_que": "..."}, {"tema": "...", "por_que": "..."}]}
```
