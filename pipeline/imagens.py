"""Busca de imagens livres (domínio público e licenças Creative Commons) com crédito."""
from __future__ import annotations

import hashlib
import re
import time
from pathlib import Path

import requests

from .comum import log

UA = {"User-Agent": "EscritorioDark/1.0 (https://escritorio-dark.mbcarello14.workers.dev; canal educativo) python-requests"}
LICENCAS_OK = ("cc0", "pd", "public domain", "domínio público", "cc by", "cc-by", "pdm")


class Buscador:
    def __init__(self, pasta: Path, fontes: list[str]):
        self.pasta = pasta / "imagens"
        self.pasta.mkdir(parents=True, exist_ok=True)
        self.fontes = [f for f in fontes if f in ("wikimedia", "openverse")]
        self.usadas: set[str] = set()
        self.creditos: list[str] = []

    # ------------------------------------------------------------------ fontes
    def _wikimedia(self, busca: str) -> list[dict]:
        r = requests.get("https://commons.wikimedia.org/w/api.php", headers=UA, timeout=30, params={
            "action": "query", "format": "json", "generator": "search", "gsrnamespace": 6,
            "gsrsearch": f"{busca} filetype:bitmap", "gsrlimit": 12,
            "prop": "imageinfo", "iiprop": "url|extmetadata|size", "iiurlwidth": 1280,
        })
        r.raise_for_status()
        paginas = (r.json().get("query") or {}).get("pages", {}).values()
        out = []
        for p in sorted(paginas, key=lambda x: x.get("index", 99)):
            info = (p.get("imageinfo") or [{}])[0]
            meta = info.get("extmetadata", {})
            lic = (meta.get("LicenseShortName", {}).get("value") or "").lower()
            if not any(lic.startswith(l) or l in lic for l in LICENCAS_OK):
                continue
            if info.get("width", 0) < 1000:
                continue
            autor = re.sub(r"<[^>]+>", "", meta.get("Artist", {}).get("value") or "autor desconhecido").strip()
            out.append({"url": info.get("thumburl") or info.get("url"), "largura": info.get("width"),
                        "altura": info.get("height"),
                        "credito": f"{p.get('title', '').replace('File:', '')} — {autor} ({lic.upper()}), Wikimedia Commons"})
        return out

    def _openverse(self, busca: str) -> list[dict]:
        r = requests.get("https://api.openverse.org/v1/images/", headers=UA, timeout=30, params={
            "q": busca, "license": "cc0,pdm,by,by-sa", "size": "large", "page_size": 12,
        })
        r.raise_for_status()
        out = []
        for it in r.json().get("results", []):
            if (it.get("width") or 0) < 1000:
                continue
            out.append({"url": it["url"], "largura": it.get("width"), "altura": it.get("height"),
                        "credito": f"{it.get('title') or 'imagem'} — {it.get('creator') or 'autor desconhecido'} "
                                   f"({(it.get('license') or '').upper()} {it.get('license_version') or ''}), via Openverse"})
        return out

    # ------------------------------------------------------------------ público
    def buscar(self, busca: str) -> Path | None:
        """Tenta a busca completa e, se nada servir, versões mais curtas dela (menos específicas)."""
        vazias = {"photograph", "photo", "engraving", "illustration", "vintage", "lithograph", "painting", "portrait",
                  "the", "of", "a", "an", "in", "with", "and"}
        palavras = busca.split()
        chave = [w for w in palavras if w.lower() not in vazias]
        tentativas = [busca, " ".join(chave[:4]), " ".join(chave[:3]), " ".join(chave[:2]), " ".join(chave[-2:])]
        vistos = set()
        for t in tentativas:
            t = t.strip()
            if not t or t in vistos:
                continue
            vistos.add(t)
            p = self._buscar(t)
            if p:
                if t != busca:
                    log.info("imagem para '%s' achada buscando '%s'", busca, t)
                return p
        return None

    def _buscar(self, busca: str) -> Path | None:
        """Baixa a melhor imagem ainda não usada para `busca`. Devolve None se nada servir."""
        for fonte in self.fontes:
            try:
                candidatos = getattr(self, f"_{fonte}")(busca)
            except Exception as e:  # rede ou API fora do ar: tenta a próxima fonte
                log.warning("busca %s falhou em %s: %s", busca, fonte, e)
                continue
            # prioriza imagens horizontais
            candidatos.sort(key=lambda c: -((c["largura"] or 1) / max(c["altura"] or 1, 1) >= 1.2))
            for c in candidatos:
                if c["url"] in self.usadas:
                    continue
                destino = self.pasta / (hashlib.sha1(c["url"].encode()).hexdigest()[:16] + ".img")
                try:
                    if not destino.exists():
                        url = c["url"].split("?utm_")[0]
                        for espera in (0, 5, 15, 40):
                            time.sleep(espera or 0.6)          # educado com o servidor de imagens
                            r = requests.get(url, headers=UA, timeout=60)
                            if r.status_code != 429:
                                break
                        r.raise_for_status()
                        destino.write_bytes(r.content)
                    from PIL import Image
                    Image.open(destino).verify()
                except Exception as e:
                    log.warning("imagem inválida %s: %s", c["url"], e)
                    destino.unlink(missing_ok=True)
                    continue
                self.usadas.add(c["url"])
                if c["credito"] not in self.creditos:
                    self.creditos.append(c["credito"])
                log.info("imagem '%s' ← %s", busca, fonte)
                return destino
        log.warning("nenhuma imagem livre para '%s' — usando cartão", busca)
        return None
