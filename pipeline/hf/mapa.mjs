// Geometria dos mapas animados para o HyperFrames: lê a cena (JSON) e devolve os caminhos SVG já projetados.
// Uso: node pipeline/hf/mapa.mjs cena.json saida.json
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const aqui = path.dirname(fileURLToPath(import.meta.url));
const req = createRequire(path.join(aqui, "x.js"));
const d3 = req("d3-geo");
const topo = req("topojson-client");
const vendor = path.join(aqui, "..", "animacao", "vendor");
const terra = JSON.parse(fs.readFileSync(path.join(vendor, "land-50m.json")));
const paises = JSON.parse(fs.readFileSync(path.join(vendor, "countries-50m.json")));
const nomesPt = JSON.parse(fs.readFileSync(path.join(aqui, "..", "animacao", "nomes-pt.json")));

const REGIOES = {
  mundo: [-168, -56, 190, 76], europa: [-24, 34, 45, 70], mediterraneo: [-9, 29, 38, 47],
  oriente_medio: [24, 11, 64, 42], america_sul: [-84, -56, -32, 13], brasil: [-74, -34, -34, 5.5],
  america_norte: [-128, 12, -58, 58], asia: [58, -8, 148, 56], africa: [-20, -36, 54, 38],
  china: [72, 17, 136, 54], india: [64, 5, 98, 36], atlantico: [-92, -38, 22, 62],
  escandinavia: [2, 53, 33, 71], caribe: [-90, 8, -58, 28], italia: [5, 36, 20, 47.5],
  iberia: [-11, 35, 4.5, 44.5], gra_bretanha: [-11, 49.5, 3, 59.5], egito: [24, 21, 37, 32.5],
  grecia: [19, 34.5, 29.5, 42], rota_seda: [10, 18, 125, 52], indico: [30, -30, 110, 28],
  japao: [127, 30, 147, 46], pacifico: [100, -45, 290, 50],
};
const reg = r => (typeof r === "string" ? REGIOES[r] : r) || REGIOES.mundo;

const [, , entrada, saida] = process.argv;
const cena = JSON.parse(fs.readFileSync(entrada));
const W = 1920, H = 1080, M = 1.25;              // o plano é 25% maior que a tela, para a câmera andar
const PW = Math.round(W * M), PH = Math.round(H * M);
const a = reg(cena.regiao);
const mp = bb => ({ type: "MultiPoint", coordinates: [[bb[0], bb[1]], [bb[2], bb[3]], [bb[0], bb[3]], [bb[2], bb[1]]] });
const pr = d3.geoMercator().fitExtent([[(PW - W) / 2 + 40, (PH - H) / 2 + 40], [(PW + W) / 2 - 40, (PH + H) / 2 - 40]], mp(a));
pr.clipExtent([[-40, -40], [PW + 40, PH + 40]]);
const p = g => d3.geoPath(pr).digits(1)(g) || "";
const pt = ll => pr(ll).map(v => +v.toFixed(1));

function anel(pontos) {
  const f = { type: "Polygon", coordinates: [[...pontos, pontos[0]]] };
  if (d3.geoArea(f) > 2 * Math.PI) f.coordinates[0].reverse();
  return f;
}
function porNome(n) {
  const en = (nomesPt[String(n).trim().toLowerCase()] || n).toLowerCase();
  return topo.feature(paises, paises.objects.countries).features.filter(f => f.properties.name.toLowerCase() === en);
}
function centroMaior(feats) {
  let melhor = null, area = -1;
  for (const f of feats) for (const c of (f.geometry.type === "MultiPolygon" ? f.geometry.coordinates : [f.geometry.coordinates])) {
    const g = { type: "Polygon", coordinates: c }, ar = d3.geoArea(g);
    if (ar > area) { area = ar; melhor = g; }
  }
  return melhor ? d3.geoCentroid(melhor) : null;
}
// câmera: escala e centro (no plano) que enquadram uma região
function camera(bb) {
  const c = pt([(bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2]);
  const q1 = pt([bb[0], bb[3]]), q2 = pt([bb[2], bb[1]]);
  const k = Math.min((W - 160) / Math.max(40, Math.abs(q2[0] - q1[0])), (H - 160) / Math.max(40, Math.abs(q2[1] - q1[1])));
  return { s: +Math.min(3.2, Math.max(1, k)).toFixed(3), cx: c[0], cy: c[1] };
}
const ondas = [];
{ let s = 7; const r = () => ((s = (s * 16807) % 2147483647) / 2147483647);
  const terraF = topo.feature(terra, terra.objects.land);
  for (let i = 0; i < 160; i++) { const x = r() * PW, y = r() * PH, ll = pr.invert([x, y]); if (ll && !d3.geoContains(terraF, ll)) ondas.push([+x.toFixed(0), +y.toFixed(0)]); } }

const out = {
  W: PW, H: PH, ondas,
  terra: p(topo.feature(terra, terra.objects.land)),
  bordas: p(topo.mesh(paises, paises.objects.countries, (x, y) => x !== y)),
  inicio: { s: 1, cx: PW / 2, cy: PH / 2 },
  fim: cena.camera_para ? camera(reg(cena.camera_para)) : null,
  paises: (cena.paises || []).map(x => { const f = (x.nomes || [x.nome]).flatMap(porNome); const c = x.rotulo_pos || centroMaior(f);
    return { d: p({ type: "FeatureCollection", features: f }), centro: c ? pt(c) : null }; }),
  areas: (cena.areas || []).map(x => { const g = anel(x.pontos); return { d: p(g), centro: pt(x.rotulo_pos || d3.geoCentroid(g)) }; }),
  rotas: (cena.rotas || []).map(x => { const pts = [];
    for (let k = 0; k < x.pontos.length - 1; k++) { const it = d3.geoInterpolate(x.pontos[k], x.pontos[k + 1]); for (let j = 0; j < 16; j++) pts.push(pt(it(j / 16))); }
    pts.push(pt(x.pontos.at(-1))); return { d: "M" + pts.map(q => q.join(",")).join("L") }; }),
  cidades: (cena.cidades || []).map(c => pt([c.lon, c.lat])),
  rotulos: (cena.rotulos || []).map(r => pt([r.lon, r.lat])),
};
fs.writeFileSync(saida, JSON.stringify(out));
