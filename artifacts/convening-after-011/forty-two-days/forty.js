// Forty-Two Days — the Atelier, 2026-11-01. Reads data.json (built by build.py).
(async function () {
  const data = await (await fetch('data.json')).json();
  const days = data.days, N = days.length;
  const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
  const fmt = i => new Date(days[i] + 'T00:00:00Z').toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' });
  const zones = data.zones.map(z => {
    const firstRow = z.v.findIndex(x => x !== null);
    let lastRow = -1; z.v.forEach((x, i) => { if (x !== null) lastRow = i; });
    // suspected-only zones: take their row span from lastSusp
    const fr = Math.min(firstRow >= 0 ? firstRow : N, days.indexOf(z.firstAny));
    const lr = Math.max(lastRow, days.indexOf(z.lastAny));
    return Object.assign({}, z, { firstRow: fr, lastRow: lr });
  }).sort((a, b) => (a.rises[0] ?? 999) - (b.rises[0] ?? 999) || a.firstRow - b.firstRow);

  const sRead = document.getElementById('s-read'), sT = document.getElementById('s-t');
  const oRead = document.getElementById('o-read'), oT = document.getElementById('o-t');
  const bAfter = document.getElementById('b-after');
  const verdict = document.getElementById('verdict');
  const plane = document.getElementById('plane'), curve = document.getElementById('curve');
  const tip = document.getElementById('tip');
  let after = false;

  function state(z, d, T) {
    let last = -1; for (const r of z.rises) if (r <= d) last = r;
    if (last < 0) return { last, quiet: null, ruled: false };
    const quiet = d - last;
    const next = z.rises.find(r => r > d);
    return { last, quiet, ruled: quiet >= T, next };
  }

  let geo = {};
  function drawPlane() {
    const d = +sRead.value, T = +sT.value;
    const W = plane.clientWidth, narrow = W < 600;
    const labelW = narrow ? 0 : 96, rowH = narrow ? 7 : 9, pad = 6, top = 18;
    const H = top + zones.length * rowH + pad;
    const dpr = window.devicePixelRatio || 1;
    plane.width = W * dpr; plane.height = H * dpr; plane.style.height = H + 'px';
    const g = plane.getContext('2d'); g.setTransform(dpr, 0, 0, dpr, 0, 0);
    const x0 = labelW + 4, cw = (W - x0 - 6) / N;
    geo = { x0, cw, top, rowH, narrow };
    const C = { rise: css('--rise'), quiet: css('--quiet'), ruled: css('--ruled'), broke: css('--broke'), gap: css('--gap'), read: css('--read'), mute: css('--mute'), line: css('--line') };
    g.clearRect(0, 0, W, H);
    // month ticks
    g.font = '11px system-ui,sans-serif'; g.fillStyle = C.mute; g.strokeStyle = C.line; g.lineWidth = 1;
    days.forEach((s, i) => { if (s.endsWith('-01')) { const x = x0 + i * cw; g.beginPath(); g.moveTo(x, top - 4); g.lineTo(x, H); g.stroke(); g.fillText(new Date(s + 'T00:00:00Z').toLocaleDateString('en-GB', { month: 'short', timeZone: 'UTC' }), x + 2, 11); } });
    zones.forEach((z, k) => {
      const y = top + k * rowH, h = rowH - 2;
      if (!narrow) { g.fillStyle = C.mute; g.font = '10px system-ui,sans-serif'; g.fillText(z.name.slice(0, 15), 0, y + h); }
      if (!z.rises.length) { // suspected only
        g.fillStyle = C.gap; g.fillRect(x0 + z.firstRow * cw, y, (z.lastRow - z.firstRow + 1) * cw, h);
        g.strokeStyle = C.mute; g.setLineDash([2, 2]); g.strokeRect(x0 + z.firstRow * cw + .5, y + .5, Math.max(1, (z.lastRow - z.firstRow + 1) * cw - 1), h - 1); g.setLineDash([]);
        return;
      }
      for (let i = z.rises[0]; i < N; i++) {
        const fade = i > d;
        if (fade && !after) break;
        let last = -1; for (const r of z.rises) if (r <= i) last = r;
        const q = i - last;
        g.globalAlpha = fade ? 0.35 : 1;
        g.fillStyle = q >= T ? C.ruled : C.quiet;
        if (q > 0) g.fillRect(x0 + i * cw, y + 1, Math.ceil(cw), h - 2);
        if (z.v[i] === null) { g.fillStyle = C.gap; g.fillRect(x0 + i * cw, y + h / 2 - 1, Math.ceil(cw), 2); }
      }
      g.globalAlpha = 1;
      z.rises.forEach((r, j) => {
        if (r > d && !after) return;
        const prev = j ? z.rises[j - 1] : null;
        const broke = prev !== null && r - prev > T;
        g.fillStyle = broke ? C.broke : C.rise;
        g.globalAlpha = r > d && !broke ? 0.45 : 1;
        g.fillRect(x0 + r * cw - (broke ? 1 : 0), y - (broke ? 1 : 0), Math.max(broke ? 3.5 : 2, cw * 0.7), h + (broke ? 2 : 0));
      });
      g.globalAlpha = 1;
    });
    if (!after) { g.fillStyle = css('--panel'); g.globalAlpha = 0.0; }
    g.globalAlpha = 1; g.fillStyle = C.read; g.fillRect(x0 + d * cw + cw / 2 - 1, top - 6, 2, H - top + 6);
  }

  function writeVerdict() {
    const d = +sRead.value, T = +sT.value;
    let seen = 0, ruled = [], broke = [];
    zones.forEach(z => { const s = state(z, d, T); if (s.last >= 0) { seen++; if (s.ruled) { ruled.push(z.name); if (s.next !== undefined) broke.push(z.name); } } });
    const susp = zones.filter(z => !z.rises.length && z.firstRow <= d).length;
    let t = `On ${fmt(d)}, ${seen} zones have had a confirmed case. After ${T} quiet days the rule calls <b>${ruled.length}</b> of them quiet.`;
    if (susp) t += ` ${susp === 2 ? 'Two zones' : 'One zone'} with no confirmed case ${susp === 2 ? 'stand' : 'stands'} outside the rule (dashed).`;
    if (!ruled.length) t += '';
    else if (!after) t += ' Nothing on this day says which of them will hold. <i>Show what came after.</i>';
    else t += ` By 29 Oct 2026, <b style="color:var(--broke)">${broke.length}</b> of them had a new confirmed case${broke.length ? ' (' + broke.join(', ') + ')' : ''}, and ${ruled.length - broke.length} were still quiet, which the record's last day cannot call either way.`;
    verdict.innerHTML = t;
  }

  function drawCurve() {
    const T = +sT.value, W = curve.clientWidth, H = 240, dpr = window.devicePixelRatio || 1;
    curve.width = W * dpr; curve.height = H * dpr;
    const g = curve.getContext('2d'); g.setTransform(dpr, 0, 0, dpr, 0, 0); g.clearRect(0, 0, W, H);
    const c = data.curve, L = 34, R = 10, Tp = 12, B = 28;
    const maxY = Math.max(...c.map(p => Math.max(p.broke, p.held)));
    const X = t => L + (t - c[0].T) / (c[c.length - 1].T - c[0].T) * (W - L - R);
    const Y = v => H - B - v / maxY * (H - B - Tp);
    g.strokeStyle = css('--line'); g.fillStyle = css('--mute'); g.font = '11px system-ui,sans-serif';
    for (let v = 0; v <= maxY; v += 10) { g.beginPath(); g.moveTo(L, Y(v)); g.lineTo(W - R, Y(v)); g.stroke(); g.fillText(v, 4, Y(v) + 4); }
    for (let t = 14; t <= 120; t += 14) g.fillText(t + ' d', X(t) - 10, H - 10);
    [42, 63, 90].forEach(t => { g.setLineDash([3, 3]); g.strokeStyle = css('--mute'); g.beginPath(); g.moveTo(X(t), Tp); g.lineTo(X(t), H - B); g.stroke(); g.setLineDash([]); });
    const line = (k, col) => { g.strokeStyle = col; g.lineWidth = 2; g.beginPath(); c.forEach((p, i) => i ? g.lineTo(X(p.T), Y(p[k])) : g.moveTo(X(p.T), Y(p[k]))); g.stroke(); g.lineWidth = 1; };
    line('held', css('--mute')); line('broke', css('--broke'));
    g.fillStyle = css('--read'); g.fillRect(X(T) - 1, Tp, 2, H - B - Tp);
    const p = c.find(q => q.T === T);
    document.getElementById('curve-read').innerHTML = `Quiet for longer than ${T} days and then broken: <b style="color:var(--broke)">${p.broke}</b> stretches. Quiet for ${T} days or more and still running on 29 Oct: <b>${p.held}</b>. Dashed lines: 42, 63 and 90 days.`;
  }

  function render() {
    oRead.textContent = fmt(+sRead.value); oT.textContent = sT.value + ' days';
    document.querySelectorAll('.preset').forEach(b => b.classList.toggle('on', b.dataset.t === sT.value));
    drawPlane(); writeVerdict(); drawCurve();
  }
  sRead.addEventListener('input', render); sT.addEventListener('input', render);
  bAfter.addEventListener('click', () => { after = !after; bAfter.setAttribute('aria-checked', after); render(); });
  document.querySelectorAll('.preset').forEach(b => b.addEventListener('click', () => { sT.value = b.dataset.t; render(); }));
  plane.addEventListener('mousemove', e => {
    const r = plane.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top;
    const k = Math.floor((y - geo.top) / geo.rowH), i = Math.floor((x - geo.x0) / geo.cw);
    if (k < 0 || k >= zones.length || i < 0 || i >= N) { tip.hidden = true; return; }
    const z = zones[k], d = +sRead.value;
    if (i > d && !after) { tip.hidden = true; return; }
    let last = -1; for (const q of z.rises) if (q <= i) last = q;
    const v = z.v[i];
    tip.innerHTML = `<b>${z.name}</b>, ${fmt(i)}<br>` + (!z.rises.length ? (v === 0 ? '0 confirmed, written' : 'no confirmed case written') + `; no row of any kind after ${fmt(days.indexOf(z.lastAny))}` :
      (v === null ? 'no row this day' : `${v} confirmed, cumulative`) + (last >= 0 ? `<br>${i - last} days since the count last rose` : ''));
    tip.hidden = false; tip.style.left = Math.min(x + 12, r.width - 290) + 'px'; tip.style.top = (y + 14) + 'px';
  });
  plane.addEventListener('mouseleave', () => tip.hidden = true);
  window.addEventListener('resize', render);
  matchMedia('(prefers-color-scheme: dark)').addEventListener('change', render);
  render();
})();
