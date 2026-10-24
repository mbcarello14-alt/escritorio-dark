// Renderiza a cena 3D quadro a quadro no Chromium sem tela (determinístico: quadro(t) para cada t).
// node pipeline/reels/render.mjs <timeline.json> <pasta_quadros> <duracao_s> [fps] [largura] [altura]
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_CORE || "playwright-core");
const aqui = path.dirname(fileURLToPath(import.meta.url));
const raiz = path.resolve(aqui, "..", "..");
const [timeline, saida, durS, fpsS = "30", wS = "1080", hS = "1920"] = process.argv.slice(2);
const fps = +fpsS, total = Math.ceil(+durS * fps);
fs.mkdirSync(saida, { recursive: true });

const TIPOS = { ".html": "text/html", ".js": "text/javascript", ".json": "application/json", ".ttf": "font/ttf" };
const rotas = { "/reels/": path.join(raiz, "pipeline", "reels"), "/fonts/": path.join(raiz, "assets", "fonts") };
const srv = http.createServer((req, res) => {
  const url = decodeURIComponent(req.url.split("?")[0]);
  let arq = null;
  if (url === "/trabalho/timeline.json") arq = path.resolve(timeline);
  for (const [pre, dir] of Object.entries(rotas)) if (url.startsWith(pre)) arq = path.join(dir, url.slice(pre.length));
  if (!arq || !fs.existsSync(arq)) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { "content-type": TIPOS[path.extname(arq)] || "application/octet-stream" });
  fs.createReadStream(arq).pipe(res);
}).listen(0);
const porta = srv.address().port;

const exe = process.env.CHROME_PATH || ["/usr/bin/google-chrome", "/opt/pw-browsers/chromium"].find(p => fs.existsSync(p));
const nav = await chromium.launch({ executablePath: exe, args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
const pag = await nav.newPage({ viewport: { width: +wS, height: +hS } });
pag.on("pageerror", e => { console.error("ERRO NA CENA:", e.message); process.exitCode = 2; });
await pag.goto(`http://localhost:${porta}/reels/cena.html?w=${wS}&h=${hS}`);
await pag.waitForFunction(() => window.pronto === true, null, { timeout: 60000 });
const t0 = Date.now();
for (let i = 0; i < total; i++) {
  const dados = await pag.evaluate(t => { window.quadro(t); return document.querySelector("canvas").toDataURL("image/jpeg", 0.9); }, i / fps);
  fs.writeFileSync(path.join(saida, `q${String(i).padStart(5, "0")}.jpg`), Buffer.from(dados.split(",")[1], "base64"));
  if (i % 60 === 0) console.log(`quadro ${i}/${total} (${((Date.now() - t0) / 1000).toFixed(0)}s)`);
}
await nav.close(); srv.close();
console.log(`pronto: ${total} quadros em ${((Date.now() - t0) / 1000).toFixed(0)}s`);
