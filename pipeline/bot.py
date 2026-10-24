"""O "recepcionista" do escritório: conversa com o Miguel pelo Telegram e decide o próximo passo.

Subcomandos (usados pelos workflows do GitHub):
  planejar [--canal C] [--dias N]   cria as pastas dos próximos vídeos da rotina
  enviar-pautas PASTA...            manda as 3 pautas de cada vídeo
  receber                           trata uma mensagem do Telegram (evento do GitHub)
  enviar-roteiro PASTA              manda o roteiro para aprovação
  enviar-blocos PASTA               manda os blocos para gravar
  produzido PASTA                   avisa que o vídeo foi agendado
  erro TEXTO                        avisa que algo falhou
  status                            resumo da semana
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

from . import estado as E
from . import telegram as T
from .comum import RAIZ, log

esc = T.esc


def _saida(**kv) -> None:
    """Escreve variáveis para os próximos passos do workflow (GITHUB_OUTPUT)."""
    arq = os.environ.get("GITHUB_OUTPUT")
    for k, v in kv.items():
        log.info("saída %s=%s", k, v)
        if arq:
            with open(arq, "a", encoding="utf-8") as f:
                f.write(f"{k}={v}\n")


def _pasta(arg: str) -> Path:
    p = Path(arg)
    return p if p.is_absolute() else RAIZ / p


def _cabecalho(pasta: Path) -> str:
    e = E.ler_estado(pasta)
    return f"<b>{esc(E.nome_canal(e['canal']))}</b> · {esc(e.get('rotulo', pasta.name))}"


# ---------------------------------------------------------------- planejamento
def planejar(canal: str | None = None, dias: int = 4) -> list[Path]:
    slots = [s for s in E.proximos_slots(dias) if not canal or s["canal"] == canal]
    if canal and not slots:  # pedido manual: pega o próximo dia livre desse canal
        slots = [s for s in E.proximos_slots(21) if s["canal"] == canal][:1]
    pastas = []
    for s in slots:
        E.salvar_estado(s["pasta"], canal=s["canal"], dia=s["dia"], rotulo=s["rotulo"],
                        publicar_em_utc=s["publicar_em_utc"], etapa="pauta")
        pastas.append(s["pasta"])
    _saida(pastas=" ".join(E.rel(p) for p in pastas))
    if pastas:
        T.enviar("🔎 <b>Pesquisando pautas</b> para:\n" + "\n".join(
            f"• {esc(E.nome_canal(E.ler_estado(p)['canal']))} — {esc(E.ler_estado(p)['rotulo'])}" for p in pastas))
    return pastas


def enviar_pautas(pastas: list[Path]) -> None:
    for pasta in pastas:
        arq = pasta / "pautas.json"
        if not arq.exists():
            E.salvar_estado(pasta, etapa="erro", erro="pautas.json não foi gerado")
            T.enviar(f"⚠️ {_cabecalho(pasta)}\nO pesquisador não entregou as pautas. Mande /pauta {E.ler_estado(pasta)['canal']} para tentar de novo.")
            continue
        ideias = json.loads(arq.read_text(encoding="utf-8"))
        linhas = [f"🗂️ {_cabecalho(pasta)}\n<b>Escolha a pauta:</b>\n"]
        for i, it in enumerate(ideias[:3], 1):
            linhas.append(f"<b>{i}. {esc(it.get('titulo', ''))}</b>\n"
                          f"🎯 {esc(it.get('angulo', ''))}\n"
                          f"📈 {esc(it.get('porque', ''))}\n")
        linhas.append("↩️ <i>Responda esta mensagem com 1, 2 ou 3 — e, se quiser, sua opinião ou ângulo "
                      "(ex.: \"2, foca no imposto do sal\"). \"outras\" pede novas ideias.</i>")
        ids = T.enviar("\n".join(linhas))
        E.registrar_msgs(ids, pasta, "pauta")
        E.salvar_estado(pasta, etapa="aguardando_escolha")


def enviar_roteiro(pasta: Path) -> None:
    rj = json.loads((pasta / "roteiro.json").read_text(encoding="utf-8"))
    palavras = sum(len(b["texto"].split()) for b in rj["blocos"])
    topo = (f"📜 {_cabecalho(pasta)}\n<b>{esc(rj.get('titulo_provisorio', ''))}</b>\n\n"
            f"💡 <b>Tese:</b> {esc(rj.get('tese', ''))}\n"
            f"⏱️ ~{palavras / 150:.0f} min · {len(rj['blocos'])} blocos para gravar\n"
            f"🔍 <b>Checagem:</b> {esc(rj.get('resumo_checagem', 'ok'))}\n"
            f"🛡️ <b>Originalidade:</b> {esc(rj.get('semaforo', ''))} {esc(rj.get('resumo_originalidade', ''))}")
    if rj.get("pergunta_para_miguel"):
        topo += f"\n\n🗣️ <b>Sua opinião deixa o vídeo mais forte:</b> {esc(rj['pergunta_para_miguel'])}"
    ids = T.enviar(topo)
    corpo = "\n\n".join(f"<b>{i}. {esc(b.get('capitulo', ''))}</b>\n{esc(b['texto'])}" for i, b in enumerate(rj["blocos"], 1))
    ids += T.enviar(corpo)
    ids += T.enviar("↩️ <i>Responda <b>aprovar</b> — ou escreva o que mudar (ex.: \"deixa o gancho mais "
                    "engraçado e tira a parte do Egito\").</i>")
    E.registrar_msgs(ids, pasta, "roteiro")
    E.salvar_estado(pasta, etapa="aguardando_aprovacao")


def _narra_sozinho(pasta: Path) -> bool:
    from .comum import carregar_config
    m = carregar_config(E.ler_estado(pasta)["canal"])["voz"]["motor"]
    return m != "gravada" and m != ["gravada"]


def enviar_blocos(pasta: Path) -> None:
    prod = json.loads((pasta / "producao.json").read_text(encoding="utf-8"))
    if _narra_sozinho(pasta):
        E.salvar_estado(pasta, etapa="renderizando", titulo=prod["titulo"])
        T.enviar(f"🎬 {_cabecalho(pasta)}\n<b>{esc(prod['titulo'])}</b>\n\nO narrador de IA está gravando e o vídeo "
                 "está sendo montado (uns 30–60 min). Te mando a thumbnail e o link quando estiver agendado.")
        _saida(produzir=E.rel(pasta))
        return
    total = len(prod["blocos"])
    T.enviar(f"🎙️ {_cabecalho(pasta)}\n<b>{esc(prod['titulo'])}</b>\n\nHora de gravar! São {total} blocos. "
             "Responda <b>cada mensagem</b> com um áudio lendo aquele bloco. Errou? Mande de novo — vale o último. "
             "Grave em lugar silencioso, com o celular a um palmo da boca.")
    for i, b in enumerate(prod["blocos"], 1):
        texto = " ".join(c["narracao"] for c in b["cenas"])
        ids = T.enviar(f"🎙️ <b>Bloco {i}/{total} — {esc(b.get('capitulo', ''))}</b>\n\n{esc(texto)}")
        E.registrar_msgs(ids[:1], pasta, "bloco", bloco=i)
    E.salvar_estado(pasta, etapa="aguardando_audio")


def produzido(pasta: Path) -> None:
    pub = json.loads((pasta / "publicacao.json").read_text(encoding="utf-8"))
    E.salvar_estado(pasta, etapa="agendado", url=pub.get("url"))
    from datetime import datetime
    quando = datetime.fromisoformat(pub["publicar_em_utc"].replace("Z", "+00:00")).astimezone(E.BRT)
    texto = (f"✅ {_cabecalho(pasta)}\n<b>{esc(pub['titulo'])}</b>\n"
             f"📅 Publica {E.NOMES_DIA[quando.weekday()]} {quando:%d/%m às %Hh%M}\n"
             f"⏱️ {pub['duracao_s'] / 60:.1f} min · {pub['cenas']} cenas · {pub.get('ilustracoes_ia', 0)} ilustrações\n"
             f"🔗 {pub.get('url', '')}")
    cortes = [c for c in pub.get("cortes", []) if c.get("url")]
    if cortes:
        texto += f"\n📱 {len(cortes)} Shorts agendados (1 por dia, 12h) — os arquivos para Reels/TikTok chegam aqui"
    for a in pub.get("avisos", []):
        texto += f"\n⚠️ {esc(a)}"
    thumb = pasta / "saida" / "thumbnail.jpg"
    if thumb.exists():
        T.enviar_foto(thumb, texto)
    else:
        T.enviar(texto)


def status() -> str:
    linhas = ["📋 <b>Escritório — próximos vídeos</b>\n"]
    for pasta, e in E.todos_videos():
        if e.get("etapa") == "agendado" and e.get("publicar_em_utc", "") < _agora_utc():
            continue
        titulo = e.get("titulo") or ""
        extra = ""
        if e.get("etapa") == "aguardando_audio":
            extra = f" ({len(E.blocos_com_audio(pasta))}/{E.total_blocos(pasta)} áudios)"
        linhas.append(f"• <b>{esc(e.get('rotulo', pasta.name))}</b> — {esc(E.nome_canal(e['canal']))}\n"
                      f"   {E.ETAPAS.get(e.get('etapa'), e.get('etapa'))}{extra}" + (f"\n   <i>{esc(titulo)}</i>" if titulo else ""))
    if len(linhas) == 1:
        linhas.append("Nada na fila. Mande /pauta historia (ou vestibular, livros) para começar um vídeo.")
    return "\n".join(linhas)


def _agora_utc() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


AJUDA = ("🤖 <b>Comandos</b>\n"
         "/status — o que está em produção\n"
         "/pauta historia | vestibular | livros — começa um vídeo extra agora\n"
         "/lote — pede as pautas dos próximos dias da rotina\n"
         "/vozes — ouvir as vozes do narrador de IA\n"
         "/narrar — o narrador de IA grava um vídeo que estava esperando seus áudios\n"
         "/ajuda — esta mensagem\n\n"
         "No dia a dia é só <b>responder</b> às mensagens: número da pauta, \"aprovar\" no roteiro e áudio em cada bloco.")


# ---------------------------------------------------------------- receber
APROVAR = re.compile(r"^\s*(aprov|ok\b|pode\b|manda\b|bora\b|perfeito|👍|✅)", re.I)


def _proximo_bloco_pendente() -> tuple[Path, int] | None:
    for pasta, e in E.todos_videos():
        if e.get("etapa") == "aguardando_audio":
            falta = sorted(set(range(1, E.total_blocos(pasta) + 1)) - E.blocos_com_audio(pasta))
            if falta:
                return pasta, falta[0]
    return None


def _checar_completo(pasta: Path) -> None:
    total = E.total_blocos(pasta)
    tem = E.blocos_com_audio(pasta)
    if total and len(tem) >= total and E.ler_estado(pasta).get("etapa") == "aguardando_audio":
        E.salvar_estado(pasta, etapa="renderizando")
        T.enviar(f"🎬 {_cabecalho(pasta)}\nTodos os {total} áudios recebidos! Montando o vídeo — aviso quando estiver agendado.")
        _saida(produzir=E.rel(pasta))


def receber(evento: dict) -> None:
    if (evento.get("inputs") or {}).get("comando"):  # disparo manual pelo GitHub
        evento = {"message": {"chat": {"id": T.chat_id()}, "message_id": 0, "text": evento["inputs"]["comando"]}}
    upd = (evento.get("client_payload") or {}).get("update") or evento
    msg = upd.get("message") or {}
    if not msg:
        return
    if str(msg.get("chat", {}).get("id")) != str(T.chat_id()):
        log.warning("mensagem de chat desconhecido ignorada")
        return
    texto = (msg.get("text") or msg.get("caption") or "").strip()
    resp = (msg.get("reply_to_message") or {}).get("message_id")
    info = E.msg_info(resp) if resp else None
    audio = msg.get("voice") or msg.get("audio")
    if not audio and (msg.get("document") or {}).get("mime_type", "").startswith("audio/"):
        audio = msg["document"]

    # ---- comandos
    if texto.startswith("/"):
        cmd, *args = texto.split()
        cmd = cmd.split("@")[0].lower()
        if cmd in ("/start", "/ajuda", "/help"):
            T.enviar(f"👋 Seu chat é o <code>{esc(str(msg['chat']['id']))}</code>.\n\n" + AJUDA)
        elif cmd == "/status":
            T.enviar(status())
        elif cmd == "/pauta":
            canal = (args[0].lower() if args else "")
            canal = {"história": "historia", "pre": "vestibular", "mapeado": "vestibular", "marca": "livros"}.get(canal, canal)
            if canal not in E.CANAIS:
                T.enviar("Qual canal? /pauta historia, /pauta vestibular ou /pauta livros")
                return
            from .comum import carregar_config
            if not carregar_config(canal).get("ativo", True):
                T.enviar(f"⏸️ O canal {esc(E.nome_canal(canal))} está em pausa (ainda não conectado ao YouTube).")
                return
            pastas = planejar(canal)
            if pastas:
                _saida(comando=f"/pautas {' '.join(E.rel(p) for p in pastas)}", pos="enviar-pautas")
        elif cmd == "/narrar":
            alvo = [p for p, e in E.todos_videos() if e.get("etapa") == "aguardando_audio"]
            if not alvo:
                T.enviar("Nenhum vídeo está esperando gravação.")
                return
            for p in alvo:
                E.salvar_estado(p, etapa="renderizando")
                T.enviar(f"🎬 {_cabecalho(p)}\nO narrador de IA assumiu este vídeo. Montando agora (uns 30–60 min).")
            _saida(produzir=E.rel(alvo[0]))
        elif cmd == "/vozes":
            _saida(vozes="sim")
            T.enviar("🎧 Gerando amostras das vozes… chegam aqui em 2–3 minutos.")
        elif cmd == "/lote":
            pastas = planejar()
            if pastas:
                _saida(comando=f"/pautas {' '.join(E.rel(p) for p in pastas)}", pos="enviar-pautas")
            else:
                T.enviar("Os próximos 4 dias da rotina já estão encaminhados. /status mostra a fila.")
        else:
            T.enviar("Não conheço esse comando.\n\n" + AJUDA)
        return

    # ---- áudio
    if audio:
        if info and info.get("tipo") == "bloco":
            pasta, bloco = _pasta(info["pasta"]), int(info["bloco"])
            aviso = ""
        else:
            alvo = _proximo_bloco_pendente()
            if not alvo:
                T.enviar("🎙️ Recebi um áudio, mas não há nenhum bloco esperando gravação.", responder_a=msg["message_id"])
                return
            pasta, bloco = alvo
            aviso = (f"\n<i>Você não respondeu a um bloco, então registrei como Bloco {bloco}. "
                     "Se não for, responda à mensagem do bloco certo.</i>")
        E.registrar_audio(pasta, bloco, audio["file_id"], msg["message_id"], int(audio.get("duration", 0)))
        total = E.total_blocos(pasta)
        tem = E.blocos_com_audio(pasta)
        T.reagir(msg["message_id"], "👍")
        if aviso or len(tem) < total:
            falta = sorted(set(range(1, total + 1)) - tem)
            T.enviar(f"✅ Bloco {bloco} gravado ({len(tem)}/{total})." +
                     (f" Faltam: {', '.join(map(str, falta))}." if falta else "") + aviso, responder_a=msg["message_id"])
        _checar_completo(pasta)
        return

    if not info:
        # sem "responder": se só um vídeo está esperando esse tipo de resposta, é ele
        esperando = {"aguardando_escolha": "pauta", "aguardando_aprovacao": "roteiro"}
        candidatos = [(p, esperando[e.get("etapa")]) for p, e in E.todos_videos() if e.get("etapa") in esperando]
        import json as _json
        for arq in sorted((RAIZ / "canais").glob("*/reels/*/estado.json")):
            if _json.loads(arq.read_text(encoding="utf-8")).get("etapa") == "aguardando_aprovacao_reel":
                candidatos.append((arq.parent, "reel"))
        if re.match(r"^\s*[1-3]\b", texto):
            candidatos = [c for c in candidatos if c[1] == "pauta"]
        elif APROVAR.match(texto):
            candidatos = [c for c in candidatos if c[1] in ("roteiro", "reel")]
        if len(candidatos) == 1:
            info = {"pasta": E.rel(candidatos[0][0]), "tipo": candidatos[0][1]}
        else:
            extra = " Tem mais de um vídeo esperando você." if len(candidatos) > 1 else ""
            T.enviar("Para eu saber de qual vídeo você está falando, <b>responda</b> (segure a mensagem → Responder) "
                     f"a uma mensagem minha.{extra}\n\n" + AJUDA)
            return

    pasta = _pasta(info["pasta"])
    tipo = info["tipo"]
    etapa = E.ler_estado(pasta).get("etapa")

    if tipo == "pauta":
        if etapa not in ("aguardando_escolha", "erro"):
            T.enviar("Essa pauta já foi escolhida. /status mostra em que pé está.", responder_a=msg["message_id"])
            return
        m = re.match(r"^\s*([1-3])\b[\s,.;:-]*(.*)$", texto, re.S)
        if m:
            E.salvar_estado(pasta, etapa="roteiro", ideia=int(m.group(1)), nota_miguel=m.group(2).strip())
            T.enviar(f"✍️ Fechado, ideia {m.group(1)}! Pesquisador e roteirista começaram. "
                     "O roteiro chega aqui já checado (uns 15–25 min).", responder_a=msg["message_id"])
            _saida(comando=f"/roteiro {E.rel(pasta)}", pos="enviar-roteiro", pasta=E.rel(pasta))
        else:
            E.salvar_estado(pasta, etapa="pauta", nota_miguel=texto)
            T.enviar("🔎 Vou buscar outras 3 ideias levando isso em conta.", responder_a=msg["message_id"])
            _saida(comando=f"/pautas {E.rel(pasta)}", pos="enviar-pautas", pasta=E.rel(pasta))
        return

    if tipo == "roteiro":
        if etapa != "aguardando_aprovacao":
            T.enviar(f"Esse roteiro está em: {E.ETAPAS.get(etapa, etapa)}.", responder_a=msg["message_id"])
            return
        if APROVAR.match(texto):
            E.salvar_estado(pasta, etapa="producao_json")
            T.enviar("🎨 Aprovado! Diretor visual, SEO e thumbnail trabalhando. Em seguida mando os blocos para gravar.",
                     responder_a=msg["message_id"])
            _saida(comando=f"/producao {E.rel(pasta)}", pos="enviar-blocos", pasta=E.rel(pasta))
        else:
            ajustes = E.ler_estado(pasta).get("ajustes", [])
            E.salvar_estado(pasta, etapa="ajuste", ajustes=ajustes + [texto])
            T.enviar("✍️ Anotado, o roteirista está ajustando.", responder_a=msg["message_id"])
            _saida(comando=f"/ajustar {E.rel(pasta)}", pos="enviar-roteiro", pasta=E.rel(pasta))
        return

    if tipo == "reel":
        if APROVAR.match(texto):
            T.enviar("📅 Aprovado! Agendando o reel no YouTube Shorts…", responder_a=msg["message_id"])
            _saida(reel_acao="publicar", reel_pasta=E.rel(pasta))
        else:
            ajustes = E.ler_estado(pasta).get("ajustes", [])
            E.salvar_estado(pasta, etapa="ajuste_reel", ajustes=ajustes + [texto])
            T.enviar("🎬 Anotado! Ajustando o reel e renderizando de novo (uns 10 min).", responder_a=msg["message_id"])
            _saida(reel_acao="ajustar", reel_pasta=E.rel(pasta))
        return

    if tipo == "bloco":
        T.enviar("Para este bloco eu preciso de um <b>áudio</b> 🎙️ (segure o microfone e leia o texto).",
                 responder_a=msg["message_id"])


# ---------------------------------------------------------------- rotinas
def lembrar() -> None:
    """Lembra o Miguel do que depende dele (pauta, aprovação, áudios) para vídeos que saem em até 2 dias."""
    from datetime import datetime, timedelta, timezone
    limite = (datetime.now(timezone.utc) + timedelta(hours=48)).strftime("%Y-%m-%dT%H:%M:%SZ")
    pend = []
    for pasta, e in E.todos_videos():
        et = e.get("etapa")
        if et in ("aguardando_escolha", "aguardando_aprovacao", "aguardando_audio", "erro") and e.get("publicar_em_utc", "") <= limite:
            extra = ""
            if et == "aguardando_audio":
                falta = sorted(set(range(1, E.total_blocos(pasta) + 1)) - E.blocos_com_audio(pasta))
                extra = f" — faltam os blocos {', '.join(map(str, falta))}"
            pend.append(f"• <b>{esc(e.get('rotulo', ''))}</b> {esc(E.nome_canal(e['canal']))}: {E.ETAPAS.get(et, et)}{extra}")
    if pend:
        T.enviar("⏰ <b>Precisa de você</b> (vídeos dos próximos 2 dias):\n" + "\n".join(pend) +
                 "\n\n<i>Responda às mensagens de cada vídeo — role o chat para cima ou mande /status.</i>")


def relatorio() -> None:
    arq = RAIZ / "canais" / "relatorio-semana.md"
    if arq.exists():
        T.enviar("📊 <b>Relatório da semana</b>\n\n" + esc(arq.read_text(encoding="utf-8")))


# ---------------------------------------------------------------- CLI
def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "planejar":
        canal = args[args.index("--canal") + 1] if "--canal" in args else None
        dias = int(args[args.index("--dias") + 1]) if "--dias" in args else 4
        planejar(canal, dias)
    elif cmd == "enviar-pautas":
        enviar_pautas([_pasta(a) for a in " ".join(args).split()])
    elif cmd == "receber":
        evento = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8")) if not args else \
            json.loads(Path(args[0]).read_text(encoding="utf-8"))
        receber(evento)
    elif cmd == "enviar-roteiro":
        enviar_roteiro(_pasta(args[0]))
    elif cmd == "enviar-blocos":
        enviar_blocos(_pasta(args[0]))
    elif cmd == "checar-audios":
        _checar_completo(_pasta(args[0]))
    elif cmd == "produzido":
        produzido(_pasta(args[0]))
    elif cmd == "erro":
        pasta = _pasta(args[0]) if args and (RAIZ / args[0]).exists() else None
        if pasta:
            E.salvar_estado(pasta, etapa="erro")
        url = os.environ.get("RUN_URL", "")
        T.enviar(f"⚠️ <b>Algo falhou</b>{(' em ' + _cabecalho(pasta)) if pasta else ''}.\n"
                 f"Detalhes: {esc(url)}\nVou deixar parado aqui; me chame no Claude Code se precisar.")
    elif cmd == "status":
        T.enviar(status())
    elif cmd == "lembrar":
        lembrar()
    elif cmd == "relatorio":
        relatorio()
    elif cmd == "ola":
        T.enviar("🎬 <b>Escritório Dark no ar!</b>\n\n" + AJUDA)
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
