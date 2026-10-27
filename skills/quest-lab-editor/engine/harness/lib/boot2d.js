// Canvas 2D harness for render.mjs. In video/stills mode run(renderAt) draws each frame; call with --flip=0.
export async function boot2d() {
  const cfg = await (await fetch('/config')).json();
  const log = m => fetch('/log', { method: 'POST', body: String(m) });
  window.addEventListener('error', e => log(`ERROR ${e.message} @ ${e.filename}:${e.lineno}`));
  window.addEventListener('unhandledrejection', e => log('REJECT ' + (e.reason?.stack ?? e.reason)));
  const canvas = document.createElement('canvas'); canvas.width = cfg.w; canvas.height = cfg.h;
  document.body.style.margin = '0'; document.body.append(canvas);
  const ctx = canvas.getContext('2d', { willReadFrequently: true });
  if (document.fonts?.ready) await document.fonts.ready;
  const emit = async name => { const img = ctx.getImageData(0, 0, cfg.w, cfg.h); await fetch('/frame' + (name ? `?name=${encodeURIComponent(name)}` : ''), { method: 'POST', body: img.data }); };
  const run = async renderAt => {
    if (cfg.stills) for (const t of cfg.stills) { await renderAt(t); await emit(`${cfg.tag}_${t.toFixed(2)}`); }
    else for (let f = 0; f < cfg.frames; f++) { await renderAt((cfg.start + f) / cfg.fps); await emit(); }
    await fetch('/finish', { method: 'POST' });
  };
  const finish = () => fetch('/finish', { method: 'POST' });
  return { cfg, canvas, ctx, log, run, finish };
}
