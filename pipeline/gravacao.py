"""Narração gravada pelo Miguel: limpa o áudio de cada bloco, transcreve e corta por cena.

Os áudios chegam pelo Telegram em `<pasta>/audio/bloco_01.ogg`, `bloco_02.ogg`...
A transcrição (faster-whisper, grátis) dá o tempo de cada palavra; com isso o motor sabe
onde cada cena começa e gera legendas com o que foi realmente falado.
"""
from __future__ import annotations

import difflib
import re
import unicodedata
from pathlib import Path

from .comum import duracao_audio, log, rodar

_modelo = None
EXTENSOES = (".ogg", ".oga", ".opus", ".mp3", ".m4a", ".wav", ".aac", ".webm")


def arquivo_bloco(pasta: Path, n: int) -> Path | None:
    for ext in EXTENSOES:
        p = pasta / "audio" / f"bloco_{n:02d}{ext}"
        if p.exists():
            return p
    return None


def blocos_faltando(pasta: Path, total: int) -> list[int]:
    return [n for n in range(1, total + 1) if not arquivo_bloco(pasta, n)]


def limpar_audio(origem: Path, destino: Path) -> Path:
    """Tira ruído e graves, comprime, normaliza e corta silêncio do começo e do fim."""
    # duas passagens: encadear areverse com loudnorm no mesmo filtro trava o FFmpeg
    meio = destino.with_suffix(".etapa1.wav")
    corte = ("highpass=f=80,afftdn=nf=-25,"
             "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.15,"
             "areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.3,areverse")
    rodar(["ffmpeg", "-nostdin", "-y", "-v", "error", "-i", str(origem), "-af", corte, "-ac", "1", "-ar", "44100", str(meio)],
          timeout=600)
    dinamica = "acompressor=threshold=-20dB:ratio=3:attack=10:release=200,loudnorm=I=-16:TP=-1.5:LRA=11"
    rodar(["ffmpeg", "-nostdin", "-y", "-v", "error", "-i", str(meio), "-af", dinamica, "-ac", "1", "-ar", "44100", str(destino)],
          timeout=600)
    meio.unlink(missing_ok=True)
    return destino


def _norm(p: str) -> str:
    p = unicodedata.normalize("NFD", p.lower())
    p = "".join(ch for ch in p if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z0-9]", "", p)


def transcrever(audio: Path) -> list[dict]:
    """[{palavra, inicio, fim}] — vazio se o faster-whisper não estiver disponível."""
    global _modelo
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        log.warning("faster-whisper não instalado — cenas divididas por proporção de texto")
        return []
    if _modelo is None:
        _modelo = WhisperModel("small", device="cpu", compute_type="int8")
    segs, _ = _modelo.transcribe(str(audio), language="pt", word_timestamps=True, vad_filter=True)
    return [{"palavra": w.word.strip(), "inicio": w.start, "fim": w.end} for s in segs for w in (s.words or [])]


def fronteiras(textos_cenas: list[str], palavras: list[dict], duracao: float) -> list[float]:
    """Tempo de início de cada cena dentro do bloco."""
    n = len(textos_cenas)
    tokens, dono = [], []
    for i, t in enumerate(textos_cenas):
        for p in t.split():
            if _norm(p):
                tokens.append(_norm(p))
                dono.append(i)
    ouvidas = [_norm(w["palavra"]) for w in palavras]
    inicios = [0.0] * n
    if palavras and tokens:
        mapa = {}
        sm = difflib.SequenceMatcher(None, tokens, ouvidas, autojunk=False)
        for bloco in sm.get_matching_blocks():
            for k in range(bloco.size):
                mapa[bloco.a + k] = bloco.b + k
        qualidade = len(mapa) / len(tokens)
        if qualidade >= 0.5:
            for cena in range(1, n):
                primeiro = dono.index(cena) if cena in dono else None
                if primeiro is None:
                    continue
                # primeira palavra da cena que foi reconhecida
                j = next((mapa[k] for k in range(primeiro, len(tokens)) if k in mapa and dono[k] == cena), None)
                if j is None:
                    continue
                anterior_fim = palavras[j - 1]["fim"] if j > 0 else 0.0
                inicios[cena] = round((anterior_fim + palavras[j]["inicio"]) / 2, 3)
            if all(inicios[i] < inicios[i + 1] for i in range(n - 1)):
                return inicios
            log.warning("alinhamento fora de ordem — usando proporção de texto")
        else:
            log.warning("transcrição muito diferente do roteiro (%.0f%%) — usando proporção de texto", qualidade * 100)
    # reserva: proporcional ao tamanho do texto
    tam = [max(1, len(t)) for t in textos_cenas]
    acum = 0.0
    for i in range(n):
        inicios[i] = round(duracao * acum / sum(tam), 3)
        acum += tam[i]
    return inicios


def cortar(audio: Path, inicio: float, fim: float, destino: Path) -> Path:
    rodar(["ffmpeg", "-y", "-v", "error", "-i", str(audio), "-ss", f"{inicio:.3f}", "-to", f"{fim:.3f}",
           "-af", "afade=t=in:d=0.03", "-ac", "1", "-ar", "44100", str(destino)])
    return destino


def preparar_bloco(pasta: Path, n_bloco: int, textos_cenas: list[str], tmp: Path):
    """Devolve ([audio_por_cena], [palavras com tempo relativo ao bloco])."""
    origem = arquivo_bloco(pasta, n_bloco)
    if not origem:
        raise SystemExit(f"Falta o áudio do bloco {n_bloco}. Grave pelo Telegram respondendo à mensagem do bloco.")
    limpo = limpar_audio(origem, tmp / f"bloco_{n_bloco:02d}_limpo.wav")
    dur = duracao_audio(limpo)
    palavras = transcrever(limpo)
    ini = fronteiras(textos_cenas, palavras, dur) + [dur]
    audios = [cortar(limpo, ini[i], ini[i + 1], tmp / f"voz_b{n_bloco:02d}_c{i + 1:02d}.wav") for i in range(len(textos_cenas))]
    log.info("bloco %d: %.1fs, %d palavras reconhecidas", n_bloco, dur, len(palavras))
    return audios, palavras, ini


def srt_das_palavras(palavras_globais: list[dict]) -> str:
    """Legendas com o que foi realmente falado (até ~80 caracteres por legenda)."""
    from .legendas import _duas_linhas, _hms
    out, atual, i = [], [], 1

    def fechar():
        nonlocal i, atual
        if atual:
            texto = " ".join(w["palavra"] for w in atual).strip()
            out.append(f"{i}\n{_hms(atual[0]['inicio'])} --> {_hms(atual[-1]['fim'])}\n{_duas_linhas(texto)}\n")
            i += 1
            atual = []

    for w in palavras_globais:
        if atual and (len(" ".join(x["palavra"] for x in atual)) + len(w["palavra"]) > 80
                      or w["inicio"] - atual[-1]["fim"] > 0.8):
            fechar()
        atual.append(w)
        if w["palavra"].endswith((".", "?", "!")) and len(" ".join(x["palavra"] for x in atual)) > 30:
            fechar()
    fechar()
    return "\n".join(out)
