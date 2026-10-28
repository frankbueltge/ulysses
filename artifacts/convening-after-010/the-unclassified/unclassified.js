// The Unclassified — the IPC famine rule as an instrument, and the count it feeds.
// All material is in material.json; this file only encodes the rule's headline conditions.
(function () {
  const STATES = [
    ["above", "measured, at or above"],
    ["below", "measured, under"],
    ["inferred", "not measured, inferred"],
    ["none", "no data"],
  ];
  const state = { g: "fs", o: { food: "above", gam: "above", cdr: "inferred" }, r: "closed", p: "cur", e: "table", d: "written", why: "lack of data" };
  let M = null;

  const fmt = (n) => n.toLocaleString("en-GB");

  // The encoding. It reads only how many outcomes are in each state, as the headline rules do.
  function verdict() {
    const v = Object.values(state.o);
    const n = (s) => v.filter((x) => x === s).length;
    if (n("below") > 0)
      return ["No Famine classification", false,
        "An outcome was measured and did not reach its threshold. This is the only state in which the rule speaks against famine: a measurement, not an absence."];
    if (state.g === "fs") {
      if (n("above") === 3)
        return ["Famine, with solid evidence", false, "All three thresholds measured and reached: the indicative."];
      if (n("above") === 2 && n("inferred") === 1)
        return ["Famine, with reasonable evidence", false,
          "Two thresholds measured, the third assessed as likely from the broader evidence. The same phase as solid evidence; one clause of it is inferred."];
      return ["(nothing is written)", true,
        "The 2025 edition has no mood for this. Fewer than two outcomes are measured, or one has no evidence at all: the area is not classified as Famine, and the rule does not say it is not one."];
    }
    if (n("above") === 3)
      return ["Famine", false, "Reliable evidence on all three outcomes: the only state the 2021 manual calls Famine without qualification."];
    if (n("none") < 3)
      return ["Famine Likely", false,
        "In the 2021 manual, minimally adequate evidence that a famine may be occurring is enough for a classification in this mood, which asks for action and for more evidence at once. (Whether the evidence is “minimally adequate” is judged by analysts; this page assumes it is whenever anything is known.)"];
    return ["(nothing is written)", true, "Nothing is known: no edition of the rule writes anything here."];
  }

  function radio(container, attr, val) {
    container.querySelectorAll("button[data-" + attr + "]").forEach((b) =>
      b.setAttribute("aria-checked", String(b.dataset[attr] === val)));
  }

  function drawOutcomes() {
    const box = document.getElementById("outcomes");
    box.innerHTML = "";
    M.rule.outcomes.forEach((o) => {
      const d = document.createElement("div");
      d.className = "oc " + state.o[o.key];
      d.innerHTML = `<h3>${o.label}</h3><p class="th">${o.threshold}</p>`;
      const g = document.createElement("div");
      g.setAttribute("role", "radiogroup");
      g.setAttribute("aria-label", o.label);
      STATES.forEach(([s, label]) => {
        const b = document.createElement("button");
        b.className = s; b.textContent = label; b.setAttribute("role", "radio");
        b.setAttribute("aria-checked", String(state.o[o.key] === s));
        b.onclick = () => { state.o[o.key] = s; document.getElementById("casenote").textContent = ""; renderRule(); };
        g.appendChild(b);
      });
      d.appendChild(g);
      box.appendChild(d);
    });
  }

  function renderRule() {
    drawOutcomes();
    radio(document.querySelector("#h-rule").parentNode, "g", state.g);
    const [t, silent, why] = verdict();
    const el = document.getElementById("verdict");
    el.textContent = t; el.classList.toggle("silent", silent);
    document.getElementById("vwhy").textContent = why;
  }

  function loadCase(c) {
    if (c.states) state.o = Object.assign({}, c.states);
    renderRule();
    document.getElementById("casenote").innerHTML =
      `<b>${c.name}</b>, ${c.as_of}. Published: <b>${c.published}</b>. ${c.evidence} <i>${c.certain}</i> <a href="${c.source}">Source</a>.`;
  }

  function renderCount() {
    const C = M.count, svg = document.getElementById("count");
    radio(document.querySelector("#h-count").parentNode, "r", state.r);
    const max = C.phase5_projected_feb_may2026 + C.unclassified_people;
    const x0 = 250, W = 620, sx = (n) => (n / max) * W;
    const open = state.r === "open";
    const rows = [
      ["Phase 5, September 2025", C.phase5_current_sep2025, "counted"],
      ["Phase 5, projected Feb–May 2026", C.phase5_projected_feb_may2026, "counted"],
    ];
    let s = `<defs><pattern id="h" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="8" height="8" fill="none"/><line x1="0" y1="0" x2="0" y2="8" stroke="var(--hatch)" stroke-width="4"/></pattern></defs>`;
    rows.forEach(([lab, n], i) => {
      const y = 20 + i * 70;
      s += `<text x="0" y="${y + 24}" font-size="15">${lab}</text>`;
      s += `<rect x="${x0}" y="${y}" width="${sx(n)}" height="36" fill="var(--above)"/>`;
      s += `<text x="${x0 + sx(n) + 8}" y="${y + 24}" font-size="15">${fmt(n)}</text>`;
    });
    const y = 160, p = C.phase5_projected_feb_may2026;
    s += `<text x="0" y="${y + 24}" font-size="15">People in unclassified areas</text>`;
    if (open) {
      s += `<rect x="${x0}" y="${y}" width="${sx(C.unclassified_people)}" height="36" fill="url(#h)" stroke="var(--mute)" stroke-dasharray="4 3"/>`;
      s += `<text x="${x0 + 8}" y="${y + 24}" font-size="15">${fmt(C.unclassified_people)}: phase unknown</text>`;
      s += `<rect x="${x0}" y="${92}" width="${sx(p + C.unclassified_people)}" height="36" fill="none" stroke="var(--above)" stroke-dasharray="4 3"/>`;
      s += `<text x="${x0 + sx(p) + 8}" y="${92 + 24}" font-size="15" class="mute">${fmt(p)} to ${fmt(p + C.unclassified_people)}</text>`;
    } else {
      s += `<line x1="${x0}" y1="${y}" x2="${x0}" y2="${y + 36}" stroke="var(--ink)" stroke-width="2"/>`;
      s += `<text x="${x0 + 10}" y="${y + 24}" font-size="15">0 in any phase</text>`;
    }
    s += `<text x="0" y="240" font-size="12" class="mute">Bars to one scale. Source: IPC Special Snapshot, Sudan, issued November 2025.</text>`;
    svg.innerHTML = s;
    // the first projection's figure is drawn over by the second; remove the duplicated label when open
    if (open) svg.querySelectorAll("text").forEach((t) => { if (t.textContent === fmt(p)) t.remove(); });
    document.getElementById("countnote").textContent = open
      ? C.bound_note
      : `Added up, Phase 5 goes from ${fmt(C.phase5_current_sep2025)} counted in September to ${fmt(p)} projected. The ${fmt(C.unclassified_people)} people in ${C.unclassified_areas} are in this total as nobody.`;
  }


  // III. The six areas as the open table holds them, period by period.
  const PH = ["people", "1", "2", "3", "4", "5"];
  function renderEnc() {
    const E = M.encodings, p = state.p, rule = state.e === "rule" && p === "p2";
    radio(document.querySelector("#h-enc").parentNode, "p", p);
    radio(document.querySelector("#h-enc").parentNode, "e", state.e);
    let people = 0, p5 = 0;
    document.getElementById("encgrid").innerHTML = E.areas.map((a) => {
      let row = a.rows[p], kept = row[0];
      if (rule && !kept) kept = a.rows.p1[0];
      const cells = PH.map((lab, i) => {
        let v = row[i], cls = "c";
        if (rule) { v = i === 0 ? kept : null; cls += i === 0 ? (row[0] ? "" : " restored") : " unknown"; }
        else if (v === null) cls += " absent";
        else if (v === 0) cls += " zero";
        if (i === 5) cls += " p5";
        const txt = rule && i > 0 ? "?" : v === null ? "" : fmt(v);
        return `<div class="${cls}"><span class="cl">${i === 0 ? "people" : "Phase " + lab}</span><span class="cv">${txt}</span></div>`;
      }).join("");
      if (!rule) { people += row[0] || 0; p5 += row[5] || 0; } else people += kept;
      const gone = p === "p2";
      const quote = !gone ? "" : a.name === "Dilling" ? E.prose.Dilling : a.encoding === "A" ? E.prose.famine : "";
      const tag = gone ? `<span class="tag k${a.encoding}">${rule ? "phase unknown" : "written " + a.encoding}</span>` : "";
      const mood = gone && !rule ? `<p class="mood">${E.kinds[a.encoding].mood}</p>` : "";
      return `<article class="area${gone ? " gone k" + a.encoding : ""}${rule ? " ruled" : ""}"><h3>${a.name} ${tag}</h3><p class="l1">${a.level1} · in the table: “${a.table_name}”</p><div class="cells">${cells}</div>${mood}${quote ? `<p class="aq">“${quote}”</p>` : ""}</article>`;
    }).join("");
    const s = document.getElementById("encsum");
    if (p !== "p2") s.innerHTML = `Added up, the six hold <b>${fmt(people)}</b> people and <b>${fmt(p5)}</b> in Phase 5, ${fmt(p5)} of the national ${p === "cur" ? "375,389" : "Phase 5 count"}. The rows are complete: every phase has a number.`;
    else if (!rule) s.innerHTML = `Added up, the six now hold <b>0</b> in Phase 5 and <b>${fmt(people)}</b> people, all in the three localities written C. The three forms give the same zero. The national total keeps none of them: Sudan's analysed population falls from 47,490,883 to 46,649,479, by 841,404, the six areas' whole population.`;
    else s.innerHTML = `Read as the sentence means them: <b>${fmt(people)}</b> people (the table's own figure where it kept one, the last counted where it dropped it), and Phase 5 <b>unknown</b>, anywhere from 0 to all of them. That is the bound of section II, area by area. The rows the table could not write are the ones a reader needs most.`;
    document.getElementById("enckinds").innerHTML = p === "p2" && !rule
      ? Object.entries(E.kinds).map(([k, v]) => `<p><span class="tag k${k}">${k}</span> ${v.table}. ${v.mood}</p>`).join("") +
        `<p class="aq">The sentence gives one reason for all six: “${E.prose.all}”</p>`
      : "";
  }


  // III, added 2026-10-28 (the Field's correction): the reason the IPC gives against the form the table gives.
  function renderWhy() {
    const W = M.encodings.elsewhere, K = M.encodings.kinds, why = state.why;
    radio(document.getElementById("h-same").parentNode, "why", why);
    const hit = (c) => why === "all" || c.reason === why;
    document.getElementById("whygrid").innerHTML = ["A", "B", "C"].map((k) => {
      const chips = W.chips.filter((c) => c.encoding === k).map((c) =>
        `<span class="chip${hit(c) ? " on" : ""}${c.first_hand ? "" : " fld"}" title="${c.reason}"><b>${c.area}</b> <small>${c.analysis}${c.people ? " · " + fmt(c.people) + " kept" : ""} · ${c.reason}${c.first_hand ? "" : " †"}</small></span>`).join("");
      return `<div class="wcol k${k}"><p class="wh"><span class="tag k${k}">${k}</span> ${K[k].table}</p>${chips}</div>`;
    }).join("");
    const on = W.chips.filter(hit), forms = [...new Set(on.map((c) => c.encoding))].sort();
    const ana = [...new Set(on.map((c) => c.analysis))].length;
    document.getElementById("whysum").innerHTML = why === "all"
      ? `${W.chips.length} unclassified areas in ${[...new Set(W.chips.map((c) => c.analysis))].length} analyses. Two reasons are each written in more than one form, and the empty place (A) and the kept people (C) each hold more than one reason. Read across a row of the table and you cannot get back to the sentence.`
      : `<b>${why}</b>: ${on.length} area${on.length > 1 ? "s" : ""} in ${ana} analys${ana > 1 ? "es" : "is"}, written in <b>${forms.length}</b> of the three forms (${forms.join(", ")}).` +
        (forms.length > 1 ? " The reason does not decide the form." : " One case is not a rule.");
    const P = W.pair;
    document.getElementById("whypair").innerHTML = why === "lack of data" || why === "all"
      ? `<p class="lab">Two sentences, almost the same, and two forms</p>` + ["Dilling", "North Gaza"].map((n) =>
        `<blockquote class="pq k${P[n].encoding}"><p>“${P[n].text}${P[n].text2 ? "” … “" + P[n].text2 : ""}”</p><p class="aq">${P[n].src}. In the table: <span class="tag k${P[n].encoding}">${P[n].encoding}</span> ${K[P[n].encoding].table.toLowerCase()}.</p></blockquote>`).join("")
      : "";
    document.getElementById("whysrc").innerHTML = `Rows: ${W.table_check} Reasons: the IPC's texts, after the Field's reading (<a href="${W.field.url}">${W.field.cite}</a>). † passage not re-read here; the row was. Not shown: ${W.unread}`;
  }


  // IV. Three records, three depths: a remainder with a size, a zero, and no row at all (lane 3 corrected 2026-10-28).
  function renderDepths() {
    const D = M.depths, is = state.d === "is";
    radio(document.querySelector("#h-depth").parentNode, "d", state.d);
    const bn = (n) => "US$ " + (n / 1e9).toFixed(2) + " bn";
    const m = D.money, gap = m.required - m.funded, fp = (100 * m.funded / m.required).toFixed(1);
    const lane = (k, title, rec, bar, can, mood, src) =>
      `<article class="depth d${k}"><p class="dk">${["", "first", "second", "third"][k]} depth</p><h3>${title}</h3><p class="l1">${rec}</p>${bar}<p class="can"><b>What a reader can do with it:</b> ${can}</p><p class="mood">${mood}</p><p class="aq">${src}</p></article>`;
    const one = lane(1, "Money asked and not given", m.plan + ", FTS plan " + m.plan_id,
      `<div class="bar"><span class="got" style="width:${fp}%">${bn(m.funded)}</span><span class="gap" style="width:${100 - fp}%">${bn(gap)} not given</span></div>`,
      `subtract. Asked ${bn(m.required)}, given ${bn(m.funded)} (${fp} %). The missing part has a size, a unit and a date.`,
      is ? "The same as written: this record already holds its absence." : "Written in the indicative, with its size. The record of money cannot fail to write what it lacks, because what it lacks is defined by what was asked.",
      `Source: <a href="${m.source.url}">${m.source.cite}</a>.`);
    const c = D.count;
    const two = lane(2, "People the count could not classify", "IPC, Sudan, second projection (Feb–May 2026); six areas, section III",
      is ? `<div class="bar"><span class="unk" style="width:100%">${fmt(c.people)} people · phase unknown</span></div>`
         : `<div class="bar zerobar"><span class="z">0</span></div>`,
      is ? "nothing exact. The phase lies anywhere from none of them to all of them (the bound of section II)."
         : `add up, and get the wrong answer: the six areas sum to ${c.written} in every phase, and the national total falls by ${fmt(c.people)}.`,
      is ? "Restored from the sentence beside the table, not from the table." : "Written as a number, in the wrong mood: a zero reads as measured, and nothing was measured.",
      "Source: the IPC rows and passages of section III.");
    const mo = D.monitor, A = mo.archive, an = new Set(["alert", "key-message-update", "food-security-outlook", "food-security-outlook-update"]);
    const ini = { "alert": "A", "key-message-update": "K", "food-security-outlook": "O", "food-security-outlook-update": "U", "price-bulletin": "P" };
    // Sudan, July 2024 to December 2025: one row for analysis, one for price bulletins, as the archive lists them.
    const row = (label, pick, darkFrom, darkTo, open) => `<span class="rl">${label}</span>` + A.months.map((k, i) => {
      const got = A.sudan[k].filter(pick);
      if (got.length) return `<span class="mo got" title="${k}: ${got.join(", ")}">${got.map((t) => ini[t]).join("")}</span>`;
      const dark = k >= darkFrom && (open || k <= darkTo);
      if (!dark || !is) return `<span class="mo void" title="${k}: no entry"></span>`;
      return `<span class="mo lost${open && i === A.months.length - 1 ? " open" : ""}" title="${k}: dark">?</span>`;
    }).join("");
    const head = `<span class="rl"></span>` + A.months.map((k) => `<span class="mh${k.endsWith("-01") ? " yr" : ""}">${"JFMAMJJASOND"[+k.slice(5) - 1]}</span>`).join("");
    const grid = `<div class="months18${is ? " shown" : ""}">${head}${row("Analysis", (t) => an.has(t), "2025-01", "2025-08", false)}${row("Prices", (t) => t === "price-bulletin", "2024-11", null, true)}</div>` +
      `<p class="l1">Sudan, July 2024 to December 2025, as FEWS NET's own archive lists its pages. A alert, K key message, O outlook, U outlook update, P price bulletin.</p>` +
      (is ? `<ol class="edges">${A.edges.map((e) => `<li><b>${e.date}</b> <a href="${e.url}">${e.what}</a>: “${e.quote}”</li>`).join("")}</ol>` : "");
    const pb = A.lines_not_returned["price-bulletin"], rm = A.lines_not_returned["remote-monitoring-report"];
    const three = lane(3, "The monitor switched off", mo.name + ", the famine early warning system, read in its own archive",
      grid,
      is ? `date the dark by its edges, and only by them. Sudan's analysis stops after the Alert of 31 December 2024 and resumes with the Alert of 5 September 2025: eight dark months, which FEWS NET's release of 24 June 2025 calls “a brief pause”. The price bulletins have one edge only. ${pb.dated_2024} are dated January to October 2024 across all countries, and none since, for Sudan or anywhere; the remote monitoring reports, written for places without staff on the ground, end the same month (${rm.dated_2024} in 2024, none since).`
         : "nothing inside the dark. The archive has no entry for the months it was silent; it holds only the last page before them and the first after, and a reader has to know to look for the gap between.",
      is ? "Restored from the monitor's own record, but only at its edges. Where a series never came back there is one edge: a start with no end, which a record without a field for “ended” cannot tell from a delay. <span class=\"corr\"><b>Corrected 2026-10-28, nineteenth session:</b> it can, from the day the delay ends, where its entry dates are its first (below, <i>The hour you read it</i>).</span>"
         : "Not written at all. Of the three absences, only this one leaves nothing a program could find inside it.",
      `Source: <a href="${A.url}">FEWS NET's sitemap</a>, ${fmt(A.urls)} pages, read 2026-10-28, and the three pages above, read at first hand; after <a href="${A.field.url}">${A.field.cite}</a>. ${A.price_watch_note} ${A.limits}` +
      `<span class="corr"><b>Corrected 2026-10-28.</b> Until today this card placed six dark months, January to June 2025, from a news report (“${mo.source.quotes[0]}”), and said the archive's silence was inferred, not checked. The Field checked it: for Sudan the dark ran eight months, dated at both ends by FEWS NET itself. This practice re-read the archive and the pages the same day and agrees.</span>`);
    document.getElementById("depths").innerHTML = one + two + three;
    document.getElementById("depthsum").innerHTML = is
      ? "Read as the absences are, the three records hold one Sudan year: money missing, people unplaced, a monitor dark. Only the first is restored whole from its own record. The second needs the sentence beside the table. The third is restored from its own archive only at its edges, and the price bulletins have only one edge. <b>The deeper the cut, the less of it its own record can close.</b>"
      : "Read as written, the cut is visible only where it did least to the means of seeing: as money, with a size. Where it reached the count, it reads as zero; where it reached the monitor, it does not read at all.";
  }

  // IV, added 2026-10-28 (nineteenth session): the day you read the warehouse decides whether its dark is an end or a delay.
  function renderClock() {
    const C = M.clock, day = C.days[state.t];
    document.getElementById("clockday").textContent = day;
    const months = [];
    for (let y = 2024, mo = 1; y < 2026 || mo <= 9; mo++) { if (mo > 12) { y++; mo = 1; } months.push(y + "-" + String(mo).padStart(2, "0")); }
    const ended = (m) => { const [y, mo] = m.split("-").map(Number); return new Date(Date.UTC(y, mo, 0)).toISOString().slice(0, 10) <= day; };
    const head = `<span class="rl"></span>` + months.map((m) => `<span class="mh${m.endsWith("-01") ? " yr" : ""}">${m.endsWith("-01") ? m.slice(2, 4) : "JFMAMJJASOND"[+m.slice(5) - 1]}</span>`).join("");
    const stat = {};
    const row = (s) => {
      const S = C.data.series[s] || {}; let last = null, lastDay = null, back = 0;
      const cells = months.map((m) => {
        if (!ended(m)) return `<span class="cc"></span>`;
        const e = (S[m] || []).filter((x) => x[0] <= day), p = e.reduce((a, x) => a + x[1], 0), n = e.reduce((a, x) => a + x[2], 0);
        e.forEach((x) => { if (!lastDay || x[0] > lastDay) lastDay = x[0]; });
        if (p) { last = m; if (m >= "2024-10" && m <= "2026-01" && e.some((x) => x[0] >= "2026-02-01")) back++; }
        const cls = (p && n ? " mix" : p ? " in" : n ? " nc" : " wait") + (e.some((x) => x[0] === day) ? " now" : "");
        const sh = p && n ? Math.round(100 * p / (p + n)) : 0;
        const st = sh ? `background:linear-gradient(to top, var(--below) ${sh}%, transparent ${sh}%), repeating-linear-gradient(45deg, transparent 0 3px, var(--hatch) 3px 6px)` : p ? `opacity:${Math.max(.35, Math.min(1, p / 170)).toFixed(2)}` : "";
        const tip = `${s}, ${m}: ` + (e.length ? e.map((x) => `${x[1]} prices` + (x[2] ? ` and ${x[2]} “Not Collected”` : "") + ` entered ${x[0]}`).join("; ") : "nothing in the record yet");
        return `<span class="cc${cls}" style="${st}" title="${tip}"></span>`;
      }).join("");
      stat[s] = { last, lastDay, back };
      return `<span class="rl">${s}${s === "WFP" ? "<br><small>re-dated</small>" : ""}</span>` + cells;
    };
    const key = `<p class="clockkey"><i class="cc in"></i>prices entered (paler: fewer)<i class="cc nc"></i>marked “Not Collected” (the blue part: the share with a price)<i class="cc wait"></i>month over, nothing entered yet</p>`;
    document.getElementById("clockgrid").innerHTML = head + row("WFP") + row("FAMIS") + key;
    const mn = (m) => m ? new Date(m + "-15").toLocaleString("en-GB", { month: "long", year: "numeric" }) : "none";
    const w = stat.WFP, f = stat.FAMIS, any = [w.lastDay, f.lastDay].sort().pop();
    let txt;
    const nc = Object.values(C.data.series.FAMIS || {}).flat().filter((x) => x[0] <= day).reduce((a, x) => a + x[2], 0);
    const wfp = day < "2026-06-17"
      ? ` WFP's row is blank on this day even for January 2024: the warehouse now dates every WFP row 17 June 2026 or later, so it keeps no first hour for that stream.`
      : ` WFP's whole series, from January 2024 on, now carries the entry date 17 June 2026 (a share of it again 13 October 2026). Whether WFP's dark months were written late or on time, the record no longer says: it has re-dated its own hour.`;
    if (!f.back) {
      const gap = Math.round((Date.parse(day) - Date.parse(f.lastDay)) / 864e5);
      txt = `Read on ${day} by its own entry dates, the record's last FAMIS entry is ${f.lastDay}, ${gap} days ago, and its newest month is ${mn(f.last)}. No row says “ended”, none says “delayed”, and no month after it is marked at all. <b>On this day the record cannot tell an end from a delay: both would look exactly like this.</b>` + wfp;
    } else {
      txt = `Read on ${day}, FAMIS's dark is a delay. Its sixteen months, October 2024 to January 2026, were all entered on 3 February 2026: prices for ${f.back} of them, thinning from 76 to 18, and ${fmt(nc)} “Not Collected” marks, the record's own name for its silence. <b>The record could write that its silence was a delay only after the silence was over, and it named the silence only on the day it ended.</b>` +
        (f.last < "2026-02" && day >= "2026-04-01" ? ` And FAMIS has nothing after ${mn(f.last)}: for that stream the record stands on this day where it stood on 2 February 2026, with one edge and no way to say which.` : "") + wfp;
    }
    document.getElementById("clocksum").innerHTML = txt;
    document.getElementById("clocksrc").innerHTML = `Source: <a href="${C.data.url}">FEWS NET Data Warehouse, market price facts, Sudan</a>, fetched ${C.data.fetched}, ${fmt(C.data.rows)} rows, sha256 <code>${C.data.sha256.slice(0, 12)}…</code> (the same file the Field fetched), reduced by <a href="https://github.com/frankbueltge/ulysses/blob/main/artifacts/convening-after-010/the-unclassified/build_clock.py">build_clock.py</a> into <a href="price-clock.json">price-clock.json</a>. Only rows with a price or marked “Not Collected” are drawn; ${fmt(C.data.left_out["Not Available"])} “Not Available” rows (to September 2024) and ${fmt(C.data.left_out["No Data"])} “No Data” rows (no entry date) are left out. An entry date may mark a re-import rather than a first entry. For FAMIS it does not seem to: its rows for January to September 2024 carry dates ten to thirty days after their month. For WFP it does: its rows for January 2024 carry 17 June 2026, like its rows for 2025. The dark is “sixteen months” as the Field counts it, October 2024 to January 2026.`;
    document.querySelectorAll("#clockjump button").forEach((b) => b.setAttribute("aria-checked", b.dataset.t === day ? "true" : "false"));
  }

  function renderDoors() {
    const tb = document.querySelector("#doors tbody");
    tb.innerHTML = M.doors.map((d) =>
      `<tr><td><a href="${d.url}">${d.name}</a></td><td class="${d.status === 200 ? "open" : "closed"}">${d.status} — ${d.reading}</td><td>${d.reaches}</td></tr>`).join("");
  }

  function renderSources() {
    const ul = document.getElementById("sources");
    const items = M.rule.sources.map((s) =>
      `<li><a href="${s.url}">${s.cite}</a>${s.read_via ? ", read via " + s.read_via.split(" ")[0].replace(/^(.*)$/, '<a href="$1">a mirror</a>') + " (direct download refused)" : ""}. Quoted: ${s.quotes.map((q) => "“" + q + "”").join(" ")}</li>`);
    items.push(`<li><a href="${M.count.source.url}">${M.count.source.cite}</a>. Quoted: “${M.count.quote}”.</li>`);
    items.push(`<li><a href="${M.encodings.source.url}">${M.encodings.source.cite}</a>, sha256 <code>${M.encodings.source.sha256.slice(0, 12)}…</code>, fetched ${M.encodings.source.fetched}; the encodings A, B, C after <a href="${M.encodings.field.url}">${M.encodings.field.cite}</a>.</li>`);
    items.push(`<li><a href="${M.count.source.url}">${M.encodings.prose_source}</a>. Quoted in section III: “${M.encodings.prose.famine}” “${M.encodings.prose.Dilling}”</li>`);
    items.push(`<li><a href="${M.cases[0].source}">FEWS NET, Sudan Food Security Outlook, October 2025</a>, for El Fasher's malnutrition figure and inferred mortality.</li>`);
    items.push(`<li><a href="${M.depths.money.source.url}">${M.depths.money.source.cite}</a>, sha256 <code>${M.depths.money.source.sha256.slice(0, 12)}…</code>; section IV.</li>`);
    items.push(`<li><a href="${M.depths.monitor.source.url}">${M.depths.monitor.source.cite}</a>. Quoted: ${M.depths.monitor.source.quotes.map((q) => "“" + q + "”").join(" ")} (${M.depths.monitor.source.quote_note})</li>`);
    items.push(`<li><a href="${M.depths.monitor.archive.url}">FEWS NET, sitemap</a>, read 2026-10-28, sha256 of the sorted list <code>${M.depths.monitor.archive.sha256_of_sorted_url_list.slice(0, 12)}…</code>; ${M.depths.monitor.archive.edges.map((e) => `<a href="${e.url}">${e.what}</a>`).join("; ")}. Section IV, corrected the same day.</li>`);
    items.push(`<li><a href="${M.depths.voices[0].url}">${M.depths.voices[0].cite}</a>. Quoted: ${M.depths.voices[0].quotes.map((q) => "“" + q + "”").join(" ")}</li>`);
    ul.innerHTML = items.join("");
  }

  Promise.all([fetch("material.json").then((r) => r.json()), fetch("price-clock.json").then((r) => r.json())]).then(([m, pc]) => {
    M = m;
    const days = [];
    for (let t = Date.parse("2024-09-01"); t <= Date.parse(pc.fetched); t += 864e5) days.push(new Date(t).toISOString().slice(0, 10));
    M.clock = { data: pc, days };
    state.t = days.indexOf("2025-06-24");
    const ck = document.getElementById("clock");
    ck.max = days.length - 1; ck.value = state.t;
    ck.oninput = () => { state.t = +ck.value; renderClock(); };
    const jumps = [["2024-09-30", "the last entry before"], ["2025-06-24", "“a brief pause”"], ["2025-09-05", "the analysis returns"], ["2026-02-02", "the day before"], ["2026-02-03", "the first entry after"], ["2026-06-17", "WFP's months"], [pc.fetched, "today"]];
    const cj = document.getElementById("clockjump");
    jumps.forEach(([d, l]) => { const b = document.createElement("button"); b.setAttribute("role", "radio"); b.dataset.t = d; b.textContent = l; b.title = d; b.onclick = () => { state.t = days.indexOf(d); ck.value = state.t; renderClock(); }; cj.appendChild(b); });
    document.querySelectorAll("button[data-g]").forEach((b) => (b.onclick = () => { state.g = b.dataset.g; renderRule(); }));
    document.querySelectorAll("button[data-r]").forEach((b) => (b.onclick = () => { state.r = b.dataset.r; renderCount(); }));
    document.querySelectorAll("button[data-p]").forEach((b) => (b.onclick = () => { state.p = b.dataset.p; renderEnc(); }));
    document.querySelectorAll("button[data-e]").forEach((b) => (b.onclick = () => { state.e = b.dataset.e; if (state.e === "rule") state.p = "p2"; renderEnc(); }));
    document.querySelectorAll("button[data-why]").forEach((b) => (b.onclick = () => { state.why = b.dataset.why; renderWhy(); }));
    document.querySelectorAll("button[data-d]").forEach((b) => (b.onclick = () => { state.d = b.dataset.d; renderDepths(); }));
    const cb = document.getElementById("casebtns");
    M.cases.forEach((c) => {
      const b = document.createElement("button");
      b.textContent = c.name.split(",")[0];
      b.onclick = () => loadCase(c);
      cb.appendChild(b);
    });
    document.getElementById("countquote").textContent = "“" + M.count.quote + "” — the analysis itself.";
    renderRule(); renderCount(); renderEnc(); renderWhy(); renderDepths(); renderClock(); renderDoors(); renderSources();
    loadCase(M.cases[0]);
  });
})();
