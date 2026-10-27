// QUEST LAB renderer (end card names come from the plan: brand=, partner=).
// Draws one output frame at time t from an edit JSON (?edit=edits/x.json), built by build.py.
// Layers: world (background + footage cards, moved by the energy camera) -> world gfx -> HUD -> captions -> top gfx -> post (rgb split, flash, grain).
import { boot2d } from '/_skill/boot2d.js';

const q = new URLSearchParams(location.search);
const E = await (await fetch(q.get('edit'))).json();
for (const f of ['900 80px Inter', '700 30px Inter', '700 30px JBM', '700 80px Bahn']) await document.fonts.load(f);
const { cfg, ctx, run, log } = await boot2d();
const W = cfg.w, H = cfg.h, SFPS = 30, VERT = H > W, U = VERT ? W / 1080 : W / 1920;   // U = unit scale
const C = Object.assign({
  blue: '#4282F0', blueD: '#2A60E4', blueDD: '#173E9E', mint: '#12EABB', ink: '#0B1220', ivory: '#F7F5EF',
  red: '#FF4A3D', yellow: '#FFD23F', grey: '#9AA3B2',
}, E.colors || {});
const KEYC = { mint: C.mint, red: C.red, yellow: C.yellow, blue: C.blue, ivory: C.ivory, ink: C.ink };
const KEYT = { mint: C.ink, red: C.ivory, yellow: C.ink, blue: C.ivory, ivory: C.ink, ink: C.mint };

// ---------- helpers ----------
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const lerp = (a, b, p) => a + (b - a) * p;
const lerpR = (a, b, p) => a.map((v, i) => lerp(v, b[i], p));
const eio = p => p < .5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2;
const eout = p => 1 - Math.pow(1 - p, 3);
const eout5 = p => 1 - Math.pow(1 - p, 5);
const back = (p, s = 1.7) => 1 + (s + 1) * Math.pow(p - 1, 3) + s * Math.pow(p - 1, 2);
const spring = p => p >= 1 ? 1 : 1 - Math.exp(-6.5 * p) * Math.cos(11 * p);     // overshoot settle
const hash = n => { const s = Math.sin(n * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); };
function rr(x, y, w, h, r) { ctx.beginPath(); if (ctx.roundRect) ctx.roundRect(x, y, w, h, Math.max(0, r)); else ctx.rect(x, y, w, h); }
function font(px, wt = 900, fam = 'Inter') {
  ctx.font = `${wt} ${Math.round(px)}px ${fam}`;
  ctx.fontStretch = fam === 'Bahn' ? 'condensed' : 'normal';
}
const S = v => v * U;

// ---------- footage frames ----------
const cache = new Map();
function frame(n, clip) {
  const key = clip ? clip + ':' + n : n;
  const url = m => clip ? `/clips/${clip}/${m}.jpg` : `/frames/${m}.jpg`;
  const get = async () => {
    // nearest available frame (time-lapses only cache every Nth frame); never stall the render on a missing frame
    for (let d = 0; d <= 24; d++) for (const m of d ? [n - d, n + d] : [n]) { if (m < 1) continue; const r = await fetch(url(m)); if (r.ok) return createImageBitmap(await r.blob()); }
    log('WARN missing frame ' + n + (clip ? ' in ' + clip : '') + ' (no neighbour within 24)');
    const blank = new OffscreenCanvas(16, 16); blank.getContext('2d');   // transferToImageBitmap throws on a canvas with no context
    return blank.transferToImageBitmap();
  };
  if (!cache.has(key)) { const p = get(); p.catch(() => {}); cache.set(key, p); }
  return cache.get(key);
}
function evict(keep) {
  if (cache.size < 60) return;
  for (const [k, v] of cache) if (typeof k === 'string' ? true : Math.abs(k - keep) > 90) { v.then(b => b.close?.()).catch(() => {}); cache.delete(k); if (cache.size < 45) break; }
}
const assets = new Map();
function asset(name) {
  if (!assets.has(name)) { const p = (async () => createImageBitmap(await (await fetch(E.assets[name])).blob()))(); p.catch(e => log('asset ' + name + ' ' + e)); assets.set(name, p); }
  return assets.get(name);
}

const shots = E.shots;
let shotIdx = 0;
function shotAt(t) {
  if (t < shots[shotIdx].t0) shotIdx = 0;
  while (shotIdx < shots.length - 1 && t >= shots[shotIdx].t1) shotIdx++;
  return shots[shotIdx];
}
let HOLD = 0;   // hit-stop offset (seconds) for the current frame, from the camera track
function srcT(s, t) { const loc = Math.max(0, t - s.t0 - HOLD); return s.hold != null ? s.hold : s.freeze ? s.src0 : s.src0 + loc * (s.speed ?? 1); }
function srcFrame(st) { return Math.max(1, Math.round(st * SFPS)); }

// ---------- backgrounds (drawn with margin so the camera can move) ----------
const M = Math.round(120 * U);
function makeBg(kind) {
  const c = new OffscreenCanvas(W + 2 * M, H + 2 * M), d = c.getContext('2d');
  const BW = c.width, BH = c.height;
  if (kind === 'blue') {
    d.fillStyle = C.blue; d.fillRect(0, 0, BW, BH);
    const g = d.createRadialGradient(BW * .3, BH * .25, 0, BW * .5, BH * .5, Math.max(BW, BH) * .8);
    g.addColorStop(0, 'rgba(255,255,255,0.10)'); g.addColorStop(1, 'rgba(10,30,90,0.28)'); d.fillStyle = g; d.fillRect(0, 0, BW, BH);
    d.fillStyle = 'rgba(12,32,96,0.32)';
  } else {
    d.fillStyle = C.ink; d.fillRect(0, 0, BW, BH);
    const g = d.createRadialGradient(BW * .5, BH * .35, 0, BW * .5, BH * .5, Math.max(BW, BH) * .75);
    g.addColorStop(0, 'rgba(66,130,240,0.20)'); g.addColorStop(1, 'rgba(0,0,0,0)'); d.fillStyle = g; d.fillRect(0, 0, BW, BH);
    d.fillStyle = 'rgba(120,160,255,0.10)';
  }
  const st = Math.round(22 * U), ds = Math.max(2, Math.round(3 * U));
  for (let y = st / 2; y < BH; y += st) for (let x = st / 2; x < BW; x += st) d.fillRect(x, y, ds, ds);
  return c;
}
const BG = { blue: makeBg('blue'), ink: makeBg('ink') };
function drawBg(s, img, t) {
  const b = s.bg || { type: 'blue' };
  if (b.type === 'blur' && img) {
    const [sx, sy, sw, sh] = b.rect || [0, 0, img.width, img.height]; const k = Math.max((W + 2 * M) / sw, (H + 2 * M) / sh);
    ctx.save(); ctx.filter = 'blur(40px) brightness(0.45) saturate(1.4)';
    ctx.drawImage(img, sx, sy, sw, sh, (W - sw * k) / 2, (H - sh * k) / 2, sw * k, sh * k); ctx.restore(); ctx.filter = 'none';
    ctx.globalAlpha = .55; ctx.drawImage(BG.ink, -M, -M); ctx.globalAlpha = 1; return;
  }
  const c = BG[b.type] || BG.blue;
  const drift = (t * 14 * U) % (22 * U);   // dot grid drifts slowly
  ctx.drawImage(c, -M - drift, -M - drift * .5);
  if (b.wedge !== false && b.type !== 'ink') {   // the overlay's mint corner wedge
    ctx.save(); ctx.fillStyle = C.mint; ctx.beginPath();
    if (VERT) { ctx.moveTo(W * .55, -M); ctx.lineTo(W + M, -M); ctx.lineTo(W + M, H * .07); }
    else { ctx.moveTo(W * .78, -M); ctx.lineTo(W + M, -M); ctx.lineTo(W + M, H * .13); }
    ctx.closePath(); ctx.fill(); ctx.restore();
  }
}

// ---------- cards ----------
function trkAt(tr, t) {   // face-track offset [dx, dy] at shot-local time t (evenly spaced samples from build.py)
  if (t <= tr[0][0]) return [tr[0][1], tr[0][2]];
  const step = tr.length > 1 ? tr[1][0] - tr[0][0] : 1, i = Math.min(tr.length - 2, Math.floor((t - tr[0][0]) / step));
  if (i < 0) return [tr[0][1], tr[0][2]];
  const f = clamp((t - tr[i][0]) / step); return [lerp(tr[i][1], tr[i + 1][1], f), lerp(tr[i][2], tr[i + 1][2], f)];
}
function paneRect(p, prog, loc) {
  const k = p.ease === 'punch' ? eout(clamp(loc / .3)) : p.ease === 'out' ? eout(prog) : p.ease === 'lin' ? prog : eio(prog);
  const r = p.s1 ? lerpR(p.s0, p.s1, k) : p.s0;
  if (p.trk && p.trk.length) { const o = trkAt(p.trk, loc); return [r[0] + o[0], r[1] + o[1], r[2], r[3]]; }   // face tracking
  return r;
}
function cardIn(p, loc) {   // entrance animation of a card: slide / scale with spring
  if (!p.in || loc > (p.in.dur ?? .45) + (p.in.delay ?? 0)) return { dx: 0, dy: 0, sc: 1, a: 1 };
  const k = clamp((loc - (p.in.delay ?? 0)) / (p.in.dur ?? .45)), s = spring(k);
  const f = p.in.from || 'scale';
  if (f === 'scale') return { dx: 0, dy: 0, sc: lerp(.6, 1, s), a: clamp(k * 4) };
  const dist = (f === 'left' || f === 'right' ? W : H) * .7, sg = (f === 'left' || f === 'top') ? -1 : 1;
  return f === 'left' || f === 'right' ? { dx: sg * dist * (1 - s), dy: 0, sc: 1, a: 1 } : { dx: 0, dy: sg * dist * (1 - s), sc: 1, a: 1 };
}
function drawCard(img, p, prog, loc, opt = {}) {
  let [sx, sy, sw, sh] = paneRect(p, prog, loc);
  const d = p.d1 ? lerpR(p.d, p.d1, (p.dease === 'out' ? eout : eio)(prog)) : p.d;
  let [dx, dy, dw, dh] = d;
  if (p.fit === 'contain') {   // letterbox the whole source rect inside d
    const k = Math.min(dw / sw, dh / sh); const nw = sw * k, nh = sh * k; dx += (dw - nw) / 2; dy += (dh - nh) / 2; dw = nw; dh = nh;
  } else {
    const sa = sw / sh, da = dw / dh;
    if (sa > da) { const nw = sh * da; sx += (sw - nw) / 2; sw = nw; } else { const nh = sw / da; sy += (sh - nh) / 2; sh = nh; }
  }
  const an = cardIn(p, loc);
  const r = p.round ? Math.min(dw, dh) / 2 : (p.r ?? 0) * U, ol = (p.outline ?? 0) * U, sd = (p.shadow ?? 0) * U;
  ctx.save(); ctx.globalAlpha = an.a * (p.alpha ?? 1);
  ctx.translate(dx + dw / 2 + an.dx, dy + dh / 2 + an.dy); ctx.rotate((p.tilt ?? 0) * Math.PI / 180); ctx.scale(an.sc, an.sc);
  const x = -dw / 2, y = -dh / 2;
  if (sd) { rr(x + sd, y + sd, dw, dh, r); ctx.fillStyle = C.ink; ctx.fill(); }
  else if (p.soft) { ctx.shadowColor = 'rgba(0,0,0,0.55)'; ctx.shadowBlur = 40 * U; ctx.shadowOffsetY = 14 * U; rr(x, y, dw, dh, r); ctx.fillStyle = '#000'; ctx.fill(); ctx.shadowColor = 'transparent'; }
  ctx.save(); rr(x, y, dw, dh, r); ctx.clip();
  if (p.fill) { ctx.fillStyle = p.fill; ctx.fillRect(x, y, dw, dh); }
  const up = dw / sw;
  const sat = opt.sat ?? 1;
  let f = `contrast(${(1.06 * (p.contrast ?? 1)).toFixed(3)}) saturate(${(1.06 * sat).toFixed(3)}) brightness(${(p.bright ?? 1.01).toFixed(3)})`;
  if (p.grade) f += ' ' + p.grade;   // webcam-only grade from build.py cam_grade (references/colour.md)
  if ((p.sharpen ?? (up > 1.55)) && !opt.nosharp) f = 'url(#sharp) ' + f;
  ctx.filter = f; ctx.imageSmoothingEnabled = true; ctx.imageSmoothingQuality = 'high';
  if (img) ctx.drawImage(img, sx, sy, sw, sh, x, y, dw, dh);
  ctx.filter = 'none';
  if (opt.tint) { ctx.fillStyle = opt.tint; ctx.fillRect(x, y, dw, dh); }
  ctx.restore();
  if (ol) { ctx.lineWidth = ol; ctx.strokeStyle = p.outlineColor || C.ink; rr(x, y, dw, dh, r); ctx.stroke(); }
  ctx.restore();
  if (p.tag) sticker(p.tag, dx + 18 * U + an.dx, dy + dh - 18 * U + an.dy, { size: 24, fill: p.tagColor || 'ink', anchor: 'bl', rot: -2 });
}

// ---------- stickers (the overlay's flat block + ink outline + hard shadow) ----------
function sticker(text, x, y, o = {}) {
  const size = (o.size ?? 32) * U, fam = o.fam || 'Bahn', wt = o.wt ?? 700;
  font(size, wt, fam); const tw = ctx.measureText(text).width;
  const px = size * (o.padX ?? .42), py = size * (o.padY ?? .26), w = tw + 2 * px, h = size * 1.0 + 2 * py;
  const fill = KEYC[o.fill] || o.fill || C.mint, tcol = o.color || KEYT[o.fill] || C.ink;
  const ol = (o.outline ?? 4) * U, sd = (o.shadow ?? 6) * U;
  let ax = x, ay = y;
  const an = o.anchor || 'cc';
  if (an[1] === 'l') ax = x + w / 2; else if (an[1] === 'r') ax = x - w / 2;
  if (an[0] === 't') ay = y + h / 2; else if (an[0] === 'b') ay = y - h / 2;
  ctx.save(); ctx.globalAlpha = o.alpha ?? 1; ctx.translate(ax, ay); ctx.rotate((o.rot ?? 0) * Math.PI / 180); ctx.scale(o.scale ?? 1, o.scale ?? 1);
  if (sd) { rr(-w / 2 + sd, -h / 2 + sd, w, h, 6 * U); ctx.fillStyle = C.ink; ctx.fill(); }
  rr(-w / 2, -h / 2, w, h, 6 * U); ctx.fillStyle = fill; ctx.fill();
  if (ol) { ctx.lineWidth = ol; ctx.strokeStyle = C.ink; ctx.stroke(); }
  font(size, wt, fam); ctx.fillStyle = tcol; ctx.textBaseline = 'middle'; ctx.textAlign = 'center';
  ctx.fillText(text, 0, size * (fam === 'Bahn' ? .04 : .03));
  ctx.restore();
  return { w, h };
}

// ---------- footage ----------
async function drawWorld(t, cam) {
  const s = shotAt(t), loc = t - s.t0, prog = clamp(loc / Math.max(.001, s.t1 - s.t0));
  const st = srcT(s, t), n = srcFrame(st);
  const need = new Set(s.panes.map(p => p.src || 'frame'));
  const img = need.has('frame') || (s.bg && s.bg.type === 'blur') ? await frame(n) : null;
  for (let k = 1; k <= 4; k++) { const tt = Math.min(s.t1 - .001, t + k / cfg.fps); frame(srcFrame(srcT(s, tt))).catch(() => {}); }
  evict(n);
  const fx = s.fx || {};
  // camera
  ctx.save();
  let [cdx, cdy, crot, cz] = cam;
  if (fx.whip && loc < .2) { const k = 1 - eout(clamp(loc / .2)); cdx += (fx.whip === 'left' ? -1 : 1) * W * .35 * k; }
  ctx.translate(W / 2 + cdx, H / 2 + cdy); ctx.rotate(crot * Math.PI / 180); ctx.scale(cz, cz); ctx.translate(-W / 2, -H / 2);
  if (fx.whip && loc < .2) ctx.filter = `blur(${(18 * (1 - loc / .2)).toFixed(1)}px)`;
  drawBg(s, img, t);
  const sat = fx.freeze ? lerp(1, .35, eout(clamp(loc / .25))) : 1;
  for (const p of s.panes) {
    let im = null; const src = p.src || 'frame';
    if (src === 'frame') im = p.hold != null ? await frame(srcFrame(p.hold)) : img;
    else if (src.startsWith('clip:')) {
      const c = src.slice(5), ct = p.clipT != null ? p.clipT + (p.clipSpeed ?? 1) * loc : (p.clip0 ?? 0) + loc;
      im = await frame(Math.max(1, Math.round(ct * SFPS)), c);
      frame(Math.max(1, Math.round((ct + 1 / cfg.fps) * SFPS)), c).catch(() => {});
    } else if (src.startsWith('img:')) im = await asset(src.slice(4));
    drawCard(im, p, prog, loc, { sat });
  }
  ctx.filter = 'none';
  for (const g of E.gfx) if (g.layer === 'world') G[g.type]?.(g, t);
  ctx.restore();
  if (fx.freeze) freezeFx(s, loc);
  if (fx.rewind) rewindFx(loc);
  return s;
}
function freezeFx(s, loc) {
  const k = eout(clamp(loc / .3));
  ctx.save(); ctx.strokeStyle = s.fx.freezeColor === 'red' ? C.red : C.mint; ctx.lineWidth = 8 * U; ctx.lineCap = 'square';
  const inset = lerp(60, 26, k) * U, L = 90 * U;
  for (const [px, py, sx, sy] of [[inset, inset, 1, 1], [W - inset, inset, -1, 1], [inset, H - inset, 1, -1], [W - inset, H - inset, -1, -1]]) {
    ctx.beginPath(); ctx.moveTo(px + sx * L, py); ctx.lineTo(px, py); ctx.lineTo(px, py + sy * L); ctx.stroke();
  }
  ctx.restore();
}
function rewindFx(loc) {
  ctx.save(); ctx.globalAlpha = .45; ctx.fillStyle = '#fff';
  for (let i = 0; i < 7; i++) { const y = ((loc * 1100 + i * 211) % H); ctx.fillRect(0, y, W, 2 + (i % 3) * U); }
  ctx.globalAlpha = 1; sticker('◀◀ REWIND', 60 * U, (VERT ? 330 : 150) * U, { size: 40, fill: 'ivory', anchor: 'cl' }); ctx.restore();
}

// ---------- captions (kinetic, word pop, keyword sticker, energy jitter) ----------
const CB = Object.assign(VERT ? { y: 1150, size: 80, maxW: 760, lineH: 1.18, dx: -60 } : { y: 930, size: 66, maxW: 1500, lineH: 1.16, dx: 0 }, E.capBox || {});
const layoutCache = new Map();
function capLayout(cap) {
  if (layoutCache.has(cap)) return layoutCache.get(cap);
  const size = (cap.size ?? CB.size) * U, maxW = (cap.maxW ?? CB.maxW) * U, gap = size * .26;
  const lines = [[]]; let x = 0;
  for (const w of cap.words) {
    let sz = size * (w.big ? 1.3 : 1); font(sz, 900);
    let ww = ctx.measureText(w.tx).width + (w.key ? sz * .36 : 0);
    if (ww > maxW) { sz *= maxW / ww; font(sz, 900); ww = ctx.measureText(w.tx).width + (w.key ? sz * .36 : 0); }   // a long sticker shrinks to fit
    if (w.br || (x > 0 && x + ww > maxW)) { lines.push([]); x = 0; }
    lines[lines.length - 1].push({ ...w, x, ww, sz }); x += ww + gap;
  }
  const L = { size, lines: lines.map(l => ({ items: l, w: l.length ? l[l.length - 1].x + l[l.length - 1].ww : 0, h: Math.max(...l.map(i => i.sz), size) })) };
  layoutCache.set(cap, L); return L;
}
function drawCap(cap, t, amp) {
  if (t < cap.t0 || t >= cap.t1) return;
  const { size, lines } = capLayout(cap);
  const lh = size * CB.lineH, total = lines.reduce((a, l) => a + l.h * CB.lineH, 0);
  let y = (cap.y ?? CB.y) * U - total / 2 + lines[0].h * .8;
  const outK = clamp((cap.t1 - t) / .07);
  lines.forEach((ln, li) => {
    let bx = cap.align === 'left' ? (cap.x ?? 80) * U : (W - ln.w) / 2 + (cap.dx ?? CB.dx) * U;
    bx = Math.max(36 * U, Math.min(bx, W - 36 * U - ln.w));   // never past the frame edge
    for (const it of ln.items) {
      const lt = t - it.t; if (lt < 0) continue;
      const pop = lt < .11 ? lerp(it.key || it.big ? 1.28 : 1.12, 1, back(clamp(lt / .11))) : 1, a = clamp(lt / .035) * outK;
      const jit = (it.key || it.shake) ? amp * (it.shake ? 1.2 : .5) : 0;
      const jx = jit * (hash(t * 60 + it.x) - .5) * 2, jy = jit * (hash(t * 60 + it.x + 9) - .5) * 2;
      const cx = bx + it.x + it.ww / 2, cy = y - it.sz * .34;
      ctx.save(); ctx.globalAlpha = a; ctx.translate(cx + jx, cy + jy); ctx.scale(pop, pop);
      font(it.sz, 900); ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.lineJoin = 'round';
      if (it.key) {
        const k = eout(clamp((lt - .03) / .1)), w = it.ww, h = it.sz * 1.16, rot = (hash(it.x + li) - .5) * 5;
        ctx.rotate(rot * Math.PI / 180);
        const sd = 7 * U; rr(-w / 2 + sd, -h / 2 + sd, w * k, h, 8 * U); ctx.fillStyle = C.ink; ctx.fill();
        const hexk = it.key[0] === '#';   // {=#RRGGBB:word} custom sticker colour, text ink/ivory by luminance
        rr(-w / 2, -h / 2, w * k, h, 8 * U); ctx.fillStyle = KEYC[it.key] || (hexk ? it.key : C.mint); ctx.fill(); ctx.lineWidth = 5 * U; ctx.strokeStyle = C.ink; ctx.stroke();
        let tcol = KEYT[it.key] || C.ink;
        if (hexk) { const n = parseInt(it.key.slice(1), 16), lum = (.299 * (n >> 16 & 255) + .587 * (n >> 8 & 255) + .114 * (n & 255)) / 255; tcol = lum > .55 ? C.ink : C.ivory; }
        ctx.fillStyle = k > .4 ? tcol : C.ivory; ctx.fillText(it.tx, 0, it.sz * .05);
      } else {
        const sk = it.strike ? clamp((lt - .25) / .16) : 0;
        if (sk > 0) ctx.globalAlpha = a * lerp(1, .5, sk);
        ctx.lineWidth = it.sz * .2; ctx.strokeStyle = C.ink; ctx.strokeText(it.tx, 0, it.sz * .05);
        ctx.shadowColor = 'rgba(0,0,0,0.45)'; ctx.shadowBlur = 16 * U; ctx.shadowOffsetY = 6 * U;
        ctx.fillStyle = it.col ? (KEYC[it.col] || it.col) : C.ivory; ctx.fillText(it.tx, 0, it.sz * .05);
        ctx.shadowColor = 'transparent';
        if (sk > 0) { ctx.globalAlpha = a; ctx.strokeStyle = C.red; ctx.lineWidth = 8 * U; ctx.beginPath(); ctx.moveTo(-it.ww / 2, -it.sz * .02); ctx.lineTo(-it.ww / 2 + it.ww * eout(sk), -it.sz * .02); ctx.stroke(); }
        if (it.under) { const uk = eio(clamp((lt - .05) / .18)); ctx.strokeStyle = C.mint; ctx.lineWidth = 8 * U; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(-it.ww / 2, it.sz * .5); ctx.lineTo(-it.ww / 2 + it.ww * uk, it.sz * .5); ctx.stroke(); }
      }
      ctx.restore();
    }
    y += ln.h * CB.lineH;
  });
}

// ---------- graphics ----------
function inOut(g, t, din = .3, dout = .2) { const lt = t - g.t0; return { lt, k: spring(clamp(lt / din * .55)), a: clamp(lt / .08) * clamp((g.t1 - t) / dout), out: clamp((g.t1 - t) / dout) }; }

function quest(g, t) {   // QUEST tracker: title + steps that tick / fail when they happen
  if (t < g.t0 || t >= g.t1) return;
  const { lt, k, out } = inOut(g, t, .5, .25);
  const [x0, y0] = (g.at || (VERT ? [44, 150] : [48, 44])).map(v => v * U);
  const sc = g.scale ?? 1, w = (g.w ?? (VERT ? 760 : 620)) * U * sc;
  ctx.save(); ctx.translate(x0 - (1 - k) * (w + 80 * U) - (1 - out) * (w + 80 * U), y0); ctx.scale(sc, sc);
  const ww = w / sc;
  // header
  const hh = 54 * U; rr(8 * U, 8 * U, ww, hh, 8 * U); ctx.fillStyle = C.ink; ctx.fill();
  rr(0, 0, ww, hh, 8 * U); ctx.fillStyle = C.mint; ctx.fill(); ctx.lineWidth = 4 * U; ctx.strokeStyle = C.ink; ctx.stroke();
  font(30 * U, 700, 'Bahn'); ctx.fillStyle = C.ink; ctx.textBaseline = 'middle'; ctx.textAlign = 'left';
  ctx.fillText(g.kicker || 'QUEST', 18 * U, hh / 2 + 2 * U);
  const kw = ctx.measureText(g.kicker || 'QUEST').width;
  font(30 * U, 700, 'Bahn'); ctx.fillText('·  ' + g.title.toUpperCase(), 30 * U + kw, hh / 2 + 2 * U);
  // steps
  const steps = g.steps || [], rowH = 46 * U, bodyH = steps.length * rowH + 18 * U;
  if (steps.length) {
    const by = hh + 6 * U;
    rr(8 * U, by + 8 * U, ww, bodyH, 8 * U); ctx.fillStyle = C.ink; ctx.fill();
    rr(0, by, ww, bodyH, 8 * U); ctx.fillStyle = 'rgba(11,18,32,0.92)'; ctx.fill(); ctx.lineWidth = 4 * U; ctx.strokeStyle = C.ink; ctx.stroke();
    steps.forEach((s, i) => {
      const ry = by + 9 * U + i * rowH + rowH / 2, appear = s.from != null ? clamp((t - s.from) / .25) : clamp((lt - .25 - i * .08) / .25);
      if (appear <= 0) return;
      ctx.save(); ctx.globalAlpha = appear; ctx.translate((1 - eout(appear)) * -30 * U, 0);
      const done = s.at != null && t >= s.at, dk = done ? clamp((t - s.at) / .25) : 0, fail = s.state === 'fail';
      const bx = 18 * U, bs = 28 * U;
      rr(bx, ry - bs / 2, bs, bs, 5 * U); ctx.fillStyle = done ? (fail ? C.red : C.mint) : 'rgba(255,255,255,0.06)'; ctx.fill();
      ctx.lineWidth = 3 * U; ctx.strokeStyle = done ? C.ink : 'rgba(247,245,239,0.7)'; ctx.stroke();
      if (done) {
        ctx.strokeStyle = C.ink; ctx.lineWidth = 4.5 * U; ctx.lineCap = 'round'; ctx.beginPath();
        if (fail) { const e = bs * .28; ctx.moveTo(bx + e, ry - bs / 2 + e); ctx.lineTo(bx + e + (bs - 2 * e) * dk, ry - bs / 2 + e + (bs - 2 * e) * dk); if (dk > .5) { ctx.moveTo(bx + bs - e, ry - bs / 2 + e); ctx.lineTo(bx + e, ry + bs / 2 - e); } }
        else { ctx.moveTo(bx + bs * .22, ry + bs * .02); ctx.lineTo(bx + bs * .42, ry + bs * .22); if (dk > .4) ctx.lineTo(bx + bs * .8, ry - bs * .24); }
        ctx.stroke();
      }
      const pulse = done && t - s.at < .4 ? 1 + .06 * Math.sin((t - s.at) / .4 * Math.PI) : 1;
      font(27 * U, 700, 'Inter'); ctx.textAlign = 'left'; ctx.fillStyle = done && fail ? C.red : done ? C.mint : C.ivory;
      ctx.save(); ctx.translate(bx + bs + 16 * U, ry + 1 * U); ctx.scale(pulse, pulse); ctx.fillText(s.tx, 0, 0); ctx.restore();
      if (done && fail) { const tw = ctx.measureText(s.tx).width; ctx.strokeStyle = C.red; ctx.lineWidth = 3.5 * U; ctx.beginPath(); ctx.moveTo(bx + bs + 14 * U, ry + 1 * U); ctx.lineTo(bx + bs + 14 * U + (tw + 4 * U) * dk, ry + 1 * U); ctx.stroke(); }
      if (s.state === 'active' && !done) { const bl = (Math.floor(t * 2) % 2) ? 1 : .3; ctx.fillStyle = `rgba(18,234,187,${bl})`; ctx.beginPath(); ctx.arc(ww - 26 * U, ry, 7 * U, 0, 7); ctx.fill(); }
      ctx.restore();
    });
  }
  ctx.restore();
}
function meter(g, t) {   // the follower-goal bar, reused for real numbers (plan limit, progress)
  if (t < g.t0 || t >= g.t1) return;
  const { lt, k, a } = inOut(g, t, .4, .25);
  const [x, y] = g.at.map(v => v * U), w = (g.w ?? 520) * U, h = 34 * U;
  const v = lerp(g.from ?? 0, g.to, eout(clamp((lt - .3) / (g.roll ?? .8)))), p = clamp(v / (g.max ?? 100));
  ctx.save(); ctx.globalAlpha = a; ctx.translate(0, (1 - k) * 30 * U);
  font(28 * U, 700, 'Bahn'); ctx.fillStyle = C.ivory; ctx.textBaseline = 'alphabetic'; ctx.textAlign = 'left';
  ctx.shadowColor = 'rgba(0,0,0,.5)'; ctx.shadowBlur = 10 * U; ctx.fillText(g.label.toUpperCase(), x, y - 12 * U); ctx.shadowColor = 'transparent';
  rr(x + 6 * U, y + 6 * U, w, h, 6 * U); ctx.fillStyle = C.ink; ctx.fill();
  rr(x, y, w, h, 6 * U); ctx.fillStyle = C.blueD; ctx.fill();
  ctx.save(); rr(x, y, w, h, 6 * U); ctx.clip(); ctx.fillStyle = g.color ? (KEYC[g.color] || g.color) : C.mint; ctx.fillRect(x, y, w * p, h); ctx.restore();
  rr(x, y, w, h, 6 * U); ctx.lineWidth = 4 * U; ctx.strokeStyle = C.ink; ctx.stroke();
  font(44 * U, 700, 'Bahn'); ctx.textAlign = 'left'; ctx.fillStyle = C.ivory; ctx.lineWidth = 6 * U; ctx.strokeStyle = C.ink; ctx.lineJoin = 'round';
  const val = (g.fmt || '{v}').replace('{v}', (g.dec ? v.toFixed(g.dec) : Math.round(v)).toString());
  ctx.strokeText(val, x + w + 18 * U, y + h - 2 * U); ctx.fillText(val, x + w + 18 * U, y + h - 2 * U);
  ctx.restore();
}
function chip(g, t) {
  if (t < g.t0 || t >= g.t1) return; const { k, a } = inOut(g, t, .35, .2);
  sticker(g.text, g.at[0] * U, g.at[1] * U, { size: g.size ?? 30, fill: g.fill || 'mint', fam: g.fam || 'Bahn', anchor: g.anchor || 'tl', rot: g.rot ?? -2, scale: lerp(.5, 1, k), alpha: a });
}
function note(g, t) {   // lab note: mono, typed on
  if (t < g.t0 || t >= g.t1) return; const lt = t - g.t0, a = clamp((g.t1 - t) / .2);
  const n = Math.floor(clamp(lt / (g.text.length / 38)) * g.text.length), s = g.text.slice(0, n) + ((Math.floor(t * 3) % 2) && n < g.text.length + 1 ? '▌' : '');
  font((g.size ?? 24) * U, 700, 'JBM'); const tw = ctx.measureText(g.text + '▌').width; const [x, y] = g.at.map(v => v * U);
  ctx.save(); ctx.globalAlpha = a; rr(x, y, tw + 28 * U, 44 * U, 6 * U); ctx.fillStyle = 'rgba(11,18,32,0.86)'; ctx.fill();
  ctx.fillStyle = C.mint; ctx.textBaseline = 'middle'; ctx.textAlign = 'left'; ctx.fillText(s, x + 14 * U, y + 23 * U); ctx.restore();
}
function typecard(g, t) {   // a prompt re-typed as a readable card (screen text is too small to read)
  if (t < g.t0 || t >= g.t1) return;
  const { lt, k, a } = inOut(g, t, .45, .25);
  const [x, y, w] = [g.at[0] * U, g.at[1] * U, (g.w ?? 900) * U], size = (g.size ?? 34) * U, pad = 30 * U;
  font(size, 700, 'JBM');
  const words = g.text.split(' '), lines = []; let cur = '';
  for (const wd of words) { const tst = cur ? cur + ' ' + wd : wd; if (ctx.measureText(tst).width > w - 2 * pad && cur) { lines.push(cur); cur = wd; } else cur = tst; }
  if (cur) lines.push(cur);
  const lh = size * 1.38, hh = 56 * U, h = hh + pad + lines.length * lh + pad * .6;
  const nch = Math.floor(Math.max(0, lt - .35) * (g.cps ?? 45));
  ctx.save(); ctx.globalAlpha = a; ctx.translate(x + w / 2, y + h / 2); ctx.scale(lerp(.85, 1, k), lerp(.85, 1, k)); ctx.rotate((g.rot ?? -1) * Math.PI / 180); ctx.translate(-w / 2, -h / 2);
  rr(10 * U, 10 * U, w, h, 12 * U); ctx.fillStyle = C.ink; ctx.fill();
  rr(0, 0, w, h, 12 * U); ctx.fillStyle = '#121A2B'; ctx.fill(); ctx.lineWidth = 5 * U; ctx.strokeStyle = C.ink; ctx.stroke();
  ctx.save(); rr(0, 0, w, hh, 12 * U); ctx.clip(); ctx.fillStyle = C.mint; ctx.fillRect(0, 0, w, hh); ctx.restore();
  ctx.fillStyle = C.ink; font(30 * U, 700, 'Bahn'); ctx.textBaseline = 'middle'; ctx.textAlign = 'left'; ctx.fillText((g.title || 'PROMPT').toUpperCase(), pad, hh / 2 + 2 * U);
  for (const [i, c] of [C.red, C.yellow, C.ivory].entries()) { ctx.beginPath(); ctx.arc(w - pad - i * 30 * U, hh / 2, 8 * U, 0, 7); ctx.fillStyle = c; ctx.fill(); ctx.lineWidth = 3 * U; ctx.strokeStyle = C.ink; ctx.stroke(); }
  font(size, 700, 'JBM'); ctx.textBaseline = 'alphabetic';
  let left = nch;
  lines.forEach((ln, i) => {
    if (left <= 0) return; const s = ln.slice(0, left); left -= ln.length + 1;
    const hl = g.hl || [];
    ctx.fillStyle = C.ivory; let xx = pad;
    for (const part of s.split(/(\s+)/)) { const isH = hl.some(h => part.toLowerCase().includes(h)); ctx.fillStyle = isH ? C.mint : C.ivory; ctx.fillText(part, xx, hh + pad + (i + .8) * lh); xx += ctx.measureText(part).width; }
    if (left <= 0 && (Math.floor(t * 3) % 2)) { ctx.fillStyle = C.mint; ctx.fillRect(xx + 4 * U, hh + pad + i * lh + lh * .1, size * .55, size * 1.05); }
  });
  ctx.restore();
}
function tape(g, t) {   // CRASH-TEST band (series skin): yellow plate, 3 static ink chevrons at each end, mono title. Static, <= 3 stripe pairs: photosensitivity-safe
  if (t < g.t0 || t >= g.t1) return; const { k, a } = inOut(g, t, .3, .2);
  const [x, y] = g.at.map(v => v * U), h = (g.h ?? 64) * U, size = (g.size ?? 32) * U, n = 3, sw = h * .8;
  font(size, 700, 'JBM'); const tw = ctx.measureText(g.text).width, w = g.w ? g.w * U : tw + 2 * (n * sw + 34 * U);
  ctx.save(); ctx.globalAlpha = a; ctx.translate(x + (1 - k) * (g.from === 'right' ? 1 : -1) * W * .55, y); ctx.rotate((g.rot ?? -3) * Math.PI / 180);
  rr(-w / 2 + 8 * U, -h / 2 + 8 * U, w, h, 4 * U); ctx.fillStyle = C.ink; ctx.fill();
  rr(-w / 2, -h / 2, w, h, 4 * U); ctx.fillStyle = C.yellow; ctx.fill();
  ctx.save(); rr(-w / 2, -h / 2, w, h, 4 * U); ctx.clip(); ctx.fillStyle = C.ink;
  for (const side of [-1, 1]) for (let i = 0; i < n; i++) {
    const cx = side * (w / 2 - (i + .5) * sw), b = sw * .26, s = h * .42;
    ctx.beginPath(); ctx.moveTo(cx - b - s, h / 2); ctx.lineTo(cx + b - s, h / 2); ctx.lineTo(cx + b + s, -h / 2); ctx.lineTo(cx - b + s, -h / 2); ctx.closePath(); ctx.fill();
  }
  ctx.restore();
  ctx.lineWidth = 5 * U; ctx.strokeStyle = C.ink; rr(-w / 2, -h / 2, w, h, 4 * U); ctx.stroke();
  ctx.fillStyle = C.ink; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(g.text, 0, 2 * U);
  ctx.restore();
}
function stamp(g, t) {   // FAILED / LOOT / QUEST ACCEPTED — slams in
  if (t < g.t0 || t >= g.t1) return; const lt = t - g.t0, k = clamp(lt / .14), out = clamp((g.t1 - t) / .2);
  const sc = lerp(2.2, 1, eout5(k)) * (g.scale ?? 1), sz = (g.size ?? (VERT ? 120 : 130)) * U;
  const [x, y] = (g.at || [VERT ? 540 : 960, VERT ? 760 : 470]).map(v => v * U);
  font(sz, 700, 'Bahn'); const tw = ctx.measureText(g.text).width, w = tw + sz * .7, h = sz * 1.25;
  const col = KEYC[g.color || 'red'] || g.color;
  ctx.save(); ctx.globalAlpha = k * out; ctx.translate(x, y); ctx.rotate((g.rot ?? -7) * Math.PI / 180); ctx.scale(sc, sc);
  rr(-w / 2 + 12 * U, -h / 2 + 12 * U, w, h, 12 * U); ctx.fillStyle = C.ink; ctx.fill();
  rr(-w / 2, -h / 2, w, h, 12 * U); ctx.fillStyle = col; ctx.fill(); ctx.lineWidth = 7 * U; ctx.strokeStyle = C.ink; ctx.stroke();
  rr(-w / 2 + 12 * U, -h / 2 + 12 * U, w - 24 * U, h - 24 * U, 6 * U); ctx.lineWidth = 3 * U; ctx.strokeStyle = 'rgba(11,18,32,0.55)'; ctx.stroke();
  ctx.fillStyle = KEYT[g.color || 'red'] || C.ink; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(g.text, 0, sz * .05);
  if (g.sub) { font(sz * .28, 800, 'Inter'); ctx.fillStyle = C.ivory; ctx.lineWidth = 6 * U; ctx.strokeStyle = C.ink; ctx.strokeText(g.sub, 0, h / 2 + sz * .32); ctx.fillText(g.sub, 0, h / 2 + sz * .32); }
  ctx.restore();
}
function level(g, t) {   // chapter card: blue dot-grid panel wipes across the cut, LEVEL nn + title slam
  const lt = t - g.t; const dur = g.hold ?? 1.25; if (lt < -.28 || lt > dur + .32) return;
  const pin = eio(clamp((lt + .28) / .28)), pout = eio(clamp((lt - dur) / .32));
  const x = lerp(W * 1.05, 0, pin) - pout * W * 1.1;
  ctx.save(); ctx.translate(x, 0);
  ctx.drawImage(BG.blue, -M, -M);
  ctx.fillStyle = C.mint; ctx.fillRect(-26 * U, 0, 26 * U, H); ctx.fillStyle = C.ink; ctx.fillRect(-34 * U, 0, 8 * U, H);
  {   // giant outlined level number drifting on the right
    const gs = (VERT ? 760 : 980) * U; font(gs, 700, 'Bahn'); ctx.textAlign = 'right'; ctx.textBaseline = 'alphabetic';
    const gx = W - (VERT ? 30 : 60) * U + (lt * 40 * U), gy = VERT ? H - 160 * U : H + 150 * U;
    ctx.save(); ctx.globalAlpha = .9; ctx.lineWidth = 10 * U; ctx.strokeStyle = 'rgba(11,18,32,0.55)'; ctx.fillStyle = 'rgba(18,234,187,0.14)';
    ctx.fillText(g.num, gx, gy); ctx.strokeText(g.num, gx, gy); ctx.restore();
    ctx.fillStyle = C.mint; ctx.beginPath(); ctx.moveTo(W * .72, -2); ctx.lineTo(W + 2, -2); ctx.lineTo(W + 2, H * .16); ctx.closePath(); ctx.fill();
  }
  if (lt > -.05) {
    const k = spring(clamp((lt + .05) / .5));
    const cx = VERT ? 80 * U : 150 * U, cy = VERT ? 820 * U : 430 * U;
    sticker(g.kicker || ('LEVEL ' + g.num), cx, cy, { size: VERT ? 52 : 46, fam: 'JBM', fill: 'ink', color: C.mint, anchor: 'bl', rot: -3, scale: k });
    const ts = (g.size ?? (VERT ? 150 : 170)) * U; font(ts, 700, 'Bahn'); ctx.textAlign = 'left'; ctx.textBaseline = 'alphabetic';
    const lines = g.title.split('/');
    lines.forEach((ln, i) => {
      const lk = spring(clamp((lt - .06 - i * .09) / .5)); const yy = cy + (i + 1) * ts * .98 + 10 * U;
      ctx.save(); ctx.translate(cx + (1 - lk) * 160 * U, yy); ctx.lineWidth = 12 * U; ctx.lineJoin = 'round'; ctx.strokeStyle = C.ink;
      ctx.fillStyle = C.ink; ctx.fillText(ln.trim(), 9 * U, 9 * U); ctx.strokeText(ln.trim(), 0, 0); ctx.fillStyle = i === lines.length - 1 && g.lastMint ? C.mint : C.ivory; ctx.fillText(ln.trim(), 0, 0); ctx.restore();
    });
    if (g.sub) { const a = clamp((lt - .35) / .2); font(34 * U, 700, 'JBM'); ctx.globalAlpha = a; ctx.fillStyle = C.ink; ctx.fillText(g.sub, cx, cy + (lines.length + 1) * ts * .98 + 30 * U); ctx.globalAlpha = 1; }
  }
  ctx.restore();
}
function lower3(g, t) {
  if (t < g.t0 || t >= g.t1) return; const { k, out } = inOut(g, t, .45, .25);
  const [x, y] = g.at.map(v => v * U);
  ctx.save(); ctx.translate(-(1 - k) * 700 * U - (1 - out) * 700 * U, 0);
  const a = sticker(g.name, x, y, { size: VERT ? 54 : 50, fill: 'ivory', anchor: 'bl', rot: -1.5 });
  sticker(g.role, x + 24 * U, y + 8 * U, { size: VERT ? 30 : 28, fill: 'mint', fam: 'JBM', anchor: 'tl', rot: -1.5 });
  ctx.restore();
}
function circle(g, t) {   // hand-drawn ring, draws on in 0.45 s
  if (t < g.t0 || t >= g.t1) return; const lt = t - g.t0, k = eout(clamp(lt / .45)); const [x, y, w, h] = g.rect.map(v => v * U);
  ctx.save(); ctx.globalAlpha = clamp((g.t1 - t) / .2); ctx.strokeStyle = KEYC[g.color] || C.mint; ctx.lineWidth = 9 * U; ctx.lineCap = 'round';
  ctx.shadowColor = 'rgba(0,0,0,.5)'; ctx.shadowBlur = 8 * U;
  ctx.beginPath(); const a0 = -Math.PI * .6, steps = 90;
  for (let i = 0; i <= steps * k; i++) {
    const a = a0 + (i / steps) * Math.PI * 2.15, wob = 1 + .03 * Math.sin(i * .45);
    const px = x + w / 2 + Math.cos(a) * w / 2 * wob * (1 + .05 * i / steps), py = y + h / 2 + Math.sin(a) * h / 2 * wob;
    i ? ctx.lineTo(px, py) : ctx.moveTo(px, py);
  }
  ctx.stroke(); ctx.restore();
  if (g.label && lt > .4) sticker(g.label, (g.lx ?? g.rect[0]) * U, (g.ly ?? g.rect[1] - 16) * U, { size: 30, fill: g.color || 'mint', anchor: 'bl', rot: -3, scale: spring(clamp((lt - .4) / .4)) });
}
function arrow(g, t) {
  if (t < g.t0 || t >= g.t1) return; const lt = t - g.t0, k = eout(clamp(lt / .4));
  const [x0, y0] = g.from.map(v => v * U), [x1, y1] = g.to.map(v => v * U), mx = (x0 + x1) / 2 + (g.bend ?? 80) * U, my = (y0 + y1) / 2 - (g.bend ?? 80) * U;
  const P = s => [(1 - s) ** 2 * x0 + 2 * (1 - s) * s * mx + s * s * x1, (1 - s) ** 2 * y0 + 2 * (1 - s) * s * my + s * s * y1];
  ctx.save(); ctx.globalAlpha = clamp((g.t1 - t) / .2); ctx.strokeStyle = KEYC[g.color] || C.mint; ctx.lineWidth = 10 * U; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  ctx.shadowColor = 'rgba(0,0,0,.45)'; ctx.shadowBlur = 8 * U; ctx.beginPath();
  for (let i = 0; i <= 40 * k; i++) { const [px, py] = P(i / 40); i ? ctx.lineTo(px, py) : ctx.moveTo(px, py); }
  ctx.stroke();
  if (k > .95) { const [ax, ay] = P(1), [bx, by] = P(.93), ang = Math.atan2(ay - by, ax - bx); ctx.beginPath(); ctx.moveTo(ax, ay); ctx.lineTo(ax - 34 * U * Math.cos(ang - .5), ay - 34 * U * Math.sin(ang - .5)); ctx.moveTo(ax, ay); ctx.lineTo(ax - 34 * U * Math.cos(ang + .5), ay - 34 * U * Math.sin(ang + .5)); ctx.stroke(); }
  ctx.restore();
}
function spot(g, t) {   // dim everything except a rect (rounded), mint frame
  if (t < g.t0 || t >= g.t1) return; const a = clamp((t - g.t0) / .2) * clamp((g.t1 - t) / .2); const [x, y, w, h] = g.rect.map(v => v * U);
  ctx.save(); ctx.globalAlpha = a * .62; ctx.fillStyle = '#05080F'; ctx.beginPath(); ctx.rect(0, 0, W, H); if (ctx.roundRect) ctx.roundRect(x, y, w, h, 14 * U); ctx.fill('evenodd');
  ctx.globalAlpha = a; ctx.lineWidth = 6 * U; ctx.strokeStyle = C.mint; rr(x, y, w, h, 14 * U); ctx.stroke(); ctx.restore();
}
function vs(g, t) {
  if (t < g.t0 || t >= g.t1) return; const k = spring(clamp((t - g.t0) / .5)); const [x, y] = g.at.map(v => v * U), r = (g.r ?? 70) * U * k;
  ctx.save(); ctx.translate(x, y); ctx.rotate(-8 * Math.PI / 180);
  ctx.beginPath(); ctx.arc(9 * U, 9 * U, r, 0, 7); ctx.fillStyle = C.ink; ctx.fill();
  ctx.beginPath(); ctx.arc(0, 0, r, 0, 7); ctx.fillStyle = C.mint; ctx.fill(); ctx.lineWidth = 6 * U; ctx.strokeStyle = C.ink; ctx.stroke();
  font(r * .95, 700, 'Bahn'); ctx.fillStyle = C.ink; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(g.text || 'VS', 0, r * .06); ctx.restore();
}
function label(g, t) {   // small sticker label on a card (REFERENCE / CLAUDE IN UNREAL)
  if (t < g.t0 || t >= g.t1) return; const k = spring(clamp((t - g.t0) / .45));
  sticker(g.text, g.at[0] * U, g.at[1] * U, { size: g.size ?? 34, fill: g.fill || 'ivory', anchor: g.anchor || 'bl', rot: g.rot ?? -3, scale: k, fam: g.fam || 'Bahn' });
}
function hook(g, t) {   // Short header: topic line(s) at the top, keyword in a sticker
  if (t < g.t0 || t >= g.t1) return; const lt = t - g.t0, still = g.t0 <= 0 || g.instant, a = still ? 1 : clamp(lt / .15);   // a hook at t=0 is fully on frame 0 (no fade-in)
  const size = (g.size ?? 64) * U; let y = (g.y ?? 230) * U;
  for (const [li, line] of g.lines.entries()) {
    const parts = line.split(/(\{[^}]+\})/).filter(Boolean); font(size, 900);
    const ws = parts.map(p => ctx.measureText(p.replace(/[{}]/g, '')).width + (p.startsWith('{') ? size * .4 : 0)); const total = ws.reduce((a, b) => a + b, 0);
    let x = (W - total) / 2;
    parts.forEach((p, j) => {
      const pk = still ? 1 : spring(clamp((lt - li * .1 - j * .05) / .45));
      ctx.save(); ctx.globalAlpha = a; ctx.translate(x + ws[j] / 2, y - size * .34); ctx.scale(lerp(.6, 1, pk), lerp(.6, 1, pk));
      font(size, 900); ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.lineJoin = 'round';
      if (p.startsWith('{')) {
        const txt = p.slice(1, -1), w = ws[j], h = size * 1.14; ctx.rotate(-2 * Math.PI / 180);
        rr(-w / 2 + 6 * U, -h / 2 + 6 * U, w, h, 8 * U); ctx.fillStyle = C.ink; ctx.fill();
        rr(-w / 2, -h / 2, w, h, 8 * U); ctx.fillStyle = KEYC[g.key || 'mint']; ctx.fill(); ctx.lineWidth = 5 * U; ctx.strokeStyle = C.ink; ctx.stroke();
        ctx.fillStyle = KEYT[g.key || 'mint']; ctx.fillText(txt, 0, size * .05);
      } else { ctx.lineWidth = size * .2; ctx.strokeStyle = C.ink; ctx.strokeText(p, 0, size * .05); ctx.fillStyle = C.ivory; ctx.fillText(p, 0, size * .05); }
      ctx.restore(); x += ws[j];
    });
    y += size * 1.22;
  }
}
function progress(g, t) {   // follower-goal style bar for Shorts
  if (t < g.t0 || t >= g.t1) return; const p = clamp((t - g.t0) / (g.t1 - g.t0));
  const x = 44 * U, y = (g.y ?? 96) * U, w = W - 88 * U, h = 18 * U;
  rr(x + 4 * U, y + 4 * U, w, h, 5 * U); ctx.fillStyle = C.ink; ctx.fill(); rr(x, y, w, h, 5 * U); ctx.fillStyle = C.blueD; ctx.fill();
  ctx.save(); rr(x, y, w, h, 5 * U); ctx.clip(); ctx.fillStyle = C.mint; ctx.fillRect(x, y, w * p, h); ctx.restore();
  rr(x, y, w, h, 5 * U); ctx.lineWidth = 3 * U; ctx.strokeStyle = C.ink; ctx.stroke();
}
function comment(g, t) {   // editor's commentary layer: mono, grey, in parentheses — never styled as speech
  if (t < g.t0 || t >= g.t1) return; const lt = t - g.t0, a = clamp(lt / .15) * clamp((g.t1 - t) / .15);
  font((g.size ?? (VERT ? 40 : 34)) * U, 700, 'JBM');
  const L = String(g.text).split(' / '); L[0] = '(' + L[0]; L[L.length - 1] += ')';   // ' / ' = line break
  const tw = Math.max(...L.map(s => ctx.measureText(s).width)), lh = 52 * U;
  const x = g.at ? g.at[0] * U : (W - tw) / 2 + (VERT ? -60 * U : 0), y = g.at ? g.at[1] * U : (VERT ? 1010 : 860) * U;
  ctx.save(); ctx.globalAlpha = a; ctx.translate(0, (1 - eout(clamp(lt / .2))) * 14 * U);
  rr(x - 16 * U, y - 34 * U, tw + 32 * U, 52 * U + lh * (L.length - 1), 8 * U); ctx.fillStyle = 'rgba(11,18,32,0.78)'; ctx.fill();
  ctx.fillStyle = '#C9D1DE'; ctx.textBaseline = 'alphabetic'; ctx.textAlign = 'left'; L.forEach((s, i) => ctx.fillText(s, x, y + i * lh)); ctx.restore();
}
function black(g, t) { if (t < g.t0 || t >= g.t1) return; ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H); }
function flashG(g, t) { const lt = t - g.t0; if (lt < 0 || lt > (g.dur ?? .12)) return; ctx.fillStyle = `rgba(255,255,255,${(1 - lt / (g.dur ?? .12)) * (g.a ?? .85)})`; ctx.fillRect(0, 0, W, H); }
function bars(g, t) {   // cinematic letterbox for reveals
  if (t < g.t0 || t >= g.t1) return; const k = eio(clamp((t - g.t0) / .4)) * eio(clamp((g.t1 - t) / .4)); const h = (g.h ?? (VERT ? 220 : 110)) * U * k;
  ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, h); ctx.fillRect(0, H - h, W, h);
}
function endcard(g, t) {
  if (t < g.t0 || t >= g.t1) return; const lt = t - g.t0;
  const k = eio(clamp(lt / .35)); ctx.save(); ctx.globalAlpha = k; ctx.drawImage(BG.blue, -M, -M); ctx.restore();
  if (lt < .1) return;
  const cx = W / 2, cy = (VERT ? 820 : 430) * U;
  const s1 = spring(clamp((lt - .1) / .5)), s2 = spring(clamp((lt - .25) / .5)), s3 = spring(clamp((lt - .45) / .5));
  sticker(g.brand ?? 'YOUR SHOW', cx, cy, { size: VERT ? 110 : 120, fill: 'ivory', rot: -3, scale: s1, outline: 6, shadow: 10 });
  if (g.partner !== '') sticker(g.partner ?? '×  YOUR LAB', cx + (VERT ? 120 : 260) * U, cy + (VERT ? 150 : 150) * U, { size: VERT ? 90 : 96, fill: 'mint', rot: 2, scale: s2, outline: 6, shadow: 10 });
  if (g.line) { font((VERT ? 46 : 42) * U, 800); ctx.save(); ctx.globalAlpha = clamp((lt - .6) / .2); ctx.fillStyle = C.ivory; ctx.textAlign = 'center'; ctx.lineWidth = 8 * U; ctx.strokeStyle = C.ink; ctx.lineJoin = 'round';
    ctx.strokeText(g.line, cx, cy + (VERT ? 340 : 310) * U); ctx.fillText(g.line, cx, cy + (VERT ? 340 : 310) * U); ctx.restore(); }
  if (g.handle) sticker(g.handle, cx, cy + (VERT ? 440 : 400) * U, { size: VERT ? 40 : 36, fam: 'JBM', fill: 'ink', color: C.mint, scale: s3 });
}
const G = { quest, meter, chip, note, typecard, stamp, tape, level, lower3, circle, arrow, spot, vs, label, hook, progress, flash: flashG, bars, endcard, comment, black };

// ---------- post ----------
const grain = []; for (let i = 0; i < 4; i++) { const c = new OffscreenCanvas(256, 256), d = c.getContext('2d'), im = d.createImageData(256, 256); for (let j = 0; j < im.data.length; j += 4) { const v = Math.random() * 255; im.data[j] = im.data[j + 1] = im.data[j + 2] = v; im.data[j + 3] = 255; } d.putImageData(im, 0, 0); grain.push(c); }
const vign = new OffscreenCanvas(W, H); { const d = vign.getContext('2d'); const g = d.createRadialGradient(W / 2, H / 2, Math.min(W, H) * .35, W / 2, H / 2, Math.max(W, H) * .75); g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, 'rgba(0,0,0,0.38)'); d.fillStyle = g; d.fillRect(0, 0, W, H); }
function rgbSplit(px) {
  const img = ctx.getImageData(0, 0, W, H), d = img.data, src = new Uint8ClampedArray(d); const k = Math.round(px) * 4, row = W * 4;
  for (let y = 0; y < H; y++) { const o = y * row; for (let x = 0; x < row; x += 4) { const xr = Math.min(row - 4, x + k), xb = Math.max(0, x - k); d[o + x] = src[o + xr]; d[o + x + 2] = src[o + xb + 2]; } }
  ctx.putImageData(img, 0, 0);
}
function glitch(loc) {   // horizontal slice offsets for the first frames of a shot
  const img = ctx.getImageData(0, 0, W, H); const n = 9; ctx.putImageData(img, 0, 0);
  for (let i = 0; i < n; i++) { const y = Math.floor(hash(i + loc * 100) * H), h = Math.floor((10 + hash(i * 3) * 60) * U), dx = Math.floor((hash(i * 7 + loc) - .5) * 160 * U); ctx.putImageData(img, dx, 0, 0, y, W, h); }
}

const CAM = E.cam || [];
async function renderAt(t) {
  const f = Math.min(CAM.length - 1, Math.round(t * cfg.fps));
  const cam = CAM.length ? CAM[f] : [0, 0, 0, 1, 0, 0, 0];
  HOLD = cam[6] || 0;
  const s = await drawWorld(t, cam);
  // text the viewer is reading stays still; only impact frames nudge the HUD and the impact word
  const amp = Math.hypot(cam[0], cam[1]), hit = cam[4] > 0 || amp > 14 * U;
  ctx.save(); if (hit) ctx.translate(cam[0] * .35, cam[1] * .35);
  for (const g of E.gfx) if (!g.layer) G[g.type]?.(g, t);
  ctx.restore();
  for (const c of E.caps || []) drawCap(c, t, hit ? amp * .5 : 0);
  for (const g of E.gfx) if (g.layer === 'top') G[g.type]?.(g, t);
  ctx.drawImage(vign, 0, 0);
  const loc = t - s.t0;
  if (s.fx?.glitch && loc < .1) glitch(loc);
  if (cam[4] > 0) rgbSplit(cam[4] * U);
  if (cam[5] > 0) { ctx.fillStyle = `rgba(255,255,255,${cam[5]})`; ctx.fillRect(0, 0, W, H); }
  if (s.fx?.flash && loc < .12) { ctx.fillStyle = `rgba(255,255,255,${(1 - loc / .12) * .8})`; ctx.fillRect(0, 0, W, H); }
  ctx.save(); ctx.globalAlpha = .045; ctx.globalCompositeOperation = 'overlay'; const gi = grain[Math.floor(t * cfg.fps) % 4];
  for (let y = 0; y < H; y += 256) for (let x = 0; x < W; x += 256) ctx.drawImage(gi, x, y); ctx.restore();
  if (E.fadeIn && t < E.fadeIn) { ctx.fillStyle = `rgba(0,0,0,${1 - t / E.fadeIn})`; ctx.fillRect(0, 0, W, H); }
  if (E.fadeOut && t > E.dur - E.fadeOut) { ctx.fillStyle = `rgba(0,0,0,${clamp((t - (E.dur - E.fadeOut)) / E.fadeOut)})`; ctx.fillRect(0, 0, W, H); }
}
window.renderAt = renderAt;
await run(renderAt);
