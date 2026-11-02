// Forty-Two Days — the Atelier, 2026-11-01; second state 2026-11-02.
// Reads data.json (built by build.py) and said.json (built by said.py from the Field's check 51).
(async function () {
  const [data, said] = await Promise.all([
    fetch('data.json').then(r => r.json()), fetch('said.json').then(r => r.json())]);
  const days = data.days, N = days.length;
  const reported = days.map(s => data.sitreps.includes(s));
  const unread = new Set(said.unread);
  const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
  const fmt = i => new Date(days[i] + 'T00:00:00Z').toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' });
  const zones = data.zones.map(z => {
    const firstRow = z.v.findIndex(x => x !== null);
    let lastRow = -1; z.v.forEach((x, i) => { if (x !== null) lastRow = i; });
    const fr = Math.min(firstRow >= 0 ? firstRow : N, days.indexOf(z.firstAny));
    const lr = Math.max(lastRow, days.indexOf(z.lastAny));
    // kind of each day: 'w' named in that day's report, 'n' no report, 'u' report not readable,
    // 'a' report does not name the zone. Known from the Field for the 22 long quiets; elsewhere
    // only whether a report was issued ('r'), or nothing for days before the first rise.
    const kind = days.map((s, i) => reported[i] ? 'r' : 'n');
    said.runs.filter(r => r.zone === z.name).forEach(r => { for (let i = 0; i < r.k.length; i++) kind[r.a + 1 + i] = r.k[i]; });
    // cumulative counts of counted days per mode, so a quiet's length is a difference
    const cum = { cal: [], rep: [], said: [] };
    let c = { cal: 0, rep: 0, said: 0 };
    for (let i = 0; i < N; i++) {
      c.cal++; if (kind[i] !== 'n') c.rep++; if (kind[i] === 'w' || kind[i] === 'r') c.said++;
      cum.cal.push(c.cal); cum.rep.push(c.rep); cum.said.push(c.said);
    }
    return Object.assign({}, z, { firstRow: fr, lastRow: lr, kind, cum });
  }).sort((a, b) => (a.rises[0] ?? 999) - (b.rises[0] ?? 999) || a.firstRow - b.firstRow);

  const sRead = document.getElementById('s-read'), sT = document.getElementById('s-t');
  const oRead = document.getElementById('o-read'), oT = document.getElementById('o-t');
  const bAfter = document.getElementById('b-after');
  const verdict = document.getElementById('verdict'), ledger = document.getElementById('ledger');
  const plane = document.getElementById('plane'), curve = document.getElementById('curve');
  const tip = document.getElementById('tip');
  let after = false, mode = 'cal';
  const MODE = { cal: 'every calendar day', rep: 'only days a report was issued', said: 'only days a report named the zone' };

  // number of counted days in (from, to]
  const count = (z, from, to) => to <= from ? 0 : z.cum[mode][to] - z.cum[mode][from];
  function lastRise(z, i) { let last = -1; for (const r of z.rises) if (r <= i) last = r; return last; }
  function state(z, d, T) {
    const last = lastRise(z, d);
    if (last < 0) return { last, quiet: null, ruled: false };
    const quiet = count(z, last, d);
    const next = z.rises.find(r => r > d);
    return { last, quiet, cal: d - last, ruled: quiet >= T, next };
  }
  const brokeAt = (z, prev, r, T) => prev !== null && count(z, prev, r - 1) >= T;

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
    const C = { rise: css('--rise'), quiet: css('--quiet'), ruled: css('--ruled'), broke: css('--broke'), gap: css('--gap'), read: css('--read'), mute: css('--mute'), line: css('--line'), panel: css('--panel') };
    g.clearRect(0, 0, W, H);
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
        const last = lastRise(z, i);
        if (i === last) continue;
        const q = count(z, last, i);
        const kd = z.kind[i], unsaid = kd === 'n' || kd === 'u' || kd === 'a';
        g.globalAlpha = (fade ? 0.35 : 1) * (unsaid ? 0.45 : 1);
        g.fillStyle = q >= T ? C.ruled : C.quiet;
        g.fillRect(x0 + i * cw, y + 1, Math.ceil(cw), h - 2);
        if (unsaid && cw >= 2.5) { // a hollow day: nobody wrote this zone's count on it
          g.globalAlpha = fade ? 0.35 : 1; g.fillStyle = C.panel;
          g.fillRect(x0 + i * cw + cw * 0.3, y + h / 2 - 1, Math.max(1, cw * 0.4), 2);
        }
      }
      g.globalAlpha = 1;
      z.rises.forEach((r, j) => {
        if (r > d && !after) return;
        const prev = j ? z.rises[j - 1] : null;
        const broke = brokeAt(z, prev, r, T);
        g.fillStyle = broke ? C.broke : C.rise;
        g.globalAlpha = r > d && !broke ? 0.45 : 1;
        g.fillRect(x0 + r * cw - (broke ? 1 : 0), y - (broke ? 1 : 0), Math.max(broke ? 3.5 : 2, cw * 0.7), h + (broke ? 2 : 0));
      });
      g.globalAlpha = 1;
    });
    g.fillStyle = C.read; g.fillRect(x0 + d * cw + cw / 2 - 1, top - 6, 2, H - top + 6);
  }

  function writeVerdict() {
    const d = +sRead.value, T = +sT.value;
    let seen = 0; const ruled = [], broke = [];
    zones.forEach(z => { const s = state(z, d, T); if (s.last >= 0) { seen++; if (s.ruled) { ruled.push([z, s]); if (s.next !== undefined) broke.push(z.name); } } });
    const susp = zones.filter(z => !z.rises.length && z.firstRow <= d).length;
    const unit = mode === 'cal' ? 'quiet days' : mode === 'rep' ? 'quiet days with a report' : 'quiet days on which a report named the zone';
    let t = `On ${fmt(d)}, ${seen} zones have had a confirmed case. After ${T} ${unit}, the rule calls <b>${ruled.length}</b> of them quiet.`;
    if (susp) t += ` ${susp === 2 ? 'Two zones' : 'One zone'} with no confirmed case ${susp === 2 ? 'stand' : 'stands'} outside the rule (dashed).`;
    if (ruled.length && !after) t += ' Nothing on this day says which of them will hold. <i>Show what came after.</i>';
    else if (ruled.length) t += ` By 29 Oct 2026, <b style="color:var(--broke)">${broke.length}</b> of them had a new confirmed case${broke.length ? ' (' + broke.join(', ') + ')' : ''}, and ${ruled.length - broke.length} were still quiet, which the record's last day cannot call either way.`;
    verdict.innerHTML = t;
    // the ledger: what each verdict of the day rests on
    if (!ruled.length) { ledger.innerHTML = ''; return; }
    const maxTot = Math.max(...ruled.map(([, s]) => s.cal));
    ledger.innerHTML = `<p class="small">What each of these verdicts rests on: its quiet so far, day by day from the last rise, by who wrote it. Green: a report named the zone. Ochre: the report did not name it. Grey: a report that could not be read. Hollow: no report at all. The black mark is the day the count you chose reached ${T}.</p>` + ruled.map(([z, s]) => {
      const n = { w: 0, n: 0, u: 0, a: 0, r: 0 }; let cells = '', c = 0, mark = -1;
      for (let i = s.last + 1; i <= d; i++) {
        const k = z.kind[i]; n[k]++;
        if (mode === 'cal' || (mode === 'rep' && k !== 'n') || (mode === 'said' && (k === 'w' || k === 'r'))) { c++; if (c === T) mark = i; }
        cells += `<span class="seg ${k}${i === mark ? ' mark' : ''}"></span>`;
      }
      const known = n.r === 0, hit = s.next !== undefined && after ? ' broke' : '';
      return `<div class="lrow${hit}"><span class="lz">${z.name}</span><span class="lbar" style="width:${(100 * s.cal / maxTot).toFixed(1)}%">${cells}</span>` +
        `<span class="ln">${s.cal} days: ${known ? `<b>${n.w}</b> named` : `${n.r} with a report`}${n.a ? `, ${n.a} not named` : ''}${n.u ? `, ${n.u} unread` : ''}${n.n ? `, ${n.n} no report` : ''}</span></div>`;
    }).join('');
  }

  function curvePoints() {
    const pts = [];
    for (let T = 7; T <= 120; T++) {
      let broke = 0, held = 0;
      zones.forEach(z => {
        const r = z.rises;
        for (let j = 0; j + 1 < r.length; j++) if (count(z, r[j], r[j + 1] - 1) >= T) broke++;
        if (r.length && count(z, r[r.length - 1], N - 1) >= T) held++;
      });
      pts.push({ T, broke, held });
    }
    return pts;
  }
  function drawCurve() {
    const T = +sT.value, W = curve.clientWidth, H = 240, dpr = window.devicePixelRatio || 1;
    curve.width = W * dpr; curve.height = H * dpr;
    const g = curve.getContext('2d'); g.setTransform(dpr, 0, 0, dpr, 0, 0); g.clearRect(0, 0, W, H);
    const c = curvePoints(), L = 34, R = 10, Tp = 12, B = 28;
    const maxY = Math.max(...data.curve.map(p => Math.max(p.broke, p.held)));
    const X = t => L + (t - c[0].T) / (c[c.length - 1].T - c[0].T) * (W - L - R);
    const Y = v => H - B - v / maxY * (H - B - Tp);
    g.strokeStyle = css('--line'); g.fillStyle = css('--mute'); g.font = '11px system-ui,sans-serif';
    for (let v = 0; v <= maxY; v += 10) { g.beginPath(); g.moveTo(L, Y(v)); g.lineTo(W - R, Y(v)); g.stroke(); g.fillText(v, 4, Y(v) + 4); }
    for (let t = 14; t <= 120; t += 14) g.fillText(t + ' d', X(t) - 10, H - 10);
    [42, 63, 90].forEach(t => { g.setLineDash([3, 3]); g.strokeStyle = css('--mute'); g.beginPath(); g.moveTo(X(t), Tp); g.lineTo(X(t), H - B); g.stroke(); g.setLineDash([]); });
    const line = (pts, k, col, w, dash) => { g.strokeStyle = col; g.lineWidth = w; g.setLineDash(dash || []); g.beginPath(); pts.forEach((p, i) => i ? g.lineTo(X(p.T), Y(p[k])) : g.moveTo(X(p.T), Y(p[k]))); g.stroke(); g.lineWidth = 1; g.setLineDash([]); };
    if (mode !== 'cal') { g.globalAlpha = 0.5; line(data.curve, 'broke', css('--broke'), 1, [2, 3]); g.globalAlpha = 1; }
    line(c, 'held', css('--mute'), 2); line(c, 'broke', css('--broke'), 2);
    g.fillStyle = css('--read'); g.fillRect(X(T) - 1, Tp, 2, H - B - Tp);
    const p = c.find(q => q.T === T);
    const unit = mode === 'cal' ? 'days' : mode === 'rep' ? 'days with a report' : 'days on which a report named the zone';
    document.getElementById('curve-read').innerHTML = `Quiet for at least ${T} ${unit} and then broken: <b style="color:var(--broke)">${p.broke}</b> stretches. Quiet for at least ${T} ${unit} and still running on 29 Oct: <b>${p.held}</b>. Dashed lines: 42, 63 and 90.` + (mode !== 'cal' ? ' The thin dotted red line is the calendar count, for comparison.' : '');
  }

  function render() {
    oRead.textContent = fmt(+sRead.value); oT.textContent = sT.value + ' days';
    document.querySelectorAll('.preset').forEach(b => b.classList.toggle('on', b.dataset.t === sT.value));
    document.querySelectorAll('.mode').forEach(b => b.setAttribute('aria-pressed', b.dataset.m === mode));
    drawPlane(); writeVerdict(); drawCurve();
  }
  sRead.addEventListener('input', render); sT.addEventListener('input', render);
  bAfter.addEventListener('click', () => { after = !after; bAfter.setAttribute('aria-checked', after); render(); });
  document.querySelectorAll('.preset').forEach(b => b.addEventListener('click', () => { sT.value = b.dataset.t; render(); }));
  document.querySelectorAll('.mode').forEach(b => b.addEventListener('click', () => { mode = b.dataset.m; render(); }));
  const KIND = { w: 'a report named the zone that day', r: 'a report was issued that day', a: 'the report that day does not name the zone; the transcription keeps the previous number', u: 'a report is listed for that day, but it could not be read', n: 'no report was issued that day; the count is carried, not written' };
  plane.addEventListener('mousemove', e => {
    const r = plane.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top;
    const k = Math.floor((y - geo.top) / geo.rowH), i = Math.floor((x - geo.x0) / geo.cw);
    if (k < 0 || k >= zones.length || i < 0 || i >= N) { tip.hidden = true; return; }
    const z = zones[k], d = +sRead.value;
    if (i > d && !after) { tip.hidden = true; return; }
    const last = lastRise(z, i), v = z.v[i];
    const sr = said.sitrepOf[days[i]];
    tip.innerHTML = `<b>${z.name}</b>, ${fmt(i)}<br>` + (!z.rises.length ? (v === 0 ? '0 confirmed, written' : 'no confirmed case written') + `; no row of any kind after ${fmt(days.indexOf(z.lastAny))}` :
      (v === null ? 'no row this day' : `${v} confirmed, cumulative`) + (last >= 0 && i > last ? `<br>${i - last} days since the count last rose, ${count(z, last, i)} of them counted` : '') +
      (last >= 0 && i > last ? `<br><i>${KIND[z.kind[i]]}</i>${z.kind[i] === 'w' && sr ? ` (sitrep ${sr.join(', ')})` : ''}` : ''));
    tip.hidden = false; tip.style.left = Math.max(0, Math.min(x + 12, r.width - 290)) + 'px'; tip.style.top = (y + 14) + 'px';
  });
  plane.addEventListener('mouseleave', () => tip.hidden = true);
  window.addEventListener('resize', render);
  matchMedia('(prefers-color-scheme: dark)').addEventListener('change', render);
  render();
})();
