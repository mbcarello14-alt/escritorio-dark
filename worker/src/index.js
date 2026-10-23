// Escritório Dark — recepção instantânea do Telegram + painel do escritório virtual.
// Recebe o webhook do Telegram, reage na hora e repassa a mensagem ao GitHub Actions.
import PAINEL_HTML from "./painel.html";

const ok = () => new Response("ok");

async function tg(env, metodo, corpo) {
  return fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/${metodo}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(corpo),
  });
}

async function despachar(env, update) {
  const r = await fetch(`https://api.github.com/repos/${env.GH_REPO}/dispatches`, {
    method: "POST",
    headers: {
      authorization: `Bearer ${env.GH_PAT}`,
      accept: "application/vnd.github+json",
      "user-agent": "escritorio-dark-worker",
      "content-type": "application/json",
    },
    body: JSON.stringify({ event_type: "telegram", client_payload: { update } }),
  });
  if (!r.ok) {
    const chat = update.message?.chat?.id;
    await tg(env, "sendMessage", {
      chat_id: chat,
      text: `⚠️ Não consegui acordar o escritório no GitHub (${r.status}). Confira o segredo GH_PAT.`,
    });
  }
}

function enxugar(update) {
  // a mensagem respondida pode ser longa; só precisamos do id dela
  const m = update.message;
  if (m?.reply_to_message) m.reply_to_message = { message_id: m.reply_to_message.message_id };
  return update;
}

async function telegram(req, env, ctx) {
  if (req.headers.get("X-Telegram-Bot-Api-Secret-Token") !== env.WEBHOOK_SECRET) {
    return new Response("proibido", { status: 403 });
  }
  const update = await req.json();
  const msg = update.message;
  if (!msg) return ok();
  const chat = String(msg.chat.id);

  if (!env.TELEGRAM_CHAT_ID) {
    // modo de instalação: ainda não sabemos qual é o seu chat
    ctx.waitUntil(tg(env, "sendMessage", {
      chat_id: chat,
      parse_mode: "HTML",
      text: `👋 Oi! O número deste chat é <code>${chat}</code>.\n\nSalve esse número no GitHub como segredo <b>TELEGRAM_CHAT_ID</b> e rode o workflow <b>Instalar bot</b> de novo.`,
    }));
    return ok();
  }
  if (chat !== String(env.TELEGRAM_CHAT_ID)) return ok(); // só o Miguel manda no escritório

  ctx.waitUntil(Promise.all([
    tg(env, "setMessageReaction", {
      chat_id: chat, message_id: msg.message_id, reaction: [{ type: "emoji", emoji: "👀" }],
    }),
    despachar(env, enxugar(update)),
  ]));
  return ok();
}

async function estado(env) {
  const r = await fetch(
    `https://api.github.com/repos/${env.GH_REPO}/contents/canais/painel-estado.json`,
    { headers: { authorization: `Bearer ${env.GH_PAT}`, accept: "application/vnd.github.raw+json", "user-agent": "escritorio-dark-worker" } },
  );
  return new Response(r.ok ? await r.text() : "{}", {
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });
}

// Ilustração com Flux (Workers AI). Cota grátis: 10.000 neurons/dia (~150 imagens).
async function imagem(req, env) {
  const { prompt, passos } = await req.json();
  if (!prompt) return new Response("faltou o prompt", { status: 400 });
  try {
    const r = await env.AI.run("@cf/black-forest-labs/flux-1-schnell", {
      prompt: String(prompt).slice(0, 2000),
      steps: Math.min(8, Math.max(1, passos || 6)),
    });
    const bin = Uint8Array.from(atob(r.image), (c) => c.charCodeAt(0));
    return new Response(bin, { headers: { "content-type": "image/jpeg" } });
  } catch (e) {
    const msg = String(e?.message || e);
    const cota = /limit|quota|neurons|429|capacity/i.test(msg);
    return new Response(msg.slice(0, 500), { status: cota ? 429 : 502 });
  }
}

function pagina(caminho) {
  const corpo = caminho === "/privacidade"
    ? `<h1>Política de Privacidade — Escritório Dark</h1>
<p>O Escritório Dark é uma ferramenta pessoal do dono dos canais para produzir e publicar vídeos nos próprios canais do YouTube (Ouro &amp; Império, Mapeado e Marca-Página).</p>
<p>O app acessa apenas as contas do YouTube do próprio dono, para enviar vídeos, thumbnails e legendas e ler as estatísticas desses canais. Nenhum dado de terceiros é coletado, vendido ou compartilhado.</p>
<p>Os tokens de acesso ficam guardados como segredos criptografados no GitHub do dono e podem ser revogados a qualquer momento em myaccount.google.com/permissions.</p>
<p>Uso de dados do Google: o uso e a transferência de informações recebidas das APIs do Google seguem a Política de Dados do Usuário dos Serviços de API do Google, incluindo os requisitos de Uso Limitado.</p>
<p>Contato: (contato privado)</p>`
    : `<h1>Termos de Uso — Escritório Dark</h1>
<p>O Escritório Dark é uma ferramenta de uso pessoal, sem usuários externos. Ao autorizar o app, o dono permite que ele publique e analise vídeos nos próprios canais do YouTube. O acesso pode ser revogado a qualquer momento em myaccount.google.com/permissions.</p>
<p>Contato: (contato privado)</p>`;
  return new Response(`<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Escritório Dark</title><body style="font-family:system-ui,sans-serif;max-width:720px;margin:40px auto;padding:0 16px;line-height:1.6;color:#222">${corpo}</body></html>`,
    { headers: { "content-type": "text/html; charset=utf-8" } });
}

export default {
  async fetch(req, env, ctx) {
    const url = new URL(req.url);
    if (url.pathname === "/telegram" && req.method === "POST") return telegram(req, env, ctx);
    if (url.pathname === "/privacidade" || url.pathname === "/termos") return pagina(url.pathname);

    const chaveOk = env.PAINEL_KEY && url.searchParams.get("k") === env.PAINEL_KEY;
    if (url.pathname === "/api/imagem" && req.method === "POST") {
      const chave = req.headers.get("x-chave");
      if (!env.PAINEL_KEY || chave !== env.PAINEL_KEY) return new Response("proibido", { status: 403 });
      return imagem(req, env);
    }
    if (url.pathname === "/api/estado") return chaveOk ? estado(env) : new Response("{}", { status: 403 });
    if (url.pathname === "/" || url.pathname === "/painel") {
      if (!chaveOk) return new Response(`<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>Escritório Dark</title><body style="font-family:system-ui,sans-serif;max-width:720px;margin:40px auto;padding:0 16px"><h1>Escritório Dark 🎬</h1><p>Ferramenta pessoal que produz os canais Ouro &amp; Império, Mapeado e Marca-Página no YouTube.</p><p><a href="/privacidade">Política de Privacidade</a> · <a href="/termos">Termos de Uso</a></p></body></html>`, { headers: { "content-type": "text/html; charset=utf-8" } });
      return new Response(PAINEL_HTML, { headers: { "content-type": "text/html; charset=utf-8" } });
    }
    return new Response("não encontrado", { status: 404 });
  },
};
