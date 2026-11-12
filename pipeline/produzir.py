"""Produz o vídeo inteiro a partir do producao.json: voz, visuais, render, legenda, thumb e upload.

Uso:
  python -m pipeline.produzir canais/historia/videos/2026-10-25-sal-roma
  python -m pipeline.produzir <pasta> --sem-upload                 # só gera os arquivos
  python -m pipeline.produzir <pasta> --sem-upload --voz teste --sem-rede   # teste offline
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from . import animar, apresentador, cartoes, engajamento, gravacao, legendas, quadro_branco, render
from .agenda import proximo_horario
from .comum import FPS, RAIZ, carregar_config, carregar_producao, duracao_audio, log
from .imagens import Buscador
from .imagens_ia import Ilustrador
from .validar import validar
from .voz import narrar

QUADROS_ANIMACAO = 18  # 0,6 s para cada ramo novo do mapa mental (modo ilustrado)


class Contexto:
    def __init__(self, cfg, pasta, tmp, sem_rede):
        self.cfg, self.tmp, self.pasta = cfg, tmp, pasta
        self.branco = cfg["estilo"].get("modo") == "quadro_branco"
        self.buscador = None if sem_rede else Buscador(pasta / "saida", cfg["imagens"]["fontes"])
        self.ilustrador = None if sem_rede else Ilustrador(pasta / "saida", cfg)
        self.animado = bool(cfg["estilo"].get("animado")) and not self.branco
        self.animador = animar.Animador()

    def animar(self, cena: dict, audio: Path, dur: float, saida: Path) -> Path | None:
        """Cena animada em código; None se o render de animação não estiver disponível (o motor usa o plano B)."""
        try:
            return animar.clipe(self.animador, cena, audio, dur, saida, self.tmp)
        except Exception as e:
            log.warning("animação indisponível nesta cena (%s) — usando a versão parada", e)
            return None

    def imagem(self, descricao_ia: str | None, busca: str | None, estilo: str | None = None) -> Path | None:
        if descricao_ia and self.ilustrador:
            p = self.ilustrador.gerar(descricao_ia, estilo)
            if p:
                return p
        if self.buscador and (busca or descricao_ia):
            p = self.buscador.buscar(busca or descricao_ia)
            if p:
                return p
        if busca and self.ilustrador and not descricao_ia:
            # nenhuma imagem livre: em vez de um quadro só com texto, ilustra o assunto
            return self.ilustrador.gerar(busca)
        return None


def _desenhar(ctx: Contexto, depois, antes, idx, audio, dur) -> Path:
    pasta_q = ctx.tmp / f"desenho_{idx:03d}"
    n = quadro_branco.animar(depois, pasta_q, ctx.cfg["estilo"]["fundo"], antes, segundos=min(2.5, max(0.8, dur * 0.45)))
    return render.clipe_quadros(str(pasta_q / "q%03d.png"), n, audio, dur, ctx.tmp / f"cena_{idx:03d}.mp4")


def _visual(ctx: Contexto, cena: dict, idx: int, audio: Path, dur: float, bloco: str) -> Path:
    cfg, tmp = ctx.cfg, ctx.tmp
    v = cena["visual"]
    t = v["tipo"]
    saida = tmp / f"cena_{idx:03d}.mp4"
    movimento = v.get("movimento") or "zoom_in"

    if t in ("imagem", "ilustracao"):
        fixa = ctx.pasta / "imagens-fixas" / f"cena_{idx:03d}.jpg"   # imagem escolhida de uma versão anterior
        origem = fixa if fixa.exists() else ctx.imagem(v.get("cena") if t == "ilustracao" else None,
                                                       v.get("busca_reserva") if t == "ilustracao" else v["busca"])
        if origem:
            if ctx.branco:
                return _desenhar(ctx, quadro_branco.preparar_desenho(origem, cfg["estilo"]["fundo"]), None, idx, audio, dur)
            img = cartoes.preparar_imagem(origem, tmp / f"cena_{idx:03d}.jpg",
                                          preencher=origem.parent.name in ("ilustracoes", "imagens-fixas"))
            if ctx.animado:
                vv = dict(v)
                if vv.get("legenda") and not vv.get("titulo_inferior") and origem.parent.name != "imagens-fixas":
                    vv["titulo_inferior"] = {"titulo": vv["legenda"], "pequeno": True, "em": 0.08}
                if animar.tem_extras(vv):
                    feito = ctx.animar(animar.cena_de(vv, img), audio, dur, saida)
                    if feito:
                        return feito
            # imagem fixa tirada de uma versão anterior já traz a legenda gravada
            sobre = cartoes.sobreposicao_legenda(cfg, v["legenda"], tmp / f"leg_{idx:03d}.png") \
                if v.get("legenda") and origem.parent.name != "imagens-fixas" else None
            return render.clipe_imagem(img, audio, dur, saida, movimento, sobre, textura=ctx.animado)
        # sem imagem: nada de repetir o nome do capítulo na tela
        if ctx.branco:
            quadro = cartoes.fundo(cfg)                      # quadro branco limpo
        elif v.get("legenda"):
            quadro = cartoes.cartao(cfg, v["legenda"], "")
        else:
            quadro = cartoes.fundo(cfg)
    elif t == "cartao":
        quadro = cartoes.cartao(cfg, v["titulo"], v.get("subtitulo", ""))
    elif t == "numero":
        cont = animar.numero_para_contador(v) if ctx.animado else None
        feito = ctx.animar(animar.cena_de(cont), audio, dur, saida) if cont else None
        if feito:
            return feito
        quadro = cartoes.numero(cfg, str(v["valor"]), v.get("rotulo", ""))
    elif t in animar.MODELOS:
        feito = ctx.animar(animar.cena_de(v), audio, dur, saida)
        if feito:
            return feito
        quadro = _plano_b(cfg, v)
    elif t == "citacao":
        quadro = cartoes.citacao(cfg, v["texto"], v.get("autor", ""))
    elif t == "lista":
        quadro = cartoes.lista(cfg, v["titulo"], v["itens"])
    elif t == "comparacao":
        quadro = cartoes.comparacao(cfg, v["esquerda"], v["direita"])
    elif t == "mapa_mental":
        revelar = int(v["revelar"])
        if ctx.branco:
            antes = cartoes.mapa_mental(cfg, v["mapa"], revelar - 1) if revelar > 0 else None
            return _desenhar(ctx, cartoes.mapa_mental(cfg, v["mapa"], revelar), antes, idx, audio, dur)
        pasta_q = tmp / f"mapa_{idx:03d}"
        pasta_q.mkdir(exist_ok=True)
        n = QUADROS_ANIMACAO if revelar > 0 else 1
        for q in range(n):
            prog = 1.0 if n == 1 else ((q + 1) / n) ** 0.6
            cartoes.mapa_mental(cfg, v["mapa"], revelar, prog).save(pasta_q / f"q{q:03d}.png")
        return render.clipe_quadros(str(pasta_q / "q%03d.png"), n, audio, dur, saida)
    else:
        raise ValueError(f"visual desconhecido: {t}")
    if ctx.branco:
        return _desenhar(ctx, quadro, None, idx, audio, dur)
    png = tmp / f"cena_{idx:03d}.png"
    quadro.save(png)
    return render.clipe_estatico(png, audio, dur, saida)


def _plano_b(cfg: dict, v: dict):
    """Cena animada que não pôde ser renderizada: vira um cartão parado com a mesma informação."""
    t = v["tipo"]
    if t == "contador":
        return cartoes.numero(cfg, f"{v.get('prefixo', '')}{v['ate']:,.0f}{v.get('sufixo', '')}".replace(",", "."), v.get("rotulo", ""))
    if t == "linha_tempo" and v.get("eventos"):
        e = v["eventos"][min(int(v.get("foco", len(v["eventos"]) - 1)), len(v["eventos"]) - 1)]
        return cartoes.cartao(cfg, str(e.get("ano", "")), e.get("texto", ""))
    ti = v.get("titulo_inferior") or {}
    rot = [p.get("rotulo") for p in v.get("paises", []) + v.get("areas", []) if p.get("rotulo")]
    return cartoes.cartao(cfg, ti.get("titulo") or (rot[0] if rot else ""), ti.get("subtitulo", ""))


def _baixar_audios(pasta: Path, total: int) -> None:
    """Áudios que chegaram pelo Telegram: baixa os que ainda não estão na pasta."""
    for n in range(1, total + 1):
        meta = pasta / "audio" / f"bloco_{n:02d}.json"
        if meta.exists() and not gravacao.arquivo_bloco(pasta, n):
            from . import telegram
            telegram.baixar(json.loads(meta.read_text(encoding="utf-8"))["file_id"], pasta / "audio" / f"bloco_{n:02d}.ogg")


def _horario(pasta: Path, cfg: dict) -> str:
    """Usa o horário da rotina guardado no estado; se já passou (ou está perto demais), pega o próximo livre."""
    arq = pasta / "estado.json"
    if arq.exists():
        alvo = json.loads(arq.read_text(encoding="utf-8")).get("publicar_em_utc")
        if alvo:
            quando = datetime.fromisoformat(alvo.replace("Z", "+00:00"))
            if (quando - datetime.now(timezone.utc)).total_seconds() > 1800:
                return alvo
    return proximo_horario(cfg, folga_horas=1)


def produzir(pasta: Path, sem_upload=False, motor_voz=None, sem_rede=False) -> dict:
    prod = carregar_producao(pasta)
    erros = validar(prod)
    if erros:
        raise SystemExit("producao.json inválido:\n- " + "\n- ".join(erros))
    cfg = carregar_config(prod["canal"])
    motor = motor_voz or os.environ.get("MOTOR_VOZ") or cfg["voz"]["motor"]
    if isinstance(motor, list) and motor == ["gravada"]:
        motor = "gravada"
    tmp = pasta / "saida" / "tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    ctx = Contexto(cfg, pasta, tmp, sem_rede)
    if motor != "gravada":
        lista = motor if isinstance(motor, list) else [m.strip() for m in str(motor).split(",")]
        if "gemini" in lista:
            try:
                from .gemini_voz import narrar_blocos
                narrar_blocos(pasta, prod, cfg)
                motor = "gravada"
                narrador = "gemini"
            except Exception as e:
                log.warning("narrador Gemini indisponível (%s) — usando o próximo da lista", e)
                lista = [m for m in lista if m != "gemini"]
                if not lista:
                    raise SystemExit(f"Narrador Gemini indisponível ({e}) e não há voz reserva permitida.")
        if motor != "gravada":
            from .voz import escolher_motor
            motor = escolher_motor(cfg, tmp, lista)
            narrador = motor
    else:
        narrador = "Miguel"

    ja = pasta / "publicacao.json"
    if not sem_upload and ja.exists() and json.loads(ja.read_text(encoding="utf-8")).get("video_id"):
        log.info("vídeo já publicado (%s) — nada a fazer", ja)
        return json.loads(ja.read_text(encoding="utf-8"))

    if motor == "gravada":
        _baixar_audios(pasta, len(prod["blocos"]))
        faltam = gravacao.blocos_faltando(pasta, len(prod["blocos"]))
        if faltam:
            raise SystemExit(f"Faltam os áudios dos blocos {faltam}. Grave pelo Telegram.")

    if ctx.ilustrador:
        todas = [c for b in prod["blocos"] for c in b["cenas"]]
        pedidos = [c["visual"].get("cena") for i, c in enumerate(todas, 1) if c["visual"]["tipo"] == "ilustracao"
                   and not (pasta / "imagens-fixas" / f"cena_{i:03d}.jpg").exists()]
        ctx.ilustrador.pre_gerar(pedidos + [prod["thumbnail"].get("cena")])
        # trava: sem os desenhos, o vídeo não sobe — espera a cota de imagens voltar (o que já foi feito fica guardado)
        faltam = [d for d in pedidos if d and not ctx.ilustrador._destino(d).exists()]
        if prod["thumbnail"].get("cena") and not ctx.ilustrador._destino(prod["thumbnail"]["cena"]).exists() \
                and not (pasta / "thumbnail-fixa.jpg").exists():
            faltam.append("thumbnail")   # a thumbnail também espera o desenho
        if pedidos and len(faltam) / len(pedidos) > 0.25 and not sem_upload and not os.environ.get("FORCAR_SEM_IMAGEM"):
            quando = json.loads((pasta / "estado.json").read_text(encoding="utf-8")).get("publicar_em_utc") \
                if (pasta / "estado.json").exists() else None
            perto = quando and (datetime.fromisoformat(quando.replace("Z", "+00:00")) - datetime.now(timezone.utc)).total_seconds() < 8 * 3600
            if not perto:
                from . import estado as E
                E.salvar_estado(pasta, etapa="aguardando_cota")
                feitas = len(pedidos) - len(faltam)
                try:
                    from . import telegram as T
                    T.enviar(f"🎨 {T.esc(cfg['nome'])}: a cota grátis de imagens acabou ({feitas} de {len(pedidos)} desenhos prontos). "
                             "Guardei o que já foi feito e tento de novo sozinho mais tarde; o vídeo só sobe com os desenhos.")
                except Exception:
                    pass
                log.warning("cota de imagens: %d de %d desenhos prontos — montagem adiada", feitas, len(pedidos))
                raise SystemExit(0)
            log.warning("faltam %d desenhos, mas o vídeo sai em menos de 8 h — seguindo com imagens livres", len(faltam))

    clipes, tempos_cenas, tempos_blocos, palavras_globais, t, idx = [], [], [], [], 0.0, 0
    for nb, b in enumerate(prod["blocos"], 1):
        tempos_blocos.append({"inicio": t, "capitulo": b.get("capitulo", "")})
        textos = [c["narracao"] for c in b["cenas"]]
        audios_gravados = None
        if motor == "gravada":
            audios_gravados, palavras, inicios = gravacao.preparar_bloco(pasta, nb, textos, tmp)
        inicio_bloco = t
        for nc, c in enumerate(b["cenas"]):
            idx += 1
            audio = audios_gravados[nc] if audios_gravados else narrar(c["narracao"], cfg, tmp / f"voz_{idx:03d}.wav", motor)
            dur = round(duracao_audio(audio) + (0.0 if audios_gravados else 0.15), 3)
            dur = max(1.0, round(dur * FPS) / FPS)
            clipe = _visual(ctx, c, idx, audio, dur, b.get("capitulo", ""))
            if engajamento.eh_chamada(c["narracao"]):   # arte "Inscreva-se · Gostei · Comente" durante a chamada
                png = tmp / "chamada.png"
                if not png.exists():
                    engajamento.arte(cfg).save(png)
                clipe = engajamento.aplicar(clipe, png, 0.3, max(1.5, dur - 0.5), tmp / f"cena_{idx:03d}_cta.mp4")
            clipes.append(clipe)
            tempos_cenas.append({"inicio": t, "duracao": dur, "narracao": c["narracao"], "bloco": nb, "cena": nc + 1})
            t += dur
            log.info("cena %d pronta (%.1fs, total %.0fs)", idx, dur, t)
        if audios_gravados:
            # palavras com tempo global (os cortes são contíguos, então o deslocamento é o início do bloco)
            palavras_globais += [{**w, "inicio": w["inicio"] + inicio_bloco, "fim": w["fim"] + inicio_bloco} for w in palavras]

    ctx.animador.fechar()
    saida = pasta / "saida"
    bruto = render.concatenar(clipes, tmp / "narrado.mp4")
    try:
        bruto = apresentador.sobrepor(bruto, cfg, tmp, tmp / "narrado_webcam.mp4")
    except Exception as e:  # o vídeo sai sem a webcam, mas sai
        log.warning("não consegui pôr o apresentador na webcam: %s", e)
    musica = render.escolher_musica(prod.get("musica_humor") or cfg["video"].get("musica_humor"), pasta.name)
    video = render.mixar_trilha(bruto, musica, cfg["video"]["volume_musica_db"], saida / "video.mp4")

    srt = saida / "legendas.srt"
    srt.write_text(gravacao.srt_das_palavras(palavras_globais) if palavras_globais else legendas.gerar_srt(tempos_cenas),
                   encoding="utf-8")

    th = prod["thumbnail"]
    fixa = pasta / "thumbnail-fixa.jpg"   # thumbnail escolhida pelo Miguel: usada como está
    if fixa.exists():
        import shutil
        thumb = Path(shutil.copy(fixa, saida / "thumbnail.jpg"))
    else:
        img_thumb = ctx.imagem(th.get("cena"), th.get("imagem_busca"), (cfg.get("thumbnail") or {}).get("estilo_imagem"))
        if not img_thumb:   # thumbnail nunca sai sem imagem: usa a melhor ilustração do próprio vídeo
            ilus = sorted((pasta / "saida" / "ilustracoes").glob("*.img"), key=lambda a: -a.stat().st_size) \
                if (pasta / "saida" / "ilustracoes").exists() else []
            img_thumb = ilus[0] if ilus else None
            log.warning("thumbnail sem a imagem planejada — usando %s", img_thumb.name if img_thumb else "só o fundo")
        thumb = cartoes.thumbnail(cfg, th["texto"], img_thumb, th.get("layout") or (cfg.get("thumbnail") or {}).get("layout", "direita"),
                                  saida / "thumbnail.jpg")

    partes = [prod["descricao"].strip()]
    caps = legendas.capitulos(tempos_blocos)
    if caps:
        partes.append("Capítulos:\n" + caps)
    creditos = ctx.buscador.creditos if ctx.buscador else []
    if creditos:
        partes.append("Créditos das imagens:\n" + "\n".join(f"- {c}" for c in creditos))
    if ctx.ilustrador and ctx.ilustrador.gerados:
        partes.append("Ilustrações criadas com auxílio de IA.")
    if musica:
        partes.append(f"Trilha: {musica.stem}")
    if narrador != "Miguel":
        partes.append("Narração com voz gerada por IA.")
    if prod.get("hashtags"):
        partes.append(" ".join(prod["hashtags"][:3]))
    descricao = "\n\n".join(partes)[:5000]

    pub = {
        "titulo": prod["titulo"], "descricao": descricao, "tags": prod["tags"],
        "playlist": prod.get("playlist") or cfg["youtube"].get("playlist_padrao") or "",
        "comentario_inicial": prod.get("comentario_inicial", ""),
        "sintetico_realista": prod.get("sintetico_realista", False),
        "duracao_s": round(t, 1), "cenas": idx,
        "ilustracoes_ia": ctx.ilustrador.gerados if ctx.ilustrador else 0,
        "narrador": narrador,
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    if not sem_upload:
        from .youtube import publicar
        pub["publicar_em_utc"] = _horario(pasta, cfg)
        pub["video_id"] = publicar(cfg, pub, video, thumb, srt)
        pub["url"] = f"https://youtu.be/{pub['video_id']}"
    (saida / "tempos.json").write_text(json.dumps({"cenas": tempos_cenas, "palavras": palavras_globais}), encoding="utf-8")
    try:
        from .cortes import produzir_cortes
        pub["cortes"] = produzir_cortes(pasta, cfg, video, tempos_cenas, palavras_globais, tmp, pub, enviar=not sem_upload)
    except Exception as e:
        log.warning("cortes verticais falharam: %s", e)
    (pasta / "publicacao.json").write_text(json.dumps(pub, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("PRONTO: %s (%.1f min)%s", video, t / 60, f" → {pub.get('url')}" if pub.get("url") else "")
    return pub


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pasta", type=Path)
    ap.add_argument("--sem-upload", action="store_true")
    ap.add_argument("--voz", dest="motor_voz", default=None, help="gravada | kokoro | edge | openai | teste")
    ap.add_argument("--sem-rede", action="store_true", help="não busca nem gera imagens (usa cartões)")
    a = ap.parse_args()
    pasta = a.pasta if a.pasta.is_absolute() else (RAIZ / a.pasta)
    produzir(pasta, a.sem_upload, a.motor_voz, a.sem_rede)


if __name__ == "__main__":
    main()
