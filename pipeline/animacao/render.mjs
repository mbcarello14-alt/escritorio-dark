// Servidor de render das cenas animadas: abre o Chromium uma vez e renderiza várias cenas.
// Lê uma tarefa JSON por linha no stdin: {"cena": {...}, "saida": "/caminho/cena.mp4", "fps": 30}
// Para cada uma, desenha quadro a quadro (determinístico) e entrega um mp4 só com vídeo.
// Responde "OK <saida> <segundos>" ou "ERRO <mensagem>" por linha no stdout.
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import readline from "node:readline";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const aqui = path.dirname(fileURLToPath(import.meta.url));
const raiz = path.resolve(aqui, "..", "..");
function carregarPlaywright() {
  for (const base of [import.meta.url, path.join(raiz, "pipeline", "reels", "x.js")]) {
    try { return createRequire(base)(process.env.PLAYWRIGHT_CORE || "playwright-core"); } catch { /* tenta o próximo */ }
  }
  throw new Error("playwright-core não instalado (npm i --prefix pipeline/reels playwright-core)");
}
const { chromium } = carregarPlaywright();
const W = +(process.env.LARGURA || 1920), H = +(process.env.ALTURA || 1080);

const TIPOS = { ".html": "text/html", ".js": "text/javascript", ".json": "application/json", ".woff2": "font/woff2",
  ".ttf": "font/ttf", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp" };
const rotas = { "/animacao/": path.join(raiz, "pipeline", "animacao"), "/fonts/": path.join(raiz, "assets", "fonts") };
const srv = http.createServer((req, res) => {
  const url = decodeURIComponent(req.url.split("?")[0]);
  let arq = null;
  if (url.startsWith("/abs/")) arq = url.slice(4);
  for (const [pre, dir] of Object.entries(rotas)) if (url.startsWith(pre)) arq = path.join(dir, url.slice(pre.length));
  if (!arq || !fs.existsSync(arq) || fs.statSync(arq).isDirectory()) { res.writeHead(404); return res.end(); }
  const tipo = TIPOS[path.extname(arq).toLowerCase()] || "image/jpeg";
  res.writeHead(200, { "content-type": tipo });
  fs.createReadStream(arq).pipe(res);
}).listen(0);
const porta = srv.address().port;

const exe = process.env.CHROME_PATH || ["/usr/bin/google-chrome", "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell"].find(p => fs.existsSync(p));
const nav = await chromium.launch(exe ? { executablePath: exe } : {});
const pag = await nav.newPage({ viewport: { width: W, height: H } });
let erroPagina = null;
pag.on("pageerror", e => { erroPagina = e.message; });
pag.on("console", m => { if (m.type() === "error") console.error("cena:", m.text()); });
await pag.goto(`http://localhost:${porta}/animacao/cena.html?w=${W}&h=${H}`);
await pag.waitForFunction(() => window.pronto === true, null, { timeout: 60000 });

async function renderizar({ cena, saida, fps = 30 }) {
  erroPagina = null;
  await pag.evaluate(async s => { await window.carregar(s); }, cena);
  if (erroPagina) throw new Error(erroPagina);
  const total = Math.max(1, Math.round(cena.duracao * fps));
  const ff = spawn("ffmpeg", ["-y", "-v", "error", "-f", "image2pipe", "-framerate", String(fps), "-c:v", "mjpeg", "-i", "-",
    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", String(fps), saida],
    { stdio: ["pipe", "ignore", "inherit"] });
  const terminou = new Promise((ok, falha) => ff.on("close", c => c === 0 ? ok() : falha(new Error("ffmpeg saiu com " + c))));
  for (let i = 0; i < total; i++) {
    const b64 = await pag.evaluate(t => { window.quadro(t); return document.getElementById("c").toDataURL("image/jpeg", 0.92).slice(23); }, i / fps);
    if (erroPagina) { ff.stdin.end(); throw new Error(erroPagina); }
    if (!ff.stdin.write(Buffer.from(b64, "base64"))) await new Promise(r => ff.stdin.once("drain", r));
  }
  ff.stdin.end();
  await terminou;
}

const linhas = readline.createInterface({ input: process.stdin });
console.log("PRONTO");
for await (const linha of linhas) {
  if (!linha.trim()) continue;
  const t0 = Date.now();
  try {
    const tarefa = JSON.parse(linha);
    await renderizar(tarefa);
    console.log(`OK ${tarefa.saida} ${((Date.now() - t0) / 1000).toFixed(1)}`);
  } catch (e) {
    console.log("ERRO " + String(e.message || e).replace(/\n/g, " "));
  }
}
await nav.close(); srv.close();
