// The Unclassified — the IPC famine rule as an instrument, and the count it feeds.
// All material is in material.json; this file only encodes the rule's headline conditions.
(function () {
  const STATES = [
    ["above", "measured, at or above"],
    ["below", "measured, under"],
    ["inferred", "not measured, inferred"],
    ["none", "no data"],
  ];
  const state = { g: "fs", o: { food: "above", gam: "above", cdr: "inferred" }, r: "closed" };
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
    items.push(`<li><a href="${M.cases[0].source}">FEWS NET, Sudan Food Security Outlook, October 2025</a>, for El Fasher's malnutrition figure and inferred mortality.</li>`);
    ul.innerHTML = items.join("");
  }

  fetch("material.json").then((r) => r.json()).then((m) => {
    M = m;
    document.querySelectorAll("button[data-g]").forEach((b) => (b.onclick = () => { state.g = b.dataset.g; renderRule(); }));
    document.querySelectorAll("button[data-r]").forEach((b) => (b.onclick = () => { state.r = b.dataset.r; renderCount(); }));
    const cb = document.getElementById("casebtns");
    M.cases.forEach((c) => {
      const b = document.createElement("button");
      b.textContent = c.name.split(",")[0];
      b.onclick = () => loadCase(c);
      cb.appendChild(b);
    });
    document.getElementById("countquote").textContent = "“" + M.count.quote + "” — the analysis itself.";
    renderRule(); renderCount(); renderDoors(); renderSources();
    loadCase(M.cases[0]);
  });
})();
