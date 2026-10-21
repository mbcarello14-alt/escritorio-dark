"""Confere se o producao.json segue o CONTRATO.md antes de gastar tempo renderizando.

Uso: python -m pipeline.validar canais/<canal>/videos/<pasta>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

TIPOS = {
    "imagem": ["busca"], "ilustracao": ["cena"], "cartao": ["titulo"], "numero": ["valor"], "citacao": ["texto"],
    "lista": ["titulo", "itens"], "mapa_mental": ["mapa", "revelar"], "comparacao": ["esquerda", "direita"],
}


def validar(prod: dict) -> list[str]:
    erros = []
    for campo in ("canal", "titulo", "descricao", "tags", "thumbnail", "blocos"):
        if campo not in prod:
            erros.append(f"falta o campo '{campo}'")
    if erros:
        return erros
    if len(prod["titulo"]) > 100:
        erros.append("título passa de 100 caracteres")
    if len(prod["descricao"]) > 4500:
        erros.append("descrição passa de 4500 caracteres (o motor ainda acrescenta capítulos e créditos)")
    if any(c in prod["titulo"] + prod["descricao"] for c in "<>"):
        erros.append("título/descrição não podem ter '<' ou '>' (o YouTube recusa)")
    if sum(len(t) for t in prod["tags"]) > 450:
        erros.append("tags somam mais de 450 caracteres")
    th = prod["thumbnail"]
    if not th.get("texto") or len(th["texto"].split()) > 5:
        erros.append("thumbnail.texto deve ter de 1 a 5 palavras")
    if th.get("layout", "direita") not in ("esquerda", "direita", "centro"):
        erros.append("thumbnail.layout deve ser esquerda, direita ou centro")
    total_cenas, palavras = 0, 0
    for i, b in enumerate(prod["blocos"], 1):
        if not b.get("cenas"):
            erros.append(f"bloco {i} sem cenas")
            continue
        for j, c in enumerate(b["cenas"], 1):
            total_cenas += 1
            onde = f"bloco {i}, cena {j}"
            if not c.get("narracao", "").strip():
                erros.append(f"{onde}: narração vazia")
            palavras += len(c.get("narracao", "").split())
            v = c.get("visual") or {}
            t = v.get("tipo")
            if t not in TIPOS:
                erros.append(f"{onde}: visual.tipo inválido ({t})")
                continue
            for req in TIPOS[t]:
                if req not in v:
                    erros.append(f"{onde}: visual '{t}' precisa de '{req}'")
            if t == "mapa_mental" and isinstance(v.get("mapa"), dict):
                n = len(v["mapa"].get("ramos", []))
                if not 1 <= n <= 6:
                    erros.append(f"{onde}: mapa precisa de 1 a 6 ramos")
                if not 0 <= int(v.get("revelar", 0)) <= n:
                    erros.append(f"{onde}: 'revelar' fora do intervalo 0..{n}")
    if total_cenas < 3:
        erros.append("vídeo com menos de 3 cenas")
    return erros


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    arq = Path(sys.argv[1]) / "producao.json"
    try:
        prod = json.loads(arq.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"ERRO: não achei {arq}")
    except json.JSONDecodeError as e:
        raise SystemExit(f"ERRO: JSON inválido em {arq}: {e}")
    erros = validar(prod)
    if erros:
        print("ERROS no producao.json:\n- " + "\n- ".join(erros))
        sys.exit(1)
    cenas = sum(len(b["cenas"]) for b in prod["blocos"])
    palavras = sum(len(c["narracao"].split()) for b in prod["blocos"] for c in b["cenas"])
    print(f"OK: {cenas} cenas, {palavras} palavras (~{palavras / 150:.1f} min de narração)")


if __name__ == "__main__":
    main()
