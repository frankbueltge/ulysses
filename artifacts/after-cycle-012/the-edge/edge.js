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
  // off: where a quiet's day 1 falls. 0 = the day after the rise (corrected 2026-11-06, after the Studio's
  // check in CALL IT); 1 = the rise day itself, as this page counted until then.
  let off = 0;

  const Q = E.quiets.map(q => ({ ...q, f0: toD(q.f) }));
  function events(r, edge, h, o = off) {
    const out = [];
    for (const q of Q) {
      if (q.rec !== r) continue;
      let through = Math.round((edge - q.f0) / DAY) + o;
      if (h && q.f0 <= HOLE && q.f0 + q.L * DAY > HOLE) through = Math.min(through, Math.round((HOLE - q.f0) / DAY) + o);
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
      const y = top + (i + .5) * rh, s0 = q.f0 + (1 - off) * DAY, end = q.f0 + (q.L - off) * DAY;
      // with the hole as an edge, a quiet watched across it is cut on the last report day before it
      const cutT = (rec === "kivu" && hole && q.f0 <= HOLE && end + DAY > HOLE) ? Math.min(edgeT, HOLE) : edgeT;
      const caseT = q.f0 + (q.L + 1 - off) * DAY, seen = Math.min(end, cutT);
      g.lineWidth = lw; g.lineCap = "butt";
      if (end > cutT) { // what came after the edge
        g.strokeStyle = css("--nb"); g.globalAlpha = .45;
        g.beginPath(); g.moveTo(X(Math.max(s0, cutT)), y); g.lineTo(X(end), y); g.stroke();
        if (q.b) { g.fillStyle = css("--case"); g.beginPath(); g.arc(X(caseT), y, lw * .7 + 1, 0, 7); g.fill(); }
        g.globalAlpha = 1;
      }
      if (q.f0 > cutT) return;
      const reached = Math.round((cutT - q.f0) / DAY) + off >= 42 || (q.b && caseT <= cutT);
      g.strokeStyle = css("--w"); g.globalAlpha = reached ? 1 : .35;
      g.beginPath(); g.moveTo(X(s0), y); g.lineTo(X(seen), y); g.stroke(); g.globalAlpha = 1;
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
    // what the record later showed (fourth state): the same quiets read again at the record's own last day
    if (st.later) {
      const lk = st.later, lt = Math.max(...lk.ev.map(x => x.t));
      g.globalAlpha = .55; const lv = stepLine(lk.km.steps, lt, css("--a"), [1, 3], 5); g.globalAlpha = 1;
      lab("later", Y(lv) + (Math.abs(Y(lv) - Y(lc)) < 14 ? -14 : 0), css("--a"));
      // the gap between the edge's rules and the later reading, on the last cut quiet's day
      const x = X(k.tStar), yv = Y(stepAt(lk.km.steps, k.tStar));
      g.fillStyle = css("--a"); g.beginPath(); g.arc(x, yv, 4.5, 0, 7); g.fill();
    }
    const ll = stepLine(k.steps, k.tStar, css("--fg"), [], 2.4);
    g.fillStyle = css("--fg"); g.beginPath(); g.arc(X(k.tStar), Y(ll), 3.5, 0, 7); g.fill();
    if (probeDay != null && probeDay >= 42 && probeDay <= maxT) {
      g.strokeStyle = css("--you"); g.lineWidth = 1; g.setLineDash([2, 3]); g.beginPath(); g.moveTo(X(probeDay), T); g.lineTo(X(probeDay), Y(0)); g.stroke(); g.setLineDash([]);
    }
    st.curves = { carried, out, nb };
  }

  const pct = p => Math.round(p * 100);

  // ---- the rule's own day (second state): for T = 42..120, the chance a quiet that reached T breaks within W days ----
  const W = E.W, T0 = 42, T1 = 120, day = $("day");
  let probeT = null, dgeom = null;
  function ruleDay(r, edge, h, T, o = off) {
    const rows = [];
    for (const q of Q) {
      if (q.rec !== r || q.L < T) continue;
      let through = Math.round((edge - q.f0) / DAY) + o;
      if (h && q.f0 <= HOLE && q.f0 + q.L * DAY > HOLE) through = Math.min(through, Math.round((HOLE - q.f0) / DAY) + o);
      if (through < T) continue;
      rows.push(q.b && q.L + 1 <= through ? [q.L + 1, 1] : [Math.min(q.L, through), 0]);
    }
    if (!rows.length) return null;
    const n = rows.length, H = T + W;
    const inwin = rows.filter(([t, e]) => e && t <= H).length;
    const known = rows.filter(([t, e]) => (e && t <= H) || t >= H).length;
    let S = 1, m = n;
    for (const t of [...new Set(rows.map(x => x[0]))].sort((a, b) => a - b)) {
      if (t > H) break;
      const d = rows.filter(([u, e]) => u === t && e).length;
      if (d) S *= 1 - d / m;
      m -= rows.filter(([u]) => u === t).length;
    }
    const maxt = Math.max(...rows.map(x => x[0]));
    const undef = H > maxt && rows.some(([t, e]) => t === maxt && !e);
    return { n, known, carried: inwin / n, out: known ? inwin / known : null, lost: undef ? null : 1 - S };
  }
  function drawDay() {
    const h0 = rec === "kivu" && hole, rows = [];
    for (let T = T0; T <= T1; T++) rows.push([T, ruleDay(rec, edgeT, h0, T)]);
    const [g, w, h] = size(day), L = 34, R = 70, Tp = 26, B = 30;
    const X = T => L + (T - T0) / (T1 - T0) * (w - L - R), Y = p => Tp + (1 - p) * (h - Tp - B);
    dgeom = { L, R, w };
    g.clearRect(0, 0, w, h);
    g.strokeStyle = css("--line"); g.lineWidth = 1; g.fillStyle = css("--mute"); g.font = "11px system-ui,sans-serif";
    for (const p of [0, .25, .5, .75, 1]) { g.beginPath(); g.moveTo(L, Y(p)); g.lineTo(w - R, Y(p)); g.stroke(); g.textAlign = "right"; g.fillText(Math.round(p * 100), L - 5, Y(p) + 4); }
    g.textAlign = "left"; g.fillText(w < 560 ? `broke within ${W} days, in 100` : `broke within the next ${W} days, in 100 quiets that reached the rule's day`, L, 12);
    // one in ten
    g.setLineDash([2, 4]); g.strokeStyle = css("--mute"); g.beginPath(); g.moveTo(L, Y(.1)); g.lineTo(w - R, Y(.1)); g.stroke(); g.setLineDash([]);
    g.textAlign = "left"; g.fillText("1 in 10", w - R + 6, Y(.1) + 4);
    g.textAlign = "center";
    const step = w < 520 ? 20 : 10;
    for (let T = 50; T <= T1; T += step) g.fillText("day " + T, X(T), h - 10);
    // the two days of the literature
    const mark = (T, txt, col) => { g.strokeStyle = col; g.lineWidth = 1.5; g.beginPath(); g.moveTo(X(T), Tp); g.lineTo(X(T), Y(0)); g.stroke(); g.fillStyle = col; g.font = "600 11px system-ui,sans-serif"; g.textAlign = "left"; g.fillText(txt, X(T) + 4, Tp + 10); g.font = "11px system-ui,sans-serif"; };
    mark(42, "42 · WHO", css("--a")); mark(63, w < 560 ? "63" : "63 · another clock", css("--mute"));
    const line = (key, col, dash, wd) => {
      g.strokeStyle = col; g.lineWidth = wd; g.setLineDash(dash); g.beginPath(); let on = false, lastY = null;
      for (const [T, r] of rows) {
        const v = r && r[key]; if (v == null) { on = false; continue; }
        on ? g.lineTo(X(T), Y(v)) : g.moveTo(X(T), Y(v)); on = true; lastY = [T, v];
      }
      g.stroke(); g.setLineDash([]); return lastY;
    };
    const lc = line("carried", css("--held"), [], 2.2), lo = line("out", css("--case"), [6, 4], 2), ll = line("lost", css("--fg"), [], 2.4);
    // where lost becomes undefined: hatch from the first undefined day
    const firstU = rows.find(([, r]) => r && r.lost == null), lastR = rows.filter(([, r]) => r).pop();
    if (firstU && lastR) {
      const x0 = X(firstU[0]), x1 = X(lastR[0]);
      g.save(); g.beginPath(); g.rect(x0, Tp, x1 - x0, Y(0) - Tp); g.clip(); g.strokeStyle = css("--mute"); g.globalAlpha = .3;
      for (let x = x0 - 300; x < x1 + 300; x += 7) { g.beginPath(); g.moveTo(x, Y(0)); g.lineTo(x + 300, Y(0) - 300); g.stroke(); }
      g.restore();
      if (x1 - x0 > 80) { g.fillStyle = css("--mute"); g.font = "italic 13px Georgia,serif"; g.textAlign = "left"; g.fillText("lost: undefined", x0 + 6, Y(.62)); }
    }
    const lab = (txt, pt, col, dy) => { if (!pt) return; g.fillStyle = col; g.font = "600 12px system-ui,sans-serif"; g.textAlign = "left"; g.fillText(txt, X(pt[0]) + 6, Y(pt[1]) + 4 + dy); };
    if (lc && lastR && lc[0] === T1) lab("carried", lc, css("--held"), 0);
    if (probeT != null) { g.strokeStyle = css("--you"); g.lineWidth = 1; g.setLineDash([2, 3]); g.beginPath(); g.moveTo(X(probeT), Tp); g.lineTo(X(probeT), Y(0)); g.stroke(); g.setLineDash([]); }
    const at = T => (rows.find(x => x[0] === T) || [])[1];
    const r42 = at(42), rp = probeT != null ? at(probeT) : null;
    const f = v => v == null ? "undefined" : pct(v) + " in 100";
    const tell = (T, r) => r ? `Day <b>${T}</b>: <b>${r.n}</b> quiets had reached it, and the window of ${W} days after it is closed at the edge for <b>${r.known}</b>. Broke within it: carried <b>${f(r.carried)}</b> · lost <b>${f(r.lost)}</b> · left out <b>${r.out == null ? "nothing to say" : f(r.out)}</b>.` : `Day <b>${T}</b>: no quiet had reached it by this edge.`;
    $("dayRead").innerHTML = rp !== null && probeT != null ? tell(probeT, rp) : (r42 ? tell(42, r42) : "At this edge no quiet has yet reached 42 days.");
    let spread = 0; for (const [, r] of rows) if (r && r.out != null) spread = Math.max(spread, r.out - r.carried);
    const tenth = rows.find(([, r]) => r && r.lost != null && r.lost < .1);
    $("dayVerdict").innerHTML = !r42 ? "At this edge no quiet has reached 42 days, so no rule has anything to say." : (r42 && r42.out != null && r42.out - r42.carried < .05)
      ? `Here the three rules almost agree: the edge lies far beyond most of the windows. ${tenth ? `The lost curve falls below 1 in 10 from day <b>${tenth[0]}</b>.` : "Up to day 120 it never falls below 1 in 10."}`
      : `Here the rules part by up to <b>${pct(spread)}</b> points on the same day: the edge cuts the windows, and how long is long enough is decided by the rule for the cut, not by the quiets. ${tenth ? `The lost curve falls below 1 in 10 from day <b>${tenth[0]}</b>.` : "No rule-day up to 120 brings the lost curve below 1 in 10 before it becomes undefined."}`;
    window.__dayState = r42 ? { n: r42.n, known: r42.known, carried: Math.round(r42.carried * 1000) / 1000, out: r42.out == null ? null : Math.round(r42.out * 1000) / 1000, lost: r42.lost == null ? null : Math.round(r42.lost * 1000) / 1000, tenth: tenth ? tenth[0] : null } : null;
  }
  day.addEventListener("pointermove", e => {
    if (!dgeom) return; const r = day.getBoundingClientRect(), x = e.clientX - r.left;
    const T = Math.round(T0 + (x - dgeom.L) / (dgeom.w - dgeom.L - dgeom.R) * (T1 - T0));
    probeT = T >= T0 && T <= T1 ? T : null; drawDay();
  });
  day.addEventListener("pointerleave", () => { probeT = null; drawDay(); });
  function render() {
    const ev = events(rec, edgeT, rec === "kivu" && hole);
    drawCal(); drawDay();
    const read = $("read");
    if (!ev.length) {
      read.innerHTML = "At this edge no quiet has yet reached 42 days. There is nothing to read."; $("fence").textContent = ""; $("later").textContent = ""; window.__edgeState = null;
      const [g, w, h] = size(cur); g.clearRect(0, 0, w, h);
      $("sCarried").textContent = $("sLost").textContent = $("sOut").textContent = ""; return;
    }
    const realEnd0 = edgeT >= toD(E.records[rec][1]);
    let lat = null;
    if (!realEnd0) {
      const ids = new Set(ev.map(x => x.q)), ev2 = events(rec, toD(E.records[rec][1]), false).filter(x => ids.has(x.q));
      lat = { ev: ev2, km: km(ev2) };
    }
    const st = { ev, km: km(ev), later: lat }; drawCurve(st);
    const cut = ev.filter(x => !x.e), later = cut.filter(x => x.q.b).length, broke = ev.length - cut.length;
    const realEnd = edgeT >= toD(E.records[rec][1]);
    read.innerHTML = `Edge: <b>${nice(edgeT)}</b>. <b>${ev.length}</b> quiets had reached 42 days: <b>${broke}</b> broke before the edge, <b>${cut.length}</b> are cut by it. ` +
      (realEnd ? "This is the record's own last day: what the cut quiets become, nobody here can know."
        : `Of the ${cut.length} quiets this edge would carry as over, <b>${later}</b> broke later in the record.`);
    { const L2 = $("later");
      if (st.later) {
        const t = st.km.tStar, v = stepAt(st.later.km.steps, t), c = cut.length / ev.length, l = stepAt(st.km.steps, t);
        const d = { carried: Math.abs(c - v), lost: Math.abs(l - v), "left out": v }, best = Object.keys(d).reduce((a, b) => d[b] < d[a] ? b : a);
        L2.innerHTML = `<span class="sw"></span><b>What the record later showed.</b> The same ${ev.length} quiets, read again on the record's own last day, ${nice(toD(E.records[rec][1]))}: on day <b>${t}</b>, <b>${pct(v)} in 100</b> still quiet. At this edge carried said <b>${pct(c)}</b>, lost <b>${pct(l)}</b>, left out <b>0</b>. Nearest: <b>${best}</b>. The later reading is cut again by its own edge, so it is a second reading, not the truth.`;
      } else L2.innerHTML = `<span class="sw"></span>Move the edge back, and a fourth line shows what the record's later days wrote about the same quiets.`;
    }
    const k = st.km;
    { const ev2 = events(rec, edgeT, rec === "kivu" && hole, 1 - off), cut2 = ev2.filter(x => !x.e), k2 = ev2.length ? km(ev2) : null;
      const same = ev2.length === ev.length && cut2.length === cut.length && cut2.filter(x => x.q.b).length === later && k2 && k2.tStar === k.tStar;
      const who = off ? "With the correct count (from the day after the rise)," : "With the old count (from the rise day itself),";
      $("fence").innerHTML = `${who} the same edge reads ` + (ev2.length ? `<b>${ev2.length}</b> quiets past 42 days, <b>${cut2.length}</b> cut, <b>${cut2.filter(x => x.q.b).length}</b> of them broke later; last cut quiet on day <b>${k2.tStar}</b>. ` : "no quiet past 42 days. ") +
        (same ? "Here the one day changes nothing a curve shows." : "<b>Here the one day moves the reading.</b>"); }
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

  { const L = E.facts.later;
    $("laterFacts").innerHTML = `Move the edge back and the record's later days can be set beside the three rules. On 29 September, at the last cut quiet's day (${L.sep29.t}), carried said ${pct(L.sep29.carried)} in 100 still quiet, lost ${pct(L.sep29.lost)}, and the later record ${pct(L.sep29.later)}: carried read too much quiet. On 30 August, at day ${L.aug30.t}, lost said ${pct(L.aug30.lost)}, and the later record ${pct(L.aug30.later)}, as carried had: lost read too little. Over the ${L.near.carried + L.near.lost + L.near["left out"]} edges in 2026 a month or more back with at least ten quiets, the later reading lay nearest carried at ${L.near.carried} and nearest lost at ${L.near.lost}; left out was never nearest. No rule is the right one. Each is a wager on the edge, and the record that comes after settles it one edge at a time, under a rule of its own.`; }
  // ---- controls ----
  const first = {};
  for (const r of ["bdbv", "kivu"]) { const a = toD(E.records[r][0]); let d = 0; while (!events(r, a + d * DAY, false, 0).length) d++; first[r] = d; }
  function setRange() {
    const [a, b] = span(); rng.min = first[rec]; rng.max = Math.round((b - a) / DAY); rng.value = Math.round((edgeT - a) / DAY);
  }
  function pick(r) {
    rec = r; edgeT = span()[1];
    $("r26").setAttribute("aria-pressed", r === "bdbv"); $("rK").setAttribute("aria-pressed", r === "kivu");
    $("holeL").hidden = r !== "kivu"; setRange(); render();
  }
  $("r26").onclick = () => pick("bdbv"); $("rK").onclick = () => pick("kivu");
  $("hole").onchange = e => { hole = e.target.checked; render(); };
  $("day1").onchange = e => { off = e.target.checked ? 1 : 0; render(); };
  rng.oninput = () => { edgeT = span()[0] + rng.value * DAY; render(); };
  const dragTo = ev => {
    const r = cal.getBoundingClientRect(), [a, b] = span(), pad = 8;
    const f = Math.max(0, Math.min(1, (ev.clientX - r.left - pad) / (r.width - 2 * pad)));
    edgeT = a + Math.max(first[rec], Math.round(f * (b - a) / DAY)) * DAY; setRange(); render();
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
  window.__edgeSet = (r, d, h, o) => { pick(r); hole = !!h; $("hole").checked = hole; off = o ? 1 : 0; $("day1").checked = !!o; edgeT = toD(d); setRange(); render(); return { edge: window.__edgeState, day: window.__dayState }; };
  { const R = E.facts.ruleDay;
    $("dayFacts").innerHTML = `${pct(R.k42.lost)} in 100 quiets that reached 42 days broke within 90 days, ${pct(R.k63.lost)} in 100 of those that reached day 63, and the share falls below 1 in 10 only for quiets that reached day ${R.kTenth}. Counting the 94 days without a report as an edge raises the first figure to ${pct(R.h42.lost)} (lost) or ${pct(R.h42.out)} (left out).`; }
  facts(); pick("bdbv");
})();
