// Only a Return — the plane of writing days, and the ledger of fifteen warehouses.
(function () {
  "use strict";
  var D, C = null, srcOn = {}, showPrices = true, take = false, hits = [], E = 33;  // E: the month the query ends
  var cv = document.getElementById("plane"), ctx = cv.getContext("2d");
  var tip = document.getElementById("tip"), readout = document.getElementById("readout");
  var MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  var t0 = Date.UTC(2024, 0, 1);
  var fmtN = function (n) { return n.toLocaleString("en-GB"); };
  var mLabel = function (m) { return MONTHS[m % 12] + " " + (2024 + Math.floor(m / 12)); };
  var dLabel = function (d) { var x = new Date(t0 + d * 864e5); return x.getUTCDate() + " " + MONTHS[x.getUTCMonth()] + " " + x.getUTCFullYear(); };
  var TOP = (Date.UTC(2026, 10, 1) - t0) / 864e5;  // the day of the fetch: the top of the plane
  var css = function (v) { return getComputedStyle(document.documentElement).getPropertyValue(v).trim(); };

  function priceDay(c, s, w) {
    var pd = c.price_days[s]; if (!pd) return 0;
    for (var i = 0; i < pd.length; i++) if (pd[i][0] === w) return pd[i][1];
    return 0;
  }
  function nearPrice(c, s, w) {
    var pd = c.price_days[s]; if (!pd || !pd.length) return Infinity;
    var b = Infinity; pd.forEach(function (p) { b = Math.min(b, Math.abs(p[0] - w)); }); return b;
  }

  // In a query that ends with month E, a dated row exists if its month is in the window; a No Data
  // row exists only if its gap's far edge (the next written row of its series) is in the window too.
  function inWindow(g) { return g[1] === "nodata" ? (g[5] >= 0 && g[5] <= E) : g[2] <= E; }
  function stats(c, all) {
    var a = 0, same = 0, near1 = 0, nod = 0, pr = 0, lost = 0;
    c.groups.forEach(function (g) {
      if (!all && !inWindow(g)) { if (g[1] === "nodata" && g[2] <= E) lost += g[4]; return; }
      if (g[1] === "absence") { a += g[4]; var p = priceDay(c, g[0], g[3]); if (p) same += g[4]; else if (nearPrice(c, g[0], g[3]) <= 1) near1 += g[4]; }
      else if (g[1] === "nodata") nod += g[4]; else pr += g[4];
    });
    return { a: a, same: same, near1: near1, alone: a - same - near1, nod: nod, pr: pr, lost: lost };
  }

  function layout() {
    var w = cv.parentNode.clientWidth, h = Math.max(320, Math.min(560, w * 0.62));
    var r = window.devicePixelRatio || 1;
    cv.width = w * r; cv.height = h * r; cv.style.width = w + "px"; cv.style.height = h + "px";
    ctx.setTransform(r, 0, 0, r, 0, 0);
    return { w: w, h: h, l: w < 500 ? 44 : 64, r: 12, t: 30, b: 36 };
  }

  function draw() {
    if (!C) return;
    var L = layout(), W = L.w - L.l - L.r, H = L.h - L.t - L.b;
    var nd = TOP, M = 34;
    var X = function (m) { return L.l + (m + 0.5) / M * W; };
    var Y = function (d) { return L.t + H - d / nd * H; };
    var ink = css("--ink"), mute = css("--mute"), rule = css("--rule");
    ctx.clearRect(0, 0, L.w, L.h);
    ctx.font = "12px 'Noto Serif', Georgia, serif"; ctx.fillStyle = mute; ctx.strokeStyle = rule; ctx.lineWidth = 1;
    // year grid
    [0, 12, 24].forEach(function (m) {
      ctx.beginPath(); ctx.moveTo(L.l + m / M * W, L.t); ctx.lineTo(L.l + m / M * W, L.t + H); ctx.stroke();
      ctx.textAlign = "left"; ctx.fillText(String(2024 + m / 12), L.l + m / M * W + 3, L.t + H + 16);
    });
    [2024, 2025, 2026].forEach(function (y) {
      var d = (Date.UTC(y, 0, 1) - t0) / 864e5, yy = Y(d);
      ctx.beginPath(); ctx.moveTo(L.l, yy); ctx.lineTo(L.l + W, yy); ctx.stroke();
      ctx.textAlign = "right"; ctx.fillText(String(y), L.l - 6, yy + 4);
    });
    ctx.textAlign = "left"; ctx.fillText("month the row is for →", L.l + W - 150, L.t + H + 30);
    ctx.save(); ctx.translate(12, L.t + H / 2); ctx.rotate(-Math.PI / 2); ctx.textAlign = "center";
    ctx.fillText("day it was written →", 0, 0); ctx.restore();
    // diagonal: written in the month it is for (end of that month)
    ctx.strokeStyle = css("--diag"); ctx.setLineDash([4, 4]); ctx.beginPath();
    for (var m = 0; m < M; m++) { var dd = (Date.UTC(2024, m + 1, 0) - t0) / 864e5; if (m === 0) ctx.moveTo(X(m), Y(dd)); else ctx.lineTo(X(m), Y(dd)); }
    ctx.stroke(); ctx.setLineDash([]);
    // the end of the query: everything past it is outside the window
    if (E < M - 1) {
      var xe = L.l + (E + 1) / M * W;
      ctx.fillStyle = css("--outside"); ctx.fillRect(xe, L.t, L.l + W - xe, H);
      ctx.strokeStyle = css("--nodata"); ctx.beginPath(); ctx.moveTo(xe, L.t); ctx.lineTo(xe, L.t + H); ctx.stroke();
      ctx.fillStyle = css("--nodata"); ctx.textAlign = xe > L.l + W - 160 ? "right" : "left";
      ctx.fillText("the query ends: " + mLabel(E), xe + (ctx.textAlign === "right" ? -4 : 4), L.t - 10);
    }
    hits = [];
    var col = { price: css("--price"), absence: css("--absence"), nodata: css("--nodata") };
    var order = ["nodata", "price", "absence"];
    order.forEach(function (kind) {
      if (kind === "price" && !showPrices) return;
      C.groups.forEach(function (g) {
        if (g[1] !== kind || !srcOn[g[0]] || !inWindow(g)) return;
        var withP = kind === "absence" && priceDay(C, g[0], g[3]) > 0;
        if (take && kind === "absence" && (withP || nearPrice(C, g[0], g[3]) <= 1)) return;
        var x = X(g[2]), y = Y(g[3] + 0.5);
        var rad = kind === "price" ? Math.min(6, 1.2 + Math.sqrt(g[4]) * 0.35) : Math.min(11, 1.8 + Math.sqrt(g[4]) * 0.32);
        if (kind === "nodata") {
          // a thread to the far edge: the written row that lets this blank exist
          ctx.strokeStyle = col.nodata; ctx.globalAlpha = 0.35; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(X(g[5]), y); ctx.stroke(); ctx.globalAlpha = 1;
          ctx.lineWidth = 1.2; ctx.beginPath(); ctx.arc(x, y, rad, 0, 7); ctx.stroke();
        }
        else { ctx.globalAlpha = kind === "price" ? 0.55 : 0.85; ctx.fillStyle = col[kind]; ctx.beginPath(); ctx.arc(x, y, rad, 0, 7); ctx.fill(); ctx.globalAlpha = 1; }
        if (take && kind === "absence") { ctx.strokeStyle = ink; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.arc(x, y, rad + 4, 0, 7); ctx.stroke(); }
        hits.push({ x: x, y: y, r: Math.max(rad, 5), g: g });
      });
    });
    say();
  }

  function say() {
    var s = stats(C);
    if (!C.groups.length) { readout.textContent = C.name + ": the warehouse holds only aggregated rows for this period, derived from other series, so there is nothing to lay out."; return; }
    var t = C.name + ": " + fmtN(s.a) + " absences carry a day. " + fmtN(s.same) + " of them were written on a day when the same source also wrote prices";
    if (s.near1) t += ", and " + fmtN(s.near1) + " one day from such a day";
    t += ". " + fmtN(s.nod) + " rows say No Data and carry no day; each is drawn at the day the next row of its series was written.";
    if (s.lost) t += " Because the query ends in " + mLabel(E) + ", " + fmtN(s.lost) + " No Data rows for months inside it do not exist: their series writes again only later.";
    if (take) t += s.alone ? " With the absences written beside prices taken away, " + fmtN(s.alone) + " are left, circled: these were written apart." : " With the absences written beside prices taken away, none is left. Every absence here was written by someone who came back with prices.";
    readout.textContent = t;
  }

  function hover(ev) {
    var b = cv.getBoundingClientRect(), mx = ev.clientX - b.left, my = ev.clientY - b.top, best = null, bd = 1e9;
    hits.forEach(function (h) { var d = Math.hypot(h.x - mx, h.y - my); if (d < h.r + 4 && d < bd) { bd = d; best = h; } });
    if (!best) { tip.hidden = true; return; }
    var g = best.g, src = C.sources[g[0]], t;
    if (g[1] === "nodata") t = "<b>" + fmtN(g[4]) + " × No Data</b> for " + mLabel(g[2]) + "<br>" + src + "<br>no id, no submission, no day<br>it exists once the series writes again: " + mLabel(g[5]) + ", written " + dLabel(g[3]);
    else {
      var p = priceDay(C, g[0], g[3]);
      t = "<b>" + fmtN(g[4]) + " × " + (g[1] === "price" ? "price" : "absence") + "</b> for " + mLabel(g[2]) + "<br>written " + dLabel(g[3]) + "<br>" + src;
      if (g[1] === "absence") t += "<br>" + (p ? "that day this source also wrote " + fmtN(p) + " prices" : "that day this source wrote no price (nearest: " + (isFinite(nearPrice(C, g[0], g[3])) ? nearPrice(C, g[0], g[3]) + " days" : "never") + ")");
    }
    tip.innerHTML = t; tip.hidden = false;
    var tx = Math.min(best.x + 12, b.width - 240); tip.style.left = Math.max(0, tx) + "px"; tip.style.top = Math.max(0, best.y - 10) + "px";
  }

  function pick(cc) {
    C = D.countries.filter(function (c) { return c.cc === cc; })[0]; srcOn = {};
    C.sources.forEach(function (s, i) { srcOn[i] = true; });
    document.querySelectorAll("#countries button").forEach(function (b) { b.setAttribute("aria-checked", b.dataset.cc === cc ? "true" : "false"); });
    var sb = document.getElementById("sources"); sb.innerHTML = "";
    if (C.sources.length > 1) C.sources.forEach(function (s, i) {
      var b = document.createElement("button"); b.setAttribute("role", "switch"); b.setAttribute("aria-checked", "true"); b.textContent = s;
      b.onclick = function () { srcOn[i] = !srcOn[i]; b.setAttribute("aria-checked", srcOn[i] ? "true" : "false"); draw(); };
      sb.appendChild(b);
    });
    document.querySelectorAll(".lrow").forEach(function (r) { r.classList.toggle("on", r.dataset.cc === cc); });
    draw();
  }

  function ledger() {
    var el = document.getElementById("ledger"), max = 1;
    var rows = D.countries.map(function (c) { var s = stats(c, true); max = Math.max(max, s.a, s.nod); return { c: c, s: s }; });
    rows.sort(function (a, b) { return b.s.a - a.s.a; });
    el.innerHTML = '<div class="lhead"><span>country</span><span>absences with a day</span><span>count · written on a day of prices · apart</span><span>No Data</span></div>';
    rows.forEach(function (r) {
      var d = document.createElement("button"); d.className = "lrow"; d.dataset.cc = r.c.cc;
      var share = r.s.a ? (100 * r.s.same / r.s.a) : null;
      var shTxt = share === null ? "" : (Math.floor(share * 10) / 10).toFixed(1) + " %";
      d.innerHTML = '<span class="ln">' + r.c.name + '</span><span class="lb"><i class="ba" style="width:' + (100 * r.s.a / max) + '%"><i class="bs" style="width:' + (r.s.a ? 100 * r.s.same / r.s.a : 0) + '%"></i></i></span><span class="lt">' + (r.s.a ? fmtN(r.s.a) + " · " + shTxt + (r.s.alone ? " · " + r.s.alone + " apart" : "") : (r.c.groups.length ? "none" : "aggregated rows only")) + '</span><span class="lt nd">' + fmtN(r.s.nod) + '</span>';
      d.onclick = function () { pick(r.c.cc); document.getElementById("h-plane").scrollIntoView({ behavior: "smooth" }); };
      el.appendChild(d);
    });
    var T = D.totals;
    document.getElementById("totals").textContent = "All fifteen: " + fmtN(T.absence) + " absences with a day, " + fmtN(T.absence_same_day_as_price) + " written on a day of prices (" + (100 * T.absence_same_day_as_price / T.absence).toFixed(1) + " %), " + fmtN(T.absence_within_1_day_of_price) + " one day from one, " + fmtN(T.absence - T.absence_same_day_as_price - T.absence_within_1_day_of_price) + " apart; " + fmtN(T.nodata) + " rows of No Data, none with a day and every one between two written rows of its own series; " + fmtN(T.price) + " prices.";
    var put = function (k, v) { document.querySelectorAll('[data-t="' + k + '"]').forEach(function (e) { e.textContent = v; }); };
    put("sameShare", (100 * T.absence_same_day_as_price / T.absence).toFixed(1) + " % (" + fmtN(T.absence_same_day_as_price) + " of " + fmtN(T.absence) + ")");
    put("subShare", (100 * T.absence_in_submission_with_price / T.absence).toFixed(1) + " %");
    var apart = T.absence - T.absence_same_day_as_price - T.absence_within_1_day_of_price;
    put("aloneShare", fmtN(apart) + " of " + fmtN(T.absence) + ", or " + (100 * apart / T.absence).toFixed(2) + " %");
  }

  fetch("data.json").then(function (r) { return r.json(); }).then(function (d) {
    D = d;
    var cb = document.getElementById("countries");
    D.countries.forEach(function (c) {
      var b = document.createElement("button"); b.setAttribute("role", "radio"); b.dataset.cc = c.cc; b.textContent = c.name;
      b.onclick = function () { pick(c.cc); }; cb.appendChild(b);
    });
    ledger(); pick("SD");
    document.getElementById("t-prices").onclick = function () { showPrices = !showPrices; this.setAttribute("aria-checked", showPrices); this.textContent = showPrices ? "prices shown" : "prices hidden"; draw(); };
    document.getElementById("t-take").onclick = function () { take = !take; this.setAttribute("aria-checked", take); draw(); };
    cv.addEventListener("mousemove", hover); cv.addEventListener("mouseleave", function () { tip.hidden = true; });
    cv.addEventListener("click", hover);
    window.addEventListener("resize", draw);
    var sl = document.getElementById("t-end"), so = document.getElementById("t-end-out");
    var setE = function () { E = +sl.value; so.textContent = mLabel(E); draw(); };
    sl.addEventListener("input", setE); setE();
  }).catch(function (e) { readout.textContent = "The data file did not load: " + e; });
})();
