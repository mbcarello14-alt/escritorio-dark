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

export default {
  async fetch(req, env, ctx) {
    const url = new URL(req.url);
    if (url.pathname === "/telegram" && req.method === "POST") return telegram(req, env, ctx);

    const chaveOk = env.PAINEL_KEY && url.searchParams.get("k") === env.PAINEL_KEY;
    if (url.pathname === "/api/estado") return chaveOk ? estado(env) : new Response("{}", { status: 403 });
    if (url.pathname === "/" || url.pathname === "/painel") {
      if (!chaveOk) return new Response("Escritório Dark 🎬", { headers: { "content-type": "text/plain; charset=utf-8" } });
      return new Response(PAINEL_HTML, { headers: { "content-type": "text/html; charset=utf-8" } });
    }
    return new Response("não encontrado", { status: 404 });
  },
};
