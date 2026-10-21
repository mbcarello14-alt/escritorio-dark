#!/usr/bin/env bash
# Salva o trabalho no repositório, tentando de novo se outra execução salvou antes.
set -uo pipefail
MSG="${1:-escritório: atualização}"
git add -A
if git diff --cached --quiet; then echo "nada para salvar"; exit 0; fi
git commit -q -m "$MSG"
for i in 1 2 3 4 5 6; do
  git pull -q --rebase --autostash && git push -q && { echo "salvo"; exit 0; }
  echo "tentando de novo ($i)..."; sleep $((i * 3))
done
echo "não consegui salvar"; exit 1
