"""Narrador Gemini TTS (Google AI Studio): voz natural, com interpretação e tom por canal.

Precisa do segredo GEMINI_API_KEY (aistudio.google.com/apikey — não pede cartão).
Narra um BLOCO inteiro por chamada (poucas chamadas = cabe no plano gratuito) e salva em
<pasta>/audio/bloco_NN.wav. Depois o motor trata como narração gravada (sincroniza com Whisper).
"""
from __future__ import annotations

import base64
import os
import time
from functools import lru_cache
from pathlib import Path

import requests

from .comum import log, rodar

API = "https://generativelanguage.googleapis.com/v1beta"
PREFERIDOS = ["gemini-3.8-flash-tts", "gemini-3.1-flash-tts-preview", "gemini-2.5-flash-preview-tts",
              "gemini-3.8-flash-lite-tts", "gemini-2.5-pro-preview-tts"]

TOM_PADRAO = ("Narre em português do Brasil, com sotaque brasileiro neutro, como um youtuber jovem e "
              "carismático explicando história com bom humor: ritmo dinâmico, ironia leve nas piadas, "
              "pausas curtas antes das revelações e seriedade quando o assunto for triste.")


def _chave() -> str:
    k = os.environ.get("GEMINI_API_KEY", "").strip()
    if not k:
        raise RuntimeError("segredo GEMINI_API_KEY não configurado")
    return k


_esgotados: set[str] = set()   # modelos que bateram a cota do dia (cada modelo tem a sua)


@lru_cache(maxsize=1)
def _disponiveis() -> list[str]:
    forcado = os.environ.get("GEMINI_TTS_MODEL")
    if forcado:
        return [forcado]
    r = requests.get(f"{API}/models", params={"key": _chave(), "pageSize": 200}, timeout=60)
    r.raise_for_status()
    nomes = [m["name"].split("/")[-1] for m in r.json().get("models", [])
             if "tts" in m["name"] and "generateContent" in m.get("supportedGenerationMethods", ["generateContent"])]
    ordem = [p for p in PREFERIDOS if p in nomes] + sorted(n for n in nomes if n not in PREFERIDOS)
    if not ordem:
        raise RuntimeError("nenhum modelo de voz (TTS) disponível para esta chave")
    return ordem


def modelo() -> str:
    for m in _disponiveis():
        if m not in _esgotados:
            return m
    raise RuntimeError("Gemini TTS: todos os modelos de voz bateram a cota grátis do dia")


def _espera_sugerida(r) -> int | None:
    """Lê o 'retryDelay' do erro 429 (ex.: '37s')."""
    try:
        for d in r.json()["error"].get("details", []):
            if "retryDelay" in d:
                return int(float(d["retryDelay"].rstrip("s"))) + 2
    except Exception:
        pass
    return None


def sintetizar(texto: str, voz: str, tom: str, destino_wav: Path, tentativas: int = 12) -> Path:
    corpo = {
        # formato de "notas do diretor" + transcrição: deixa claro o que é instrução e o que é para ler
        "contents": [{"parts": [{"text": f"### DIRECTOR'S NOTES (do not read aloud)\n{tom}\n\n"
                                         f"#### TRANSCRIPT (read only this, word for word)\n{texto}"}]}],
        "generationConfig": {"responseModalities": ["AUDIO"],
                             "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voz}}}},
    }
    seguidos_429 = 0
    for t in range(tentativas):
        m = modelo()
        r = requests.post(f"{API}/models/{m}:generateContent", params={"key": _chave()}, json=corpo, timeout=300)
        if r.status_code == 429:
            seguidos_429 += 1
            dia = "PerDay" in r.text or "per day" in r.text.lower()
            if dia or seguidos_429 >= 3:
                log.warning("Gemini TTS: cota do modelo %s acabou — trocando de modelo", m)
                _esgotados.add(m)
                seguidos_429 = 0
                modelo()   # levanta erro se não sobrou nenhum
                continue
            espera = _espera_sugerida(r) or 30 * seguidos_429
            log.warning("Gemini TTS: limite por minuto (%s) — esperando %ss", m, espera)
            time.sleep(min(espera, 120))
            continue
        if r.status_code >= 500:
            log.warning("Gemini TTS instável (%s) — tentando de novo", r.status_code)
            time.sleep(15)
            continue
        if r.status_code != 200:
            raise RuntimeError(f"Gemini TTS {r.status_code}: {r.text[:300]}")
        seguidos_429 = 0
        try:
            cand = r.json()["candidates"][0]
            partes = cand["content"]["parts"]
            dados = next(p["inlineData"] for p in partes if "inlineData" in p)
        except (KeyError, IndexError, StopIteration):
            # resposta sem áudio (o modelo às vezes devolve vazio): tenta de novo; na 2ª falha troca de modelo
            motivo = (r.json().get("candidates") or [{}])[0].get("finishReason", "?")
            vazios = getattr(sintetizar, "_vazios", 0) + 1
            sintetizar._vazios = vazios
            log.warning("Gemini TTS devolveu resposta sem áudio (%s, %s) — tentando de novo", m, motivo)
            if vazios % 2 == 0:
                _esgotados.add(m)
                modelo()
            time.sleep(5)
            continue
        pcm = destino_wav.with_suffix(".pcm")
        pcm.write_bytes(base64.b64decode(dados["data"]))
        taxa = 24000
        mime = dados.get("mimeType", "")
        if "rate=" in mime:
            taxa = int(mime.split("rate=")[1].split(";")[0])
        rodar(["ffmpeg", "-nostdin", "-y", "-v", "error", "-f", "s16le", "-ar", str(taxa), "-ac", "1", "-i", str(pcm),
               "-ar", "44100", str(destino_wav)])
        pcm.unlink(missing_ok=True)
        return destino_wav
    raise RuntimeError("Gemini TTS: limite de uso atingido, tente mais tarde")


def narrar_blocos(pasta: Path, prod: dict, cfg: dict) -> None:
    """Gera audio/bloco_NN.wav para cada bloco que ainda não tem áudio."""
    from .gravacao import arquivo_bloco
    voz = cfg["voz"].get("gemini_voz", "Puck")
    tom = cfg["voz"].get("gemini_tom", TOM_PADRAO)
    (pasta / "audio").mkdir(exist_ok=True)
    for n, b in enumerate(prod["blocos"], 1):
        texto = " ".join(c["narracao"] for c in b["cenas"])
        wav = pasta / "audio" / f"bloco_{n:02d}.wav"
        if not arquivo_bloco(pasta, n):
            sintetizar(texto, voz, tom, wav)
            time.sleep(22)   # plano grátis: poucas chamadas por minuto
            log.info("narrador Gemini (%s, %s): bloco %d/%d", modelo(), voz, n, len(prod["blocos"]))
        aparar_fora_do_roteiro(wav, texto)
        from .narracao import limpar
        limpar(wav, texto, cfg)      # instrução lida no meio do trecho


def aparar_fora_do_roteiro(wav: Path, texto: str) -> None:
    """Corta o que a voz falou antes da 1ª ou depois da última frase do roteiro (ex.: leu a instrução de estilo)."""
    from .gravacao import _norm, transcrever
    palavras = transcrever(wav)
    if not palavras:
        return
    ouvidas = [_norm(w["palavra"]) for w in palavras]
    roteiro = [t for t in (_norm(p) for p in texto.split()) if t]
    if len(roteiro) < 4:
        return

    def acha(seq, inicio_lista, reverso=False):
        idxs = range(len(ouvidas) - len(seq), -1, -1) if reverso else range(len(ouvidas) - len(seq) + 1)
        for i in idxs:
            if sum(a == b for a, b in zip(ouvidas[i:i + len(seq)], seq)) >= len(seq) - 1:
                return i
        return None

    ini = acha(roteiro[:3], 0)
    fim = acha(roteiro[-3:], 0, reverso=True)
    corte_ini = palavras[ini]["inicio"] - 0.12 if ini and palavras[ini]["inicio"] > 0.6 else 0.0
    corte_fim = None
    if fim is not None and fim + 2 < len(palavras) - 1:
        ultimo = palavras[fim + 2]["fim"]
        if palavras[-1]["fim"] - ultimo > 1.2:
            corte_fim = ultimo + 0.25
    if corte_ini <= 0 and corte_fim is None:
        return
    extra = " ".join(w["palavra"] for w in palavras[:ini]) if corte_ini else ""
    log.warning("voz falou fora do roteiro em %s — aparando%s", wav.name, f" ('{extra[:80]}…')" if extra else "")
    tmp = wav.with_suffix(".aparado.wav")
    cmd = ["ffmpeg", "-nostdin", "-y", "-v", "error", "-i", str(wav), "-ss", f"{max(0.0, corte_ini):.3f}"]
    if corte_fim:
        cmd += ["-to", f"{corte_fim:.3f}"]
    rodar(cmd + [str(tmp)])
    tmp.replace(wav)
