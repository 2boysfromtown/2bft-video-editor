#!/usr/bin/env node
// GPU render harness. Serves a page from a local folder, opens it in headless Chrome (WebGL / Canvas on the NVIDIA GPU),
// and receives whatever the page sends back. Three modes:
//   video   the page draws frame f at time f/fps and POSTs raw RGBA; ffmpeg encodes with h264_nvenc (+ optional audio)
//   stills  same, but each requested time is saved as one PNG
//   pack    the page encodes its own PNGs / JSON and POSTs them to /save and /json (sprite and storyboard packs)
//
//   node render.mjs --page=<file.html[?query]> [--mode=video|stills|pack] [--w=1080 --h=1920 --fps=30 --frames=900 --start=0]
//        [--out=<mp4 | folder>] [--audio=<wav>] [--cq=20] [--flip=0|1] [--stills=0.5,3,8] [--tag=name]
//        [--mount=/pack=D:\folder] (repeatable)  [--three=<three folder>] [--chrome=<chrome.exe>] [--set.key=value ...]
//   flip: WebGL pages read pixels bottom-up (default --flip=1); Canvas 2D pages pass --flip=0.
import http from 'node:http';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawn, spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url)), skillDir = path.resolve(here, '..');
const argv = {}, mounts = {};
for (const a of process.argv.slice(2)) {
  if (!a.startsWith('--')) continue;
  const i = a.indexOf('='), k = i < 0 ? a.slice(2) : a.slice(2, i), v = i < 0 ? true : a.slice(i + 1);
  if (k === 'mount') { const j = v.indexOf('='); let p = v.slice(0, j); if (!p.endsWith('/')) p += '/'; mounts[p] = path.resolve(v.slice(j + 1)); } else argv[k] = v;
}
if (!argv.page) { console.error('usage: node render.mjs --page=<file.html> [--mode=video|stills|pack] ... (see the header of this file)'); process.exit(1); }

const [pagePath, query = ''] = String(argv.page).split('?');
const pageAbs = path.resolve(pagePath);
if (!fs.existsSync(pageAbs)) { console.error('page not found: ' + pageAbs); process.exit(1); }
const root = path.dirname(pageAbs);
const mode = argv.mode ?? (argv.stills ? 'stills' : 'video');
const set = Object.fromEntries(Object.entries(argv).filter(([k]) => k.startsWith('set.')).map(([k, v]) => [k.slice(4), v]));
const cfg = {
  mode, w: +(argv.w ?? 1920), h: +(argv.h ?? 1080), fps: +(argv.fps ?? 30), frames: +(argv.frames ?? 30), start: +(argv.start ?? 0),
  stills: argv.stills ? String(argv.stills).split(',').map(Number) : null, tag: argv.tag ?? 'still', cq: +(argv.cq ?? 18),
  flip: argv.flip !== '0', audio: argv.audio ? path.resolve(argv.audio) : null, set,
};
const out = path.resolve(argv.out ?? (mode === 'video' ? 'out/render.mp4' : mode === 'stills' ? 'out/stills' : 'out/pack'));
if (mode === 'video') fs.mkdirSync(path.dirname(out), { recursive: true }); else fs.mkdirSync(out, { recursive: true });

const threeDir = argv.three ? path.resolve(argv.three) : path.join(skillDir, 'node_modules', 'three');
if (!fs.existsSync(path.join(threeDir, 'build', 'three.module.js'))) console.warn('note: three.js not found at ' + threeDir + ' (only needed by WebGL pages; run: npm --prefix "' + skillDir + '" install)');
const chromePath = argv.chrome ?? ['C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', 'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe', 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe', 'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe'].find(p => fs.existsSync(p));
if (!chromePath) { console.error('no Chrome or Edge found; pass --chrome=<path>'); process.exit(1); }

const roots = { '/_skill/': path.join(here, 'lib') + path.sep, '/three/': threeDir + path.sep, ...Object.fromEntries(Object.entries(mounts).map(([k, v]) => [k, v + path.sep])), '/': root + path.sep };
const mime = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json', '.wav': 'audio/wav', '.mp3': 'audio/mpeg', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.svg': 'image/svg+xml', '.css': 'text/css', '.woff2': 'font/woff2', '.ttf': 'font/ttf' };

let ffmpeg = null, ffDone = Promise.resolve();
if (mode === 'video') {
  const a = ['-y', '-hide_banner', '-loglevel', 'warning', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', `${cfg.w}x${cfg.h}`, '-framerate', String(cfg.fps), '-i', 'pipe:0'];
  if (cfg.audio) a.push('-i', cfg.audio);
  a.push('-vf', (cfg.flip ? 'vflip,' : '') + 'scale=out_color_matrix=bt709:out_range=tv,format=yuv420p', '-c:v', 'h264_nvenc', '-preset', 'p7', '-tune', 'hq', '-rc', 'vbr', '-cq', String(cfg.cq), '-b:v', '0', '-profile:v', 'high',
    '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-movflags', '+faststart');
  if (cfg.audio) a.push('-c:a', 'aac', '-b:a', '192k', '-shortest');
  a.push(out);
  ffmpeg = spawn('ffmpeg', a, { stdio: ['pipe', 'inherit', 'inherit'] }); ffDone = new Promise(r => ffmpeg.on('close', r));
}

let chrome, received = 0, errors = 0;
const t0 = Date.now(), body = req => new Promise(r => { const c = []; req.on('data', d => c.push(d)); req.on('end', () => r(Buffer.concat(c))); });
const inside = (base, rel) => { const p = path.normalize(path.join(base, rel)); return p.startsWith(path.normalize(base)) ? p : null; };
const kill = () => { if (chrome) spawnSync('taskkill', ['/PID', String(chrome.pid), '/T', '/F']); };

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, 'http://x');
  try {
    if (url.pathname === '/config') { res.setHeader('content-type', 'application/json'); return res.end(JSON.stringify(cfg)); }
    if (url.pathname === '/log') { const m = (await body(req)).toString(); if (/^(ERROR|REJECT)/.test(m)) errors++; console.log('[page]', m); return res.end('ok'); }
    if (url.pathname === '/save' || url.pathname === '/json') {
      const rel = url.searchParams.get('path') ?? '', dest = inside(out, rel);
      if (!dest || !mode.match(/pack|stills/)) return res.writeHead(400).end('bad path or mode');
      fs.mkdirSync(path.dirname(dest), { recursive: true }); fs.writeFileSync(dest, await body(req)); received++; return res.end('ok');
    }
    if (url.pathname === '/frame') {
      const buf = await body(req);
      if (buf.length !== cfg.w * cfg.h * 4) { console.error('bad frame size', buf.length, 'expected', cfg.w * cfg.h * 4); return res.writeHead(400).end(); }
      if (mode === 'stills') {
        const name = url.searchParams.get('name') ?? `${cfg.tag}_${received}`;
        spawnSync('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', `${cfg.w}x${cfg.h}`, '-i', 'pipe:0', '-vf', cfg.flip ? 'vflip' : 'null', path.join(out, `${name}.png`)], { input: buf });
      } else if (!ffmpeg.stdin.write(buf)) await new Promise(r => ffmpeg.stdin.once('drain', r));
      received++; if (mode === 'video' && received % 120 === 0) console.log(`frame ${received}/${cfg.frames}  ${((Date.now() - t0) / 1000).toFixed(1)}s`);
      return res.end('ok');
    }
    if (url.pathname === '/finish') {
      res.end('ok'); if (ffmpeg) ffmpeg.stdin.end(); await ffDone;
      console.log(`done: ${received} ${mode === 'pack' ? 'files' : 'frames'} in ${((Date.now() - t0) / 1000).toFixed(1)}s -> ${out}${errors ? `  (WARNING: ${errors} page errors logged)` : ''}`);
      kill(); process.exit(errors ? 2 : 0);
    }
    const rel = decodeURIComponent(url.pathname), prefix = Object.keys(roots).filter(p => rel.startsWith(p)).sort((a, b) => b.length - a.length)[0];
    const file = inside(roots[prefix], rel.slice(prefix.length));
    if (!file || !fs.existsSync(file) || fs.statSync(file).isDirectory()) return res.writeHead(404).end('not found: ' + rel);
    res.setHeader('content-type', mime[path.extname(file).toLowerCase()] ?? 'application/octet-stream'); fs.createReadStream(file).pipe(res);
  } catch (e) { console.error(e); res.writeHead(500).end(String(e)); }
});

server.listen(0, '127.0.0.1', () => {
  const port = server.address().port, profile = fs.mkdtempSync(path.join(os.tmpdir(), 'vap-chrome-'));
  chrome = spawn(chromePath, ['--headless=new', `--user-data-dir=${profile}`, `--window-size=${cfg.w},${cfg.h}`, '--use-angle=d3d11', '--ignore-gpu-blocklist', '--enable-gpu-rasterization', '--no-first-run', '--no-default-browser-check',
    '--autoplay-policy=no-user-gesture-required', '--disable-background-timer-throttling', '--disable-renderer-backgrounding', '--disable-backgrounding-occluded-windows',
    `http://127.0.0.1:${port}/${path.basename(pageAbs)}${query ? '?' + query : ''}`], { stdio: 'ignore' });
  console.log(`mode ${mode}, ${cfg.w}x${cfg.h}, serving ${root} on :${port}`);
});
setTimeout(() => { console.error('timeout'); kill(); process.exit(1); }, +(argv.timeout ?? 25) * 60 * 1000);
