(() => {
  "use strict";
  const E = window.EDGE, DAY = 864e5;
  const toD = s => Date.UTC(+s.slice(0, 4), +s.slice(5, 7) - 1, +s.slice(8, 10));
  const iso = t => new Date(t).toISOString().slice(0, 10);
  const nice = t => new Date(t).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" });
  const HOLE = toD(E.holeLast);
  const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
  const $ = id => document.getElementById(id);
  let rec = "bdbv", edgeT = toD(E.records.bdbv[1]), hole = false, probeDay = null;

  const Q = E.quiets.map(q => ({ ...q, f0: toD(q.f) }));
  function events(r, edge, h) {
    const out = [];
    for (const q of Q) {
      if (q.rec !== r) continue;
      let through = Math.round((edge - q.f0) / DAY) + 1;
      if (h && q.f0 <= HOLE && q.f0 + q.L * DAY > HOLE) through = Math.min(through, Math.round((HOLE - q.f0) / DAY) + 1);
      if (q.b && q.L + 1 <= through) out.push({ t: q.L + 1, e: 1, q });
      else { const t = Math.min(q.L, through); if (t >= 42) out.push({ t, e: 0, q, through }); }
    }
    return out;
  }
  function km(ev) {
    let S = 1, n = ev.length; const steps = [];
    const ts = [...new Set(ev.map(x => x.t))].sort((a, b) => a - b);
    for (const t of ts) {
      const d = ev.filter(x => x.t === t && x.e).length;
      if (d) { S *= 1 - d / n; steps.push([t, S]); }
      n -= ev.filter(x => x.t === t).length;
    }
    let last = ev[0];
    for (const x of ev) if (x.t > last.t || (x.t === last.t && x.e < last.e)) last = x;
    return { steps, tStar: last.t, isLoss: last.e === 0, pStar: steps.length ? steps[steps.length - 1][1] : 1 };
  }
  const stepAt = (steps, t) => { let s = 1; for (const [u, v] of steps) { if (u <= t) s = v; else break; } return s; };

  // ---- the calendar ----
  const cal = $("cal"), cur = $("curve"), rng = $("edge");
  function size(c) {
    const dpr = window.devicePixelRatio || 1, w = c.clientWidth, h = +c.getAttribute("height");
    c.width = w * dpr; c.height = h * dpr; c.style.height = h + "px";
    const g = c.getContext("2d"); g.setTransform(dpr, 0, 0, dpr, 0, 0); return [g, w, h];
  }
  const span = () => { const [a, b] = E.records[rec]; return [toD(a), toD(b)]; };
  function drawCal() {
    const [g, w, h] = size(cal), [a, b] = span(), pad = 8, top = 18, bot = 22;
    const X = t => pad + (t - a) / (b - a) * (w - 2 * pad);
    const qs = Q.filter(q => q.rec === rec).sort((p, q) => p.f0 - q.f0);
    const rh = (h - top - bot) / qs.length;
    g.clearRect(0, 0, w, h);
    // the hole
    if (rec === "kivu") {
      const h0 = toD(E.records.kivuHole[0]) + DAY, h1 = toD(E.records.kivuHole[1]);
      g.fillStyle = css("--line"); g.globalAlpha = hole ? .9 : .45; g.fillRect(X(h0), top, X(h1) - X(h0), h - top - bot); g.globalAlpha = 1;
      g.fillStyle = css("--mute"); g.font = "11px system-ui,sans-serif"; g.textAlign = "center";
      g.textAlign = "right"; g.fillText("94 days, no report", Math.min(w - pad, X(h1)), top - 6);
    }
    const lw = Math.max(1.2, Math.min(5, rh * .6));
    qs.forEach((q, i) => {
      const y = top + (i + .5) * rh, end = q.f0 + (q.L - 1) * DAY;
      // with the hole as an edge, a quiet watched across it is cut on the last report day before it
      const cutT = (rec === "kivu" && hole && q.f0 <= HOLE && end + DAY > HOLE) ? Math.min(edgeT, HOLE) : edgeT;
      const caseT = q.f0 + q.L * DAY, seen = Math.min(end, cutT);
      g.lineWidth = lw; g.lineCap = "butt";
      if (end > cutT) { // what came after the edge
        g.strokeStyle = css("--nb"); g.globalAlpha = .45;
        g.beginPath(); g.moveTo(X(Math.max(q.f0, cutT)), y); g.lineTo(X(end), y); g.stroke();
        if (q.b) { g.fillStyle = css("--case"); g.beginPath(); g.arc(X(caseT), y, lw * .7 + 1, 0, 7); g.fill(); }
        g.globalAlpha = 1;
      }
      if (q.f0 > cutT) return;
      const reached = Math.round((cutT - q.f0) / DAY) + 1 >= 42 || (q.b && caseT <= cutT);
      g.strokeStyle = css("--w"); g.globalAlpha = reached ? 1 : .35;
      g.beginPath(); g.moveTo(X(q.f0), y); g.lineTo(X(seen), y); g.stroke(); g.globalAlpha = 1;
      if (q.b && caseT <= cutT) { g.fillStyle = css("--case"); g.beginPath(); g.arc(X(caseT), y, lw * .7 + 1.2, 0, 7); g.fill(); }
      else if (reached) { g.strokeStyle = css("--cut"); g.lineWidth = 1.6; g.beginPath(); g.arc(X(seen), y, lw * .7 + 1.5, 0, 7); g.stroke(); }
    });
    // the edge
    const ex = X(edgeT);
    g.strokeStyle = css("--cut"); g.lineWidth = 2; g.beginPath(); g.moveTo(ex, 4); g.lineTo(ex, h - bot + 4); g.stroke();
    g.fillStyle = css("--cut"); g.font = "600 12px system-ui,sans-serif";
    g.textAlign = ex > w - 90 ? "right" : "left"; g.fillText("the edge · " + nice(edgeT), ex + (ex > w - 90 ? -6 : 6), h - 6);
    g.fillStyle = css("--mute"); g.font = "11px system-ui,sans-serif"; g.textAlign = "left";
    if (ex > 120) g.fillText(nice(a), pad, h - 6);
  }

  // ---- the curves ----
  let geom = null;
  function drawCurve(st) {
    const [g, w, h] = size(cur), L = 34, R = 70, T = 26, B = 30;
    const ev = st.ev, maxT = Math.max(...Q.filter(q => q.rec === rec).map(q => q.L + 1));
    const X = t => L + (t - 42) / (maxT - 42) * (w - L - R), Y = p => T + (1 - p) * (h - T - B);
    geom = { X, L, R, w, maxT };
    g.clearRect(0, 0, w, h);
    g.strokeStyle = css("--line"); g.lineWidth = 1; g.fillStyle = css("--mute"); g.font = "11px system-ui,sans-serif";
    for (const p of [0, .25, .5, .75, 1]) { g.beginPath(); g.moveTo(L, Y(p)); g.lineTo(w - R, Y(p)); g.stroke(); g.textAlign = "right"; g.fillText(Math.round(p * 100), L - 5, Y(p) + 4); }
    g.textAlign = "left"; g.fillText("still quiet, in 100 quiets that reached 42 days", L, 12);
    g.textAlign = "center";
    const tick = [20, 40, 50, 100, 200, 400].find(s => (w - L - R) / ((maxT - 42) / s) >= 58) || 400;
    for (let t = Math.ceil(42 / tick) * tick; t <= maxT; t += tick) g.fillText("day " + t, X(t), h - 10);
    g.fillText("42", X(42), h - 10);
    // lost: hatched band past t*
    const k = st.km;
    if (k.isLoss) {
      const x0 = X(k.tStar), x1 = X(maxT);
      g.save(); g.beginPath(); g.rect(x0, Y(k.pStar), x1 - x0, Y(0) - Y(k.pStar)); g.clip();
      g.strokeStyle = css("--mute"); g.globalAlpha = .45; g.lineWidth = 1;
      for (let x = x0 - 300; x < x1 + 300; x += 7) { g.beginPath(); g.moveTo(x, Y(0)); g.lineTo(x + 300, Y(0) - 300); g.stroke(); }
      g.restore();
      g.fillStyle = css("--mute"); g.textAlign = "left"; g.font = "italic 13px Georgia,serif";
      if (x1 - x0 > 70) g.fillText("undefined", x0 + 6, Y(k.pStar / 2) + 4);
    }
    const stepLine = (steps, until, col, dash, wdt) => {
      g.strokeStyle = col; g.lineWidth = wdt; g.setLineDash(dash); g.beginPath();
      let s = 1; g.moveTo(X(42), Y(1));
      for (const [t, v] of steps) { if (t > until) break; g.lineTo(X(t), Y(s)); g.lineTo(X(t), Y(v)); s = v; }
      g.lineTo(X(until), Y(s)); g.stroke(); g.setLineDash([]); return s;
    };
    const lab = (txt, y, col) => { g.fillStyle = col; g.font = "600 12px system-ui,sans-serif"; g.textAlign = "left"; g.fillText(txt, w - R + 6, y + 4); };
    // carried: cut quiets never break
    const n = ev.length, deaths = ev.filter(x => x.e).map(x => x.t).sort((a, b) => a - b);
    const carried = [], out = []; let dc = 0;
    const nb = deaths.length;
    for (const t of [...new Set(deaths)]) { dc += deaths.filter(u => u === t).length; carried.push([t, 1 - dc / n]); out.push([t, nb ? 1 - dc / nb : 1]); }
    const lc = stepLine(carried, maxT, css("--held"), [], 2.2); lab("carried", Y(lc), css("--held"));
    const lo = stepLine(out, nb ? deaths[nb - 1] : 42, css("--case"), [6, 4], 2); lab("left out", Y(lo) + (Math.abs(Y(lo) - Y(lc)) < 14 ? 14 : 0), css("--case"));
    const ll = stepLine(k.steps, k.tStar, css("--fg"), [], 2.4);
    g.fillStyle = css("--fg"); g.beginPath(); g.arc(X(k.tStar), Y(ll), 3.5, 0, 7); g.fill();
    if (probeDay != null && probeDay >= 42 && probeDay <= maxT) {
      g.strokeStyle = css("--you"); g.lineWidth = 1; g.setLineDash([2, 3]); g.beginPath(); g.moveTo(X(probeDay), T); g.lineTo(X(probeDay), Y(0)); g.stroke(); g.setLineDash([]);
    }
    st.curves = { carried, out, nb };
  }

  const pct = p => Math.round(p * 100);
  function render() {
    const ev = events(rec, edgeT, rec === "kivu" && hole);
    drawCal();
    const read = $("read");
    if (!ev.length) {
      read.innerHTML = "At this edge no quiet has yet reached 42 days. There is nothing to read.";
      const [g, w, h] = size(cur); g.clearRect(0, 0, w, h);
      $("sCarried").textContent = $("sLost").textContent = $("sOut").textContent = ""; return;
    }
    const st = { ev, km: km(ev) }; drawCurve(st);
    const cut = ev.filter(x => !x.e), later = cut.filter(x => x.q.b).length, broke = ev.length - cut.length;
    const realEnd = edgeT >= toD(E.records[rec][1]);
    read.innerHTML = `Edge: <b>${nice(edgeT)}</b>. <b>${ev.length}</b> quiets had reached 42 days: <b>${broke}</b> broke before the edge, <b>${cut.length}</b> are cut by it. ` +
      (realEnd ? "This is the record's own last day: what the cut quiets become, nobody here can know."
        : `Of the ${cut.length} quiets this edge would carry as over, <b>${later}</b> broke later in the record.`);
    const k = st.km;
    $("sCarried").innerHTML = `No quiet the edge cut ever breaks. The curve never falls below <b>${pct(cut.length / ev.length)} in 100</b>, and it runs on for ever.`;
    $("sLost").innerHTML = k.isLoss ? `Each cut quiet counts while it was watched. The last cut one is on day <b>${k.tStar}</b>; there the estimate is <b>${pct(k.pStar)} in 100</b>. Past it: anywhere between 0 and ${pct(k.pStar)}.`
      : `The longest quiet broke, on day ${k.tStar}; the estimate reaches 0 there.`;
    const lastBreak = st.curves.nb ? Math.max(...ev.filter(x => x.e).map(x => x.t)) : null;
    $("sOut").innerHTML = st.curves.nb ? `Only the <b>${st.curves.nb}</b> finished quiets speak, and every one of them broke. The curve reaches 0 on day <b>${lastBreak}</b>.`
      : "No quiet has finished; this rule has nothing to say at all.";
    $("probe").textContent = probeDay == null ? "point at the curves to read a day"
      : `day ${probeDay}: carried ${pct(stepAt(st.curves.carried, probeDay))} · lost ${probeDay > k.tStar && k.isLoss ? "undefined" : pct(stepAt(k.steps, probeDay))} · left out ${st.curves.nb && probeDay <= lastBreak ? pct(stepAt(st.curves.out, probeDay)) : st.curves.nb ? 0 : "—"} in 100`;
    window.__edgeState = { edge: iso(edgeT), n: ev.length, broke, cut: cut.length, cutLaterBroke: later, tStar: k.tStar, pStar: Math.round(k.pStar * 1000) / 1000 };
  }

  // ---- facts stated in prose, from build.py's asserted figures ----
  function facts() {
    const F = E.facts;
    $("facts").innerHTML = `At the 2026 record's own last day, 29 October, the three rules disagree as far as they can: carried never falls below ${pct(F.full26.floor)} in 100, left out reaches 0, and the lost curve stops on day ${F.full26.tStar} at ${pct(F.full26.pStar)} in 100. ` +
      `Move the edge back to 29 September and ${F.sep29.cut} quiets are cut; the declaration's reading would carry all of them as over, and ${F.sep29.cutLaterBroke} of them broke in the month that followed. The worst edge for that reading is ${nice(toD(F.worst26.date))}: ${F.worst26.cutLaterBroke} of ${F.worst26.cut}. ` +
      `The lost curve does not stand still either. Over the ${F.pStarRange26.edges} edges in 2026 at which at least ten quiets had reached 42 days, its value at the last cut quiet runs from ${pct(F.pStarRange26.min[0])} in 100 (${nice(toD(F.pStarRange26.min[1]))}) to ${pct(F.pStarRange26.max[0])} (${nice(toD(F.pStarRange26.max[1]))}). The estimate is a reading of the edge as much as of the quiets. ` +
      `In Kivu, counting the 94 days without a report as an edge cuts every quiet watched across them on 7 March 2020: ${F.fullK.n - F.holeK.n} quiets fall below 42 days and leave, and the last cut quiet comes on day ${F.holeK.tStar} instead of ${F.fullK.tStar}, at ${pct(F.holeK.pStar)} in 100 instead of ${pct(F.fullK.pStar)}.`;
  }

  // ---- controls ----
  function setRange() {
    const [a, b] = span(); rng.min = 0; rng.max = Math.round((b - a) / DAY); rng.value = Math.round((edgeT - a) / DAY);
  }
  function pick(r) {
    rec = r; edgeT = span()[1];
    $("r26").setAttribute("aria-pressed", r === "bdbv"); $("rK").setAttribute("aria-pressed", r === "kivu");
    $("holeL").hidden = r !== "kivu"; setRange(); render();
  }
  $("r26").onclick = () => pick("bdbv"); $("rK").onclick = () => pick("kivu");
  $("hole").onchange = e => { hole = e.target.checked; render(); };
  rng.oninput = () => { edgeT = span()[0] + rng.value * DAY; render(); };
  const dragTo = ev => {
    const r = cal.getBoundingClientRect(), [a, b] = span(), pad = 8;
    const f = Math.max(0, Math.min(1, (ev.clientX - r.left - pad) / (r.width - 2 * pad)));
    edgeT = a + Math.round(f * (b - a) / DAY) * DAY; setRange(); render();
  };
  let dragging = false;
  cal.addEventListener("pointerdown", e => { dragging = true; cal.setPointerCapture(e.pointerId); dragTo(e); });
  cal.addEventListener("pointermove", e => { if (dragging) dragTo(e); });
  cal.addEventListener("pointerup", () => { dragging = false; });
  cur.addEventListener("pointermove", e => {
    if (!geom) return; const r = cur.getBoundingClientRect(), x = e.clientX - r.left;
    const t = Math.round(42 + (x - geom.L) / (geom.w - geom.L - geom.R) * (geom.maxT - 42));
    probeDay = t >= 42 && t <= geom.maxT ? t : null; render();
  });
  cur.addEventListener("pointerleave", () => { probeDay = null; render(); });
  window.addEventListener("resize", render);
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", render);
  window.__edgeSet = (r, d, h) => { pick(r); hole = !!h; $("hole").checked = hole; edgeT = toD(d); setRange(); render(); return window.__edgeState; };
  facts(); pick("bdbv");
})();
