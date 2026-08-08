// Conference deck for: "Peak Age of Information over Scheduled, Energy-Constrained
// Multi-Segment Delay-Tolerant Networks with Bundle Replication"
// All chart data is real simulation output from sim/results/*.csv.
const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10 x 5.625 in
pres.title = "PAoI over Scheduled, Energy-Constrained Multi-Segment DTNs";
pres.author = " ";

// ---------- palette (space / orbital, energy accent) ----------
const NAVY = "10182B";     // deep-space background (dark slides)
const NAVY2 = "1B2A4A";    // ink on light slides
const INK = "22304F";
const MUT = "5B6B8C";      // muted caption
const ICE = "C9D8F0";      // ice blue on dark
const WHT = "FFFFFF";
const TEAL = "0E7C7B";     // terrestrial segment
const ORNG = "E8630A";     // UAV segment
const VIOL = "6A4C93";     // LEO segment
const AMBR = "F4A100";     // energy accent
const CARD = "F4F6FB";     // light card fill
const CARD2 = "EDF1F9";
const GRID = "E2E8F0";

const HDR = "Cambria";
const BODY = "Calibri";

const mkShadow = () => ({ type: "outer", color: "000000", blur: 7, offset: 2, angle: 45, opacity: 0.14 });

// ---------- helpers ----------
function titleBar(slide, kicker, title, opts = {}) {
  const tc = opts.dark ? WHT : NAVY2;
  const kc = opts.dark ? ICE : MUT;
  slide.addText(kicker.toUpperCase(), {
    x: 0.55, y: 0.28, w: 8.9, h: 0.3, fontFace: BODY, fontSize: 11.5, bold: true,
    color: opts.kickerColor || kc, charSpacing: 3, margin: 0,
  });
  slide.addText(title, {
    x: 0.55, y: 0.57, w: 8.9, h: 0.55, fontFace: HDR, fontSize: 24, bold: true,
    color: tc, margin: 0, valign: "top",
  });
}

// small chain motif (sensor->UAV->LEO->gateway) used as recurring footer motif
function chainMotif(slide, x, y, scale = 1, dark = false) {
  const cols = [TEAL, ORNG, VIOL];
  const dotR = 0.075 * scale;
  const gap = 0.52 * scale;
  const lineCol = dark ? "3A4A6E" : "C7D2E8";
  slide.addShape(pres.shapes.LINE, { x: x + dotR, y: y + dotR, w: gap * 3, h: 0, line: { color: lineCol, width: 1.4 } });
  for (let i = 0; i < 4; i++) {
    const c = i === 0 ? (dark ? ICE : MUT) : i === 3 ? (dark ? ICE : MUT) : cols[i - 1];
    slide.addShape(pres.shapes.OVAL, { x: x + i * gap, y: y, w: dotR * 2, h: dotR * 2, fill: { color: i === 1 || i === 2 ? cols[i - 1] : c }, line: { type: "none" } });
  }
}

function footer(slide, n, dark = false) {
  chainMotif(slide, 0.55, 5.32, 0.75, dark);
  slide.addText("PAoI over scheduled, energy-constrained multi-segment DTNs", {
    x: 2.35, y: 5.26, w: 6.0, h: 0.26, fontFace: BODY, fontSize: 8.5,
    color: dark ? "6E7FA3" : "9AA7C2", margin: 0, valign: "middle",
  });
  slide.addText(String(n), {
    x: 9.35, y: 5.26, w: 0.35, h: 0.26, fontFace: BODY, fontSize: 9,
    color: dark ? "6E7FA3" : "9AA7C2", align: "right", margin: 0, valign: "middle",
  });
}

function card(slide, x, y, w, h, fill = CARD) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x, y, w, h, fill: { color: fill }, line: { type: "none" }, rectRadius: 0.06, shadow: mkShadow(),
  });
}

function statCallout(slide, x, y, w, big, label, color = NAVY2, bigSize = 30) {
  slide.addText(big, { x, y, w, h: 0.52, fontFace: HDR, fontSize: bigSize, bold: true, color, align: "center", margin: 0 });
  slide.addText(label, { x, y: y + 0.5, w, h: 0.55, fontFace: BODY, fontSize: 10.5, color: MUT, align: "center", margin: 0 });
}

const chartBase = {
  chartArea: { fill: { color: "FFFFFF" } },
  plotArea: { fill: { color: "FFFFFF" } },
  catAxisLabelColor: MUT, valAxisLabelColor: MUT,
  catAxisLabelFontSize: 9, valAxisLabelFontSize: 9,
  valGridLine: { color: GRID, size: 0.5 },
  catGridLine: { style: "none" },
  legendFontSize: 9.5,
};

// =====================================================================
// SLIDE 1 — TITLE (dark)
// =====================================================================
{
  const s = pres.addSlide();
  s.background = { color: NAVY };

  // orbital art: planet arc bottom-left + orbit ellipses + satellites
  s.addShape(pres.shapes.OVAL, { x: -2.4, y: 3.7, w: 6.6, h: 6.6, fill: { color: "16213C" }, line: { type: "none" } });
  s.addShape(pres.shapes.OVAL, { x: -2.15, y: 3.95, w: 6.1, h: 6.1, fill: { color: "1A2748" }, line: { type: "none" } });
  // orbit rings (thin ellipse outlines)
  s.addShape(pres.shapes.OVAL, { x: -3.3, y: 2.9, w: 8.6, h: 8.6, fill: { type: "none" }, line: { color: "2E3F66", width: 1 } });
  s.addShape(pres.shapes.OVAL, { x: -4.2, y: 2.15, w: 10.6, h: 10.6, fill: { type: "none" }, line: { color: "273758", width: 1 } });
  // satellites on the rings
  s.addShape(pres.shapes.OVAL, { x: 4.62, y: 4.02, w: 0.14, h: 0.14, fill: { color: VIOL }, line: { type: "none" } });
  s.addShape(pres.shapes.OVAL, { x: 8.35, y: 4.85, w: 0.1, h: 0.1, fill: { color: ORNG }, line: { type: "none" } });
  // scattered stars
  [[7.9, 0.7], [9.0, 1.6], [8.45, 3.1], [6.9, 1.05], [9.45, 0.55], [7.3, 2.3], [9.3, 4.6], [6.3, 0.5]].forEach(([sx, sy]) => {
    s.addShape(pres.shapes.OVAL, { x: sx, y: sy, w: 0.035, h: 0.035, fill: { color: "51648F" }, line: { type: "none" } });
  });

  s.addText("IEEE OJCOMS • SPECIAL ISSUE: DELAY-TOLERANT NETWORKING FOR 6G", {
    x: 0.7, y: 0.72, w: 8.6, h: 0.3, fontFace: BODY, fontSize: 11, bold: true, color: AMBR, charSpacing: 2.5, margin: 0,
  });
  s.addText("Peak Age of Information over Scheduled,\nEnergy-Constrained Multi-Segment DTNs\nwith Bundle Replication", {
    x: 0.7, y: 1.12, w: 8.9, h: 1.95, fontFace: HDR, fontSize: 31, bold: true, color: WHT, margin: 0, lineSpacingMultiple: 1.04,
  });
  s.addText("When is a bundle copy worth its energy? A freshness theory for LEO + UAV + terrestrial contact plans.", {
    x: 0.7, y: 3.18, w: 7.6, h: 0.65, fontFace: BODY, fontSize: 15, italic: true, color: ICE, margin: 0,
  });

  // author placeholder + venue line
  s.addText([
    { text: "Author name • Affiliation", options: { breakLine: true } },
    { text: "Manuscript for IEEE OJCOMS — submission Aug 2026", options: { color: "8FA1C6", fontSize: 11 } },
  ], { x: 0.7, y: 4.35, w: 6.4, h: 0.65, fontFace: BODY, fontSize: 13, color: ICE, margin: 0 });

  s.addNotes("Talk in one line: freshness (peak age of information) over DTN contact plans, where links are scheduled and intermittent, and every extra bundle copy costs harvested energy. We derive when a copy is worth its energy. Validated in Monte-Carlo and in a real Bundle Protocol / CGR simulator.");
}

// =====================================================================
// SLIDE 2 — SETTING
// =====================================================================
{
  const s = pres.addSlide();
  s.background = { color: WHT };
  titleBar(s, "The setting", "Scheduled, intermittent connectivity is the 6G frontier");

  // chain diagram
  const y0 = 1.78;
  const nodes = [
    { label: "Ground\nsensor", sub: "source", c: "8593B0", x: 0.75 },
    { label: "UAV\nmule", sub: "semi-periodic patrol", c: ORNG, x: 3.15 },
    { label: "LEO\nrelay", sub: "periodic passes", c: VIOL, x: 5.55 },
    { label: "Ground\ngateway", sub: "monitor", c: "8593B0", x: 7.95 },
  ];
  // arrows
  for (let i = 0; i < 3; i++) {
    const segc = [TEAL, ORNG, VIOL][i];
    s.addShape(pres.shapes.LINE, {
      x: nodes[i].x + 1.32, y: y0 + 0.44, w: 1.08, h: 0,
      line: { color: segc, width: 2.6, endArrowType: "triangle" },
    });
  }
  nodes.forEach((n) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: n.x, y: y0, w: 1.32, h: 0.88, fill: { color: CARD }, line: { color: n.c, width: 1.75 }, rectRadius: 0.09, shadow: mkShadow(),
    });
    s.addText(n.label, { x: n.x, y: y0 + 0.07, w: 1.32, h: 0.56, fontFace: BODY, fontSize: 12.5, bold: true, color: INK, align: "center", margin: 0, lineSpacingMultiple: 0.92 });
    s.addText(n.sub, { x: n.x - 0.25, y: y0 + 0.95, w: 1.82, h: 0.25, fontFace: BODY, fontSize: 9.5, color: MUT, align: "center", margin: 0 });
  });
  // segment tags above arrows
  const tags = [
    { t: "terrestrial: renewal ON/OFF", c: TEAL, x: 1.55 },
    { t: "UAV: jittered period", c: ORNG, x: 3.98 },
    { t: "LEO: deterministic P, W", c: VIOL, x: 6.35 },
  ];
  tags.forEach((t) => s.addText(t.t, { x: t.x, y: y0 - 0.38, w: 1.95, h: 0.3, fontFace: BODY, fontSize: 9.5, bold: true, color: t.c, align: "center", margin: 0 }));

  // three fact cards
  const facts = [
    { h: "Links are scheduled, not lossy", b: "A ground station sees a LEO satellite for a window W once per period P. Between passes the link is OFF by schedule — bundles age in a buffer, not in a queue.", c: VIOL },
    { h: "Freshness is the metric", b: "Telemetry, disaster response, IoT monitoring care about Age of Information and its peak (PAoI) — not throughput or delivery ratio.", c: TEAL },
    { h: "Copies cost energy", b: "DTN replication hedges uncertain contacts, but on harvesting relays every copy drains the battery that future contacts need.", c: AMBR },
  ];
  facts.forEach((f, i) => {
    const x = 0.55 + i * 3.05;
    card(s, x, 3.1, 2.85, 1.85);
    s.addShape(pres.shapes.OVAL, { x: x + 0.22, y: 3.32, w: 0.16, h: 0.16, fill: { color: f.c }, line: { type: "none" } });
    s.addText(f.h, { x: x + 0.5, y: 3.22, w: 2.2, h: 0.4, fontFace: BODY, fontSize: 12.5, bold: true, color: NAVY2, margin: 0 });
    s.addText(f.b, { x: x + 0.22, y: 3.72, w: 2.45, h: 1.1, fontFace: BODY, fontSize: 10.5, color: INK, margin: 0, lineSpacingMultiple: 1.04 });
  });

  footer(s, 2);
  s.addNotes("Set the scene: 6G integrates non-terrestrial segments. The canonical chain: ground sensor to UAV mule to LEO relay to gateway. Three points: connectivity is scheduled (bundle ages in buffer until next pass, a residual-wait law, not queueing); the metric is freshness; and replication couples to energy on harvesting platforms.");
}

// =====================================================================
// SLIDE 3 — THE GAP
// =====================================================================
{
  const s = pres.addSlide();
  s.background = { color: WHT };
  titleBar(s, "Positioning", "Three literatures that don’t meet");

  const cards = [
    { h: "AoI over erasure links", who: "Chiariotti et al., HARQ / satellite AoI", b: "Always-on server, random packet erasure. No scheduled OFF periods — no residual-wait law.", c: VIOL },
    { h: "Tandem-queue AoI", who: "Sinha et al., Senthilkumar et al.", b: "Persistent or memorylessly failing servers. A contact plan is deterministic-periodic — a different law.", c: TEAL },
    { h: "Contact-plan routing", who: "CGR / RUCoP / CGR-UCoP", b: "Optimizes delivery ratio under uncertain contacts. No freshness objective, no energy budget.", c: ORNG },
  ];
  cards.forEach((cd, i) => {
    const x = 0.55 + i * 3.05;
    card(s, x, 1.45, 2.85, 1.72);
    s.addText(cd.h, { x: x + 0.22, y: 1.62, w: 2.45, h: 0.32, fontFace: BODY, fontSize: 13, bold: true, color: cd.c, margin: 0 });
    s.addText(cd.who, { x: x + 0.22, y: 1.94, w: 2.45, h: 0.3, fontFace: BODY, fontSize: 9.5, italic: true, color: MUT, margin: 0 });
    s.addText(cd.b, { x: x + 0.22, y: 2.26, w: 2.45, h: 0.85, fontFace: BODY, fontSize: 10.5, color: INK, margin: 0, lineSpacingMultiple: 1.03 });
  });

  // gap statement band
  card(s, 0.55, 3.42, 8.95, 0.78, NAVY);
  s.addText([
    { text: "The gap:  ", options: { bold: true, color: AMBR } },
    { text: "no prior work couples ", options: { color: WHT } },
    { text: "scheduled store–carry–forward gating", options: { bold: true, color: ICE } },
    { text: " + ", options: { color: WHT } },
    { text: "multi-copy replication", options: { bold: true, color: ICE } },
    { text: " + ", options: { color: WHT } },
    { text: "an energy constraint", options: { bold: true, color: ICE } },
    { text: " with a freshness objective.", options: { color: WHT } },
  ], { x: 0.85, y: 3.42, w: 8.4, h: 0.78, fontFace: BODY, fontSize: 13.5, valign: "middle", margin: 0 });

  s.addText([
    { text: "Closest late-breaking work — Badia et al. (Globecom-W ’25): copy diversity lowers AoI under ", options: {} },
    { text: "random", options: { italic: true } },
    { text: " intermittency, energy-agnostic. We cover the complementary regime: deterministic contact plans, finite-battery copy-degree control, CGR realization.", options: {} },
  ], { x: 0.55, y: 4.38, w: 8.95, h: 0.62, fontFace: BODY, fontSize: 11, color: MUT, margin: 0, lineSpacingMultiple: 1.05 });

  footer(s, 3);
  s.addNotes("Reviewers here are DTN insiders (CGR lineage). Position early: erasure-channel AoI assumes always-on servers; tandem-queue AoI assumes persistent or memoryless-failing service; the space-DTN community optimizes delivery ratio, not freshness, and never models energy. We extend RUCoP/CGR rather than compete. Mention Badia Globecom-W 2025 as closest recent work: random availability, no energy; ours is deterministic scheduling + energy-coupled copy degree.");
}

// =====================================================================
// SLIDE 4 — MODEL & METRIC
// =====================================================================
{
  const s = pres.addSlide();
  s.background = { color: WHT };
  titleBar(s, "System model", "Duty-cycled segments, buffered aging, an energy gate");

  // duty cycle strip drawing (left)
  const dx = 0.55, dy = 1.6, dw = 4.6;
  card(s, dx, dy - 0.15, dw, 1.7);
  // baseline
  s.addShape(pres.shapes.LINE, { x: dx + 0.3, y: dy + 0.72, w: dw - 0.6, h: 0, line: { color: "AAB6CE", width: 1.2 } });
  // ON windows
  [[0.3, 0.55], [2.15, 0.55], [4.0, 0.0]].forEach(([ox, ow]) => {
    if (ow > 0) s.addShape(pres.shapes.RECTANGLE, { x: dx + ox, y: dy + 0.4, w: ow, h: 0.32, fill: { color: VIOL }, line: { type: "none" } });
  });
  s.addText("ON", { x: dx + 0.3, y: dy + 0.4, w: 0.55, h: 0.32, fontFace: BODY, fontSize: 8.5, bold: true, color: WHT, align: "center", valign: "middle", margin: 0 });
  s.addText("OFF", { x: dx + 0.9, y: dy + 0.42, w: 0.6, h: 0.3, fontFace: BODY, fontSize: 8.5, color: MUT, align: "center", valign: "middle", margin: 0 });
  // dimension arrows
  s.addShape(pres.shapes.LINE, { x: dx + 0.3, y: dy + 1.02, w: 0.55, h: 0, line: { color: NAVY2, width: 1.2, beginArrowType: "triangle", endArrowType: "triangle" } });
  s.addText("W", { x: dx + 0.3, y: dy + 1.06, w: 0.55, h: 0.22, fontFace: BODY, fontSize: 9.5, bold: true, color: NAVY2, align: "center", margin: 0 });
  s.addShape(pres.shapes.LINE, { x: dx + 0.87, y: dy + 1.02, w: 1.26, h: 0, line: { color: MUT, width: 1.2, beginArrowType: "triangle", endArrowType: "triangle" } });
  s.addText("G = P − W", { x: dx + 0.82, y: dy + 1.06, w: 1.35, h: 0.22, fontFace: BODY, fontSize: 9.5, color: MUT, align: "center", margin: 0 });
  s.addShape(pres.shapes.LINE, { x: dx + 0.3, y: dy + 0.12, w: 1.85, h: 0, line: { color: VIOL, width: 1.2, beginArrowType: "triangle", endArrowType: "triangle" } });
  s.addText("period P   (duty cycle δ = W/P)", { x: dx + 0.32, y: dy - 0.14, w: 3.4, h: 0.24, fontFace: BODY, fontSize: 9.5, bold: true, color: VIOL, margin: 0 });
  // arrival marker
  s.addShape(pres.shapes.LINE, { x: dx + 1.82, y: dy + 0.38, w: 0, h: 0.36, line: { color: AMBR, width: 2.2 } });
  s.addText("arrival at phase U → residual wait R (ages in buffer)", { x: dx + 1.05, y: dy + 1.32, w: 3.4, h: 0.24, fontFace: BODY, fontSize: 9.5, color: AMBR, bold: true, margin: 0 });

  // quantities (right column)
  const qx = 5.5;
  const rows = [
    ["Rₛ", "residual wait until next window at segment s"],
    ["Dₛ = Rₛ + Tₛ", "per-segment increment (wait + service/propagation)"],
    ["Y = Σₛ Dₛ", "end-to-end latency;  k copies → Yₘᵢₙ = minₖ Y⁽ᵏ⁾"],
    ["PAoI = E[Z] + E[Yₘᵢₙ]", "per-outage peak age (worst staleness per silent gap)"],
  ];
  rows.forEach((r, i) => {
    const yy = 1.42 + i * 0.53;
    s.addText(r[0], { x: qx, y: yy, w: 1.95, h: 0.3, fontFace: HDR, fontSize: 12.5, bold: true, color: NAVY2, margin: 0 });
    s.addText(r[1], { x: qx, y: yy + 0.27, w: 4.0, h: 0.26, fontFace: BODY, fontSize: 9.5, color: MUT, margin: 0 });
  });

  // energy gate band
  card(s, 0.55, 3.68, 8.95, 1.24, CARD2);
  s.addShape(pres.shapes.OVAL, { x: 0.85, y: 3.98, w: 0.62, h: 0.62, fill: { color: AMBR }, line: { type: "none" } });
  s.addText("⚡", { x: 0.85, y: 3.98, w: 0.62, h: 0.62, fontSize: 22, align: "center", valign: "middle", margin: 0, color: WHT });
  s.addText([
    { text: "Energy gate.  ", options: { bold: true, color: NAVY2 } },
    { text: "Each relay has battery bₛ, harvest rate λₑ, per-copy cost e.  A contact is usable only if the battery covers the copy:  ", options: { color: INK } },
    { text: "Iₛᵉᶠᶠ = Iₛ · 𝟙{bₛ ≥ e}", options: { bold: true, color: NAVY2 } },
    { text: ".  Scarcity thins contacts; replication drains the battery faster — the tension this paper resolves.", options: { color: INK } },
  ], { x: 1.7, y: 3.78, w: 7.55, h: 1.05, fontFace: BODY, fontSize: 11.5, margin: 0, valign: "middle", lineSpacingMultiple: 1.06 });

  footer(s, 4);
  s.addNotes("The model: each segment is a server that is ON only during scheduled windows. A bundle generated mid-gap waits a residual R before service T. Latencies add along the chain; replication takes the min over k copies. We report per-outage PAoI = E[Z] + E[Ymin] (worst-case staleness per silent gap; conservative vs textbook per-reset PAoI). Energy gates contacts: usable only when the battery covers a copy.");
}

// =====================================================================
// SLIDE 5 — RESULT 1
// =====================================================================
{
  const s = pres.addSlide();
  s.background = { color: WHT };
  titleBar(s, "Result 1", "The LEO residual-wait anchor — closed form");

  // formulas card (left)
  card(s, 0.55, 1.45, 4.5, 2.5);
  const fx = 0.85;
  s.addText("A stationary arrival meets the schedule at uniform phase:", { x: fx, y: 1.62, w: 4.0, h: 0.3, fontFace: BODY, fontSize: 10.5, color: MUT, margin: 0 });
  s.addText("P(R = 0) = δ        fᵣ(r) = 1/P  on  (0, G]", { x: fx, y: 1.95, w: 4.0, h: 0.32, fontFace: HDR, fontSize: 13.5, bold: true, color: NAVY2, margin: 0 });
  s.addText("E[R] = (P−W)² / 2P = (P/2)(1−δ)²", { x: fx, y: 2.42, w: 4.0, h: 0.32, fontFace: HDR, fontSize: 14, bold: true, color: VIOL, margin: 0 });
  s.addText("mean AoI  =  Tₛ + (P/2)(1−δ)²", { x: fx, y: 2.88, w: 4.0, h: 0.3, fontFace: HDR, fontSize: 13.5, bold: true, color: NAVY2, margin: 0 });
  s.addText("peak AoI  =  Tₛ + P(1−δ)", { x: fx, y: 3.24, w: 4.0, h: 0.3, fontFace: HDR, fontSize: 13.5, bold: true, color: NAVY2, margin: 0 });
  s.addText("Validated: KS distance 0.002; log–log slopes 1.98 / 1.00.", { x: fx, y: 3.6, w: 4.0, h: 0.28, fontFace: BODY, fontSize: 9.5, italic: true, color: MUT, margin: 0 });

  // chart: mean quadratic vs peak linear (computed from the closed forms; even δ grid)
  const deltas = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8];
  const mean = deltas.map((d) => 0.5 * (1 - d) ** 2);
  const peak = deltas.map((d) => (1 - d));
  s.addChart(pres.charts.LINE, [
    { name: "mean AoI − Tₛ  (quadratic)", labels: deltas.map(String), values: mean },
    { name: "peak AoI − Tₛ  (linear)", labels: deltas.map(String), values: peak },
  ], {
    ...chartBase, x: 5.25, y: 1.4, w: 4.25, h: 2.6,
    chartColors: [VIOL, AMBR], lineSize: 2.5, lineDataSymbol: "none",
    showLegend: true, legendPos: "t",
    catAxisTitle: "duty cycle δ", showCatAxisTitle: true, catAxisTitleFontSize: 10, catAxisTitleColor: MUT,
    valAxisTitle: "age / P", showValAxisTitle: true, valAxisTitleFontSize: 10, valAxisTitleColor: MUT,
  });

  // insight band
  card(s, 0.55, 4.25, 8.95, 0.72, CARD2);
  s.addText([
    { text: "Design consequence:  ", options: { bold: true, color: NAVY2 } },
    { text: "sparse contacts hurt the mean quadratically but the peak only linearly — mean-optimal and peak-optimal contact provisioning ", options: { color: INK } },
    { text: "differ", options: { bold: true, italic: true, color: VIOL } },
    { text: ".", options: { color: INK } },
  ], { x: 0.85, y: 4.25, w: 8.4, h: 0.72, fontFace: BODY, fontSize: 12.5, valign: "middle", margin: 0 });

  footer(s, 5);
  s.addNotes("Result 1 is the anchor everything else builds on. Uniform arrival phase gives a mixed residual law: atom at zero (arrive in-window) plus uniform slab over the gap. Mean age is quadratic in (1-delta), peak is linear - so provisioning for mean vs peak freshness leads to different constellations. Validated to KS 0.002; fitted slopes 1.98 and 1.00.");
}

// =====================================================================
// SLIDE 6 — RENEWAL GENERALIZATION + INVERSION (real data e12)
// =====================================================================
{
  const s = pres.addSlide();
  s.background = { color: WHT };
  titleBar(s, "One model, three segment types", "Renewal generalization & the AoI/PAoI inversion");

  // left: unified law
  card(s, 0.55, 1.45, 4.15, 2.05);
  s.addText([
    { text: "Alternating renewal: ON duration U, OFF gap V;", options: { breakLine: true } },
    { text: "cycle C = U + V", options: {} },
  ], { x: 0.85, y: 1.6, w: 3.6, h: 0.5, fontFace: BODY, fontSize: 10.5, color: MUT, margin: 0 });
  s.addText("E[R] = E[V²] / 2E[C]", { x: 0.85, y: 2.14, w: 3.6, h: 0.34, fontFace: HDR, fontSize: 16, bold: true, color: TEAL, margin: 0 });
  s.addText("E[PAoI] = Tₛ + E[V]", { x: 0.85, y: 2.56, w: 3.6, h: 0.34, fontFace: HDR, fontSize: 16, bold: true, color: NAVY2, margin: 0 });
  s.addText("LEO = deterministic V • UAV = low-jitter V • CTMC = exponential V • terrestrial = high-variance V", { x: 0.85, y: 3.0, w: 3.6, h: 0.45, fontFace: BODY, fontSize: 9.5, color: MUT, margin: 0 });

  // inversion condition card
  card(s, 0.55, 3.68, 4.15, 1.28, CARD2);
  s.addText([
    { text: "Exact inversion condition\n", options: { bold: true, color: NAVY2, fontSize: 11.5 } },
    { text: "CV²(V)  >  1 + 2E[U]/E[V]", options: { bold: true, color: ORNG, fontSize: 15, fontFace: HDR } },
  ], { x: 0.85, y: 3.8, w: 3.6, h: 0.7, fontFace: BODY, margin: 0, lineSpacingMultiple: 1.1 });
  s.addText("→ peak age falls below average age (≈ CV 1.11 here)", { x: 0.85, y: 4.52, w: 3.6, h: 0.3, fontFace: BODY, fontSize: 9.5, color: MUT, margin: 0 });

  // right: real e12 data chart
  const cv = ["0.0", "0.3", "0.5", "1.0", "1.5", "2.0"];
  s.addChart(pres.charts.LINE, [
    { name: "mean AoI", labels: cv, values: [0.410, 0.446, 0.511, 0.815, 1.322, 2.030] },
    { name: "mean PAoI", labels: cv, values: [0.905, 0.905, 0.904, 0.904, 0.904, 0.903] },
  ], {
    ...chartBase, x: 4.95, y: 1.45, w: 4.55, h: 3.15,
    chartColors: [TEAL, NAVY2], lineSize: 2.75,
    lineDataSymbol: "circle", lineDataSymbolSize: 5,
    showLegend: true, legendPos: "t",
    catAxisTitle: "CV of contact gap V", showCatAxisTitle: true, catAxisTitleFontSize: 10, catAxisTitleColor: MUT,
    valAxisTitle: "age (units of E[C])", showValAxisTitle: true, valAxisTitleFontSize: 10, valAxisTitleColor: MUT,
  });
  s.addText("simulation, 12 seeds — PAoI is variance-blind; AoI is not. They cross at the predicted threshold.", {
    x: 4.95, y: 4.62, w: 4.55, h: 0.35, fontFace: BODY, fontSize: 9.5, italic: true, color: MUT, align: "center", margin: 0,
  });

  footer(s, 6);
  s.addNotes("One alternating-renewal model covers all three segment types; LEO is the deterministic special case, the unreliable-server CTMC literature is the exponential point on our CV axis. Key structural finding: mean PAoI depends only on E[V], mean AoI grows with gap variance - so above an exact CV threshold, peak age sits BELOW average age. A single freshness number misleads across heterogeneous segments. Chart is real simulation data (E12).");
}

// =====================================================================
// SLIDE 7 — RESULT 2
// =====================================================================
{
  const s = pres.addSlide();
  s.background = { color: WHT };
  titleBar(s, "Result 2", "Phase mixing composes latencies — and prices a copy");

  // lemma card
  card(s, 0.55, 1.45, 4.35, 1.62);
  s.addText("Phase-mixing lemma (Weyl)", { x: 0.85, y: 1.6, w: 3.8, h: 0.3, fontFace: BODY, fontSize: 12.5, bold: true, color: NAVY2, margin: 0 });
  s.addText("If segment periods are incommensurate (or upstream dispersion exceeds Pₛ), arrival phases become uniform & independent ⇒ increments Dₛ are independent and end-to-end latency is their convolution.", {
    x: 0.85, y: 1.92, w: 3.8, h: 1.05, fontFace: BODY, fontSize: 10.5, color: INK, margin: 0, lineSpacingMultiple: 1.05,
  });

  // failure mode card
  card(s, 0.55, 3.3, 4.35, 1.55, CARD2);
  s.addText([
    { text: "Failure mode:  ", options: { bold: true, color: ORNG } },
    { text: "a UAV synchronized to one specific LEO pass locks the phases — the correction term revives. Confirmed in dtnsim: end-to-end variance additivity holds under incommensurate periods and collapses under commensurate (locked) ones.", options: { color: INK } },
  ], { x: 0.85, y: 3.42, w: 3.8, h: 1.3, fontFace: BODY, fontSize: 10.5, margin: 0, lineSpacingMultiple: 1.06 });

  // two-copy theorem (right)
  card(s, 5.15, 1.45, 4.35, 1.62);
  s.addText("Two-copy PAoI theorem", { x: 5.45, y: 1.6, w: 3.8, h: 0.3, fontFace: BODY, fontSize: 12.5, bold: true, color: NAVY2, margin: 0 });
  s.addText("E[Yₘᵢₙ] = E[Y] − ½ E|Y⁽¹⁾ − Y⁽²⁾|", { x: 5.45, y: 1.98, w: 3.8, h: 0.36, fontFace: HDR, fontSize: 16, bold: true, color: TEAL, margin: 0 });
  s.addText("The freshness bought by a second copy = half the mean absolute dispersion of path latencies (a Gini-type index).", {
    x: 5.45, y: 2.44, w: 3.8, h: 0.6, fontFace: BODY, fontSize: 10.5, color: INK, margin: 0, lineSpacingMultiple: 1.05,
  });

  // stat callouts
  card(s, 5.15, 3.3, 4.35, 1.55);
  statCallout(s, 5.3, 3.5, 2.0, "⅔(1−δ)", "two-copy residual ratio\nE[Rₘᵢₙ]/E[R] — a 33% cut\nat sparse contacts", TEAL, 26);
  statCallout(s, 7.35, 3.5, 2.0, "0", "gain for same-bottleneck\ncopies — replication pays only\non independent contacts", ORNG, 26);

  footer(s, 7);
  s.addNotes("Composition needs care: a bundle's arrival phase at segment s is displaced by upstream delays. The phase-mixing lemma (Weyl equidistribution) gives the exact condition for independence: incommensurate periods or large upstream dispersion. Then the two-copy theorem: the value of a second copy equals half the Gini dispersion of path latency - replication pays in proportion to latency spread, and pays zero on same-bottleneck copies. Failure mode validated in the real CGR stack.");
}

// =====================================================================
// SLIDE 8 — RESULT 3: THRESHOLD (real data e7)
// =====================================================================
{
  const s = pres.addSlide();
  s.background = { color: WHT };
  titleBar(s, "Result 3", "The energy–replication threshold");

  // objective (left)
  card(s, 0.55, 1.45, 4.15, 1.95);
  s.addText("Mean-PAoI objective in copies k :", { x: 0.85, y: 1.6, w: 3.6, h: 0.3, fontFace: BODY, fontSize: 10.5, color: MUT, margin: 0 });
  s.addText([
    { text: "A(k) = ", options: { color: NAVY2 } },
    { text: "P(1−pₑ)/pₑ", options: { color: AMBR } },
    { text: " + ", options: { color: NAVY2 } },
    { text: "P(1−δ)ᵏ⁺¹/(k+1)", options: { color: VIOL } },
  ], { x: 0.85, y: 1.94, w: 3.6, h: 0.4, fontFace: HDR, fontSize: 14.5, bold: true, margin: 0 });
  s.addText([
    { text: "starvation", options: { color: AMBR, bold: true } },
    { text: " (energy-forced skips)  vs  ", options: { color: MUT } },
    { text: "order-statistic gain", options: { color: VIOL, bold: true } },
  ], { x: 0.85, y: 2.38, w: 3.6, h: 0.28, fontFace: BODY, fontSize: 10, margin: 0 });
  s.addText("η = λₑP/e   (copies harvested per contact period)", { x: 0.85, y: 2.72, w: 3.6, h: 0.28, fontFace: BODY, fontSize: 10.5, color: INK, margin: 0 });
  s.addText("Unimodal ⇒ optimum brackets η", { x: 0.85, y: 3.02, w: 3.6, h: 0.3, fontFace: BODY, fontSize: 10.5, italic: true, color: MUT, margin: 0 });

  // boxed k* (left, below)
  card(s, 0.55, 3.62, 4.15, 1.32, NAVY);
  s.addText("k* = min( Kₘₐₓ , ⌊η⌋ or ⌈η⌉ )", { x: 0.85, y: 3.78, w: 3.6, h: 0.44, fontFace: HDR, fontSize: 18, bold: true, color: WHT, margin: 0 });
  s.addText("⌊η⌋ = conservative no-starvation rule; take ⌈η⌉ only when the extra copy repays its skips. Monotone in η, saturates at Kₘₐₓ.", {
    x: 0.85, y: 4.24, w: 3.6, h: 0.62, fontFace: BODY, fontSize: 9.5, color: ICE, margin: 0, lineSpacingMultiple: 1.02,
  });

  // right: unimodal curves (real e7 data)
  const ks = ["1", "2", "3", "4", "5", "6", "7", "8", "9"];
  s.addChart(pres.charts.LINE, [
    { name: "η = 3", labels: ks, values: [1.410, 1.248, 1.178, 1.456, 1.759, 2.073, 2.392, 2.719, 3.051] },
    { name: "η = 5", labels: ks, values: [1.410, 1.248, 1.169, 1.123, 1.102, 1.273, 1.458, 1.648, 1.849] },
  ], {
    ...chartBase, x: 4.95, y: 1.45, w: 4.55, h: 3.1,
    chartColors: [ORNG, TEAL], lineSize: 2.75, lineDataSymbol: "circle", lineDataSymbolSize: 6,
    showLegend: true, legendPos: "t",
    catAxisTitle: "replication degree k", showCatAxisTitle: true, catAxisTitleFontSize: 10, catAxisTitleColor: MUT,
    valAxisTitle: "mean PAoI / P", showValAxisTitle: true, valAxisTitleFontSize: 10, valAxisTitleColor: MUT,
    valAxisMinVal: 1.0,
  });
  s.addText("simulated PAoI is unimodal with minimum at k = η — over-replication starves future windows.", {
    x: 4.95, y: 4.58, w: 4.55, h: 0.35, fontFace: BODY, fontSize: 9.5, italic: true, color: MUT, align: "center", margin: 0,
  });

  footer(s, 8);
  s.addNotes("The core result. Objective: starvation term (energy-forced skipped windows) plus order-statistic gain. Unimodal in k, minimizer is one of the two integers bracketing eta = copies harvested per period. Floor = conservative no-starvation DTN rule; ceiling wins only when a skipped window is worth the extra copy - that distinction is itself a contribution. Chart is real Tier-1 data: minimum sits exactly at k = eta.");
}

// =====================================================================
// SLIDE 9 — STAIRCASE + CEILING (real data e8 + E14)
// =====================================================================
{
  const s = pres.addSlide();
  s.background = { color: WHT };
  titleBar(s, "Result 3 — validation", "The staircase, and the ceiling branch caught in the act");

  // left: staircase chart (closed form on an even η grid + simulated points, e8)
  s.addChart(pres.charts.LINE, [
    { name: "closed form min(Kₘₐₓ, ⌊η⌋)", labels: ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"], values: [1, 2, 3, 4, 5, 6, 7, 8, 8, 8] },
    { name: "simulated k*", labels: ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"], values: [1, 2, 3, 4, null, 6, null, 8, null, 8] },
  ], {
    ...chartBase, x: 0.45, y: 1.5, w: 4.45, h: 3.0,
    chartColors: ["AAB6CE", NAVY2], lineSize: 2.0,
    lineDataSymbol: "circle", lineDataSymbolSize: 7,
    showLegend: true, legendPos: "t",
    catAxisTitle: "energy adequacy η", showCatAxisTitle: true, catAxisTitleFontSize: 10, catAxisTitleColor: MUT,
    valAxisTitle: "optimal degree k*", showValAxisTitle: true, valAxisTitleFontSize: 10, valAxisTitleColor: MUT,
  });
  s.addText("k*(η) non-decreasing, saturates at Kₘₐₓ = 8 (Theorem 3)", {
    x: 0.45, y: 4.52, w: 4.45, h: 0.3, fontFace: BODY, fontSize: 9.5, italic: true, color: MUT, align: "center", margin: 0,
  });

  // right: ceiling experiment card
  card(s, 5.15, 1.5, 4.35, 3.0);
  s.addText("The ceiling branch (E14)", { x: 5.45, y: 1.66, w: 3.8, h: 0.32, fontFace: BODY, fontSize: 13, bold: true, color: NAVY2, margin: 0 });
  s.addText("Fine η-sweep across [3, 4], δ = 0.1, 16 seeds:", { x: 5.45, y: 2.0, w: 3.8, h: 0.28, fontFace: BODY, fontSize: 10.5, color: MUT, margin: 0 });
  // mini table
  const tbl = [
    [{ text: "η", options: { bold: true, color: WHT, fill: { color: NAVY2 }, align: "center" } },
     { text: "3.1 – 3.8", options: { bold: true, color: WHT, fill: { color: NAVY2 }, align: "center" } },
     { text: "3.9", options: { bold: true, color: WHT, fill: { color: NAVY2 }, align: "center" } }],
    [{ text: "simulated optimum", options: { align: "left" } },
     { text: "k = 3 = ⌊η⌋", options: { align: "center", bold: true, color: TEAL } },
     { text: "k = 4 = ⌈η⌉", options: { align: "center", bold: true, color: ORNG } }],
    [{ text: "analytic branch", options: { align: "left" } },
     { text: "floor", options: { align: "center", color: MUT } },
     { text: "ceiling", options: { align: "center", color: MUT } }],
  ];
  s.addTable(tbl, {
    x: 5.45, y: 2.34, w: 3.75, rowH: 0.34, fontFace: BODY, fontSize: 10,
    color: INK, border: { pt: 0.75, color: "D5DDEC" }, valign: "middle",
    colW: [1.45, 1.35, 0.95],
  });
  s.addText([
    { text: "Flip lands exactly at the analytic crossover  ", options: { color: INK } },
    { text: "η★ = 3.824", options: { bold: true, color: ORNG, fontFace: HDR, fontSize: 13 } },
    { text: "  — 9/9 points match. Occasional energy-forced skips are worth the extra copy near the top of the interval.", options: { color: INK } },
  ], { x: 5.45, y: 3.6, w: 3.8, h: 0.8, fontFace: BODY, fontSize: 10.5, margin: 0, lineSpacingMultiple: 1.05 });

  footer(s, 9);
  s.addNotes("Two validations of the threshold. Left: k* tracks eta one-for-one then saturates at Kmax - the staircase, real Tier-1 data. Right: E14 pins the subtle branch - between integers, the simulated optimum stays at floor(eta) through 3.8 and flips to ceiling at 3.9, bracketing the analytic crossover 3.824. 9/9 match. The floor-vs-ceiling distinction survived adversarial review.");
}

// =====================================================================
// SLIDE 10 — BATTERY HARDENING (e11 data)
// =====================================================================
{
  const s = pres.addSlide();
  s.background = { color: WHT };
  titleBar(s, "Hardening", "An exact battery-queue throttle, not a fluid guess");

  // work-conservation card
  card(s, 0.55, 1.45, 4.15, 1.9);
  s.addText("Work conservation (distribution-free)", { x: 0.85, y: 1.6, w: 3.6, h: 0.32, fontFace: BODY, fontSize: 12.5, bold: true, color: NAVY2, margin: 0 });
  s.addText("k · pₑ(k) = η − L", { x: 0.85, y: 1.98, w: 3.6, h: 0.42, fontFace: HDR, fontSize: 19, bold: true, color: AMBR, margin: 0 });
  s.addText("L ≥ 0 = harvest lost to the battery cap. Only the mean η enters; the fluid rule pₑ = min(1, η/k) is exactly the infinite-battery limit. Holds to 10⁻⁵ in simulation, Poisson and deterministic harvest alike.", {
    x: 0.85, y: 2.44, w: 3.6, h: 0.85, fontFace: BODY, fontSize: 10, color: INK, margin: 0, lineSpacingMultiple: 1.04,
  });

  // honest-claim card
  card(s, 0.55, 3.55, 4.15, 1.4, CARD2);
  s.addText([
    { text: "Finite battery ⇒ downward pressure on k∗, ", options: { bold: true, color: NAVY2 } },
    { text: "not a hard ceiling: the overflow loss L(B,k) varies with k, so the pₑ bound doesn’t order the objectives — a ceiling winner keeps winning for large enough B.", options: { color: INK } },
  ], { x: 0.85, y: 3.68, w: 3.6, h: 1.15, fontFace: BODY, fontSize: 10.5, margin: 0, lineSpacingMultiple: 1.05 });

  // right: e11 bar chart k* vs B (η = 4 series; η = 6 sampled at different B, see caption)
  s.addChart(pres.charts.BAR, [
    { name: "η = 4", labels: ["B = 4", "B = 5", "B = 6", "B = 64"], values: [2, 3, 3, 4] },
  ], {
    ...chartBase, x: 4.95, y: 1.45, w: 4.55, h: 3.05, barDir: "col",
    chartColors: [AMBR], barGapWidthPct: 80,
    showLegend: false,
    catAxisTitle: "battery capacity B (copies)", showCatAxisTitle: true, catAxisTitleFontSize: 10, catAxisTitleColor: MUT,
    valAxisTitle: "PAoI-optimal degree k* at η = 4", showValAxisTitle: true, valAxisTitleFontSize: 10, valAxisTitleColor: MUT,
    valAxisMaxVal: 5,
    showValue: true, dataLabelPosition: "outEnd", dataLabelColor: INK, dataLabelFontSize: 10,
  });
  s.addText("shrinking the battery pushes k* down (at η = 6 it falls 6 → 4 by B = 6) — quantified, not assumed.", {
    x: 4.95, y: 4.55, w: 4.55, h: 0.32, fontFace: BODY, fontSize: 9.5, italic: true, color: MUT, align: "center", margin: 0,
  });

  footer(s, 10);
  s.addNotes("The fluid throttle is replaced by the stationary law of a finite energy queue. Work conservation gives k*pe = eta - L, distribution-free - only the mean harvest matters at this order. Honesty slide: finite battery presses k* down empirically (bars, real data), but it is NOT a universal ceiling at floor(eta) - the overflow loss depends on k, so objectives are not ordered pointwise. This precision came out of adversarial review.");
}

// =====================================================================
// SLIDE 11 — POLICY (real data policy_sweep)
// =====================================================================
{
  const s = pres.addSlide();
  s.background = { color: WHT };
  titleBar(s, "From theorem to knob", "An O(1) two-candidate policy on top of CGR");

  // policy card
  card(s, 0.55, 1.45, 4.15, 2.0);
  s.addText("The rule", { x: 0.85, y: 1.6, w: 3.6, h: 0.3, fontFace: BODY, fontSize: 12.5, bold: true, color: NAVY2, margin: 0 });
  s.addText("kₚₒₗ = argmin over { ⌊η⌋, ⌈η⌉ } of A(k),  clipped to [1, Kₘₐₓ]", {
    x: 0.85, y: 1.94, w: 3.6, h: 0.55, fontFace: HDR, fontSize: 13, bold: true, color: NAVY2, margin: 0, lineSpacingMultiple: 1.05,
  });
  s.addText([
    { text: "Two objective evaluations — O(1), local, no sweep. ", options: { bold: true, color: TEAL } },
    { text: "Driven by the slow mean energy-adequacy η (a set-point, not a per-window controller). CGR picks the routes; the policy picks how many.", options: { color: INK } },
  ], { x: 0.85, y: 2.56, w: 3.6, h: 0.85, fontFace: BODY, fontSize: 10.5, margin: 0, lineSpacingMultiple: 1.04 });

  // robustness card
  card(s, 0.55, 3.65, 4.15, 1.3, CARD2);
  s.addText([
    { text: "Prediction-error robustness:  ", options: { bold: true, color: NAVY2 } },
    { text: "as contact predictions degrade (α → 0.4), the optimum stays at ⌊η⌋ (+19% PAoI); the “reserve energy” heuristic under-replicates (+50%). Replication is the right hedge.", options: { color: INK } },
  ], { x: 0.85, y: 3.78, w: 3.6, h: 1.05, fontFace: BODY, fontSize: 10.5, margin: 0, lineSpacingMultiple: 1.05 });

  // right: envelope chart (policy_sweep, real)
  const etas = ["1.5", "2", "2.5", "3", "3.5", "4", "5", "6", "8"];
  s.addChart(pres.charts.LINE, [
    { name: "k=1", labels: etas, values: [1.410, 1.410, 1.410, 1.410, 1.410, 1.410, 1.410, 1.410, 1.411] },
    { name: "k=2", labels: etas, values: [1.580, 1.256, 1.248, 1.248, 1.248, 1.248, 1.248, 1.248, 1.248] },
    { name: "k=3", labels: etas, values: [2.165, 1.668, 1.368, 1.177, 1.169, 1.169, 1.169, 1.169, 1.169] },
    { name: "k=4", labels: etas, values: [2.787, 2.122, 1.723, 1.455, 1.265, 1.131, 1.123, 1.123, 1.123] },
    { name: "adaptive policy", labels: etas, values: [1.410, 1.256, 1.248, 1.177, 1.169, 1.131, 1.123, 1.123, 1.123] },
  ], {
    ...chartBase, x: 4.95, y: 1.45, w: 4.55, h: 3.1,
    chartColors: ["C3CCE0", "9DABC9", "7A8DB5", "5B6B8C", "E8630A"],
    lineSize: 1.75, lineDataSymbol: "none",
    showLegend: true, legendPos: "t",
    catAxisTitle: "energy adequacy η", showCatAxisTitle: true, catAxisTitleFontSize: 10, catAxisTitleColor: MUT,
    valAxisTitle: "mean PAoI / P", showValAxisTitle: true, valAxisTitleFontSize: 10, valAxisTitleColor: MUT,
  });
  s.addText("the policy (orange) rides the lower envelope of every fixed degree — matched the exhaustive optimum at all η.", {
    x: 4.95, y: 4.58, w: 4.55, h: 0.35, fontFace: BODY, fontSize: 9.5, italic: true, color: MUT, align: "center", margin: 0,
  });

  footer(s, 11);
  s.addNotes("The theorem becomes a deployable knob: evaluate the objective at floor(eta) and ceil(eta) only - O(1) - and clip to Kmax. It layers on CGR: CGR answers WHICH routes, we answer HOW MANY copies. Real data: the adaptive policy rides the lower envelope of all fixed degrees and matched the exhaustive optimum at every sampled energy level. Bonus: robust to contact-prediction error - keep replicating, don't reserve energy.");
}

// =====================================================================
// SLIDE 12 — TAIL + RUCOP (real data)
// =====================================================================
{
  const s = pres.addSlide();
  s.background = { color: WHT };
  titleBar(s, "Beyond the mean", "Deadline tails collapse; RUCoP composes, not competes");

  // CCDF chart (left, real data)
  const dl = ["1.0", "1.1", "1.25", "1.5", "1.75", "2.0"];
  s.addChart(pres.charts.LINE, [
    { name: "k = 1", labels: dl, values: [1.0, 0.804, 0.654, 0.405, 0.155, 0.0] },
    { name: "k = 2", labels: dl, values: [1.0, 0.648, 0.429, 0.165, 0.024, 0.0] },
    { name: "k = 4", labels: dl, values: [1.0, 0.420, 0.184, 0.027, 0.0005, 0.0] },
  ], {
    ...chartBase, x: 0.45, y: 1.5, w: 4.45, h: 2.95,
    chartColors: ["9DABC9", VIOL, ORNG], lineSize: 2.5, lineDataSymbol: "circle", lineDataSymbolSize: 5,
    showLegend: true, legendPos: "t",
    catAxisTitle: "freshness deadline (units of P)", showCatAxisTitle: true, catAxisTitleFontSize: 10, catAxisTitleColor: MUT,
    valAxisTitle: "P( PAoI > deadline )", showValAxisTitle: true, valAxisTitleFontSize: 10, valAxisTitleColor: MUT,
  });
  s.addText("15× fewer 1.5P-deadline violations at k = 4; p99 drops 1.90P → 1.59P.", {
    x: 0.45, y: 4.47, w: 4.45, h: 0.32, fontFace: BODY, fontSize: 9.5, italic: true, color: MUT, align: "center", margin: 0,
  });

  // RUCoP card (right)
  card(s, 5.15, 1.5, 4.35, 3.3);
  s.addText("vs. a RUCoP-style MDP core", { x: 5.45, y: 1.66, w: 3.8, h: 0.32, fontFace: BODY, fontSize: 13, bold: true, color: NAVY2, margin: 0 });
  s.addText("Holder-set backward induction (delivery-optimal, energy-blind) on an illustrative uncertain diamond. The delivery-vs-copies frontier is concave — copies past the knee buy little.", {
    x: 5.45, y: 2.0, w: 3.8, h: 0.75, fontFace: BODY, fontSize: 10.5, color: INK, margin: 0, lineSpacingMultiple: 1.04,
  });
  statCallout(s, 5.45, 2.9, 1.8, "94.7%", "of the MDP’s delivery\nat our k∗ = 2", TEAL, 28);
  statCallout(s, 7.5, 2.9, 1.8, "40%", "of its energy\nspend", AMBR, 28);
  s.addText("Complementary: the MDP picks which routes, our threshold picks how many copies — the natural energy-aware extension of CGR-UCoP.", {
    x: 5.45, y: 4.05, w: 3.8, h: 0.65, fontFace: BODY, fontSize: 10, italic: true, color: MUT, margin: 0, lineSpacingMultiple: 1.03,
  });

  footer(s, 12);
  s.addNotes("Two decision-maker views. Left: mission-critical traffic cares about the tail - replication pulls the deadline-violation CCDF in sharply, 15x fewer violations of a 1.5P deadline at k=4. Right: against a RUCoP-style MDP core (honest label: decision core on an illustrative instance, not benchmark-scale) - the frontier is concave, so our energy-derived degree gets ~95% of delivery for 40% of energy. The two compose: their routes, our copy count.");
}

// =====================================================================
// SLIDE 13 — VALIDATION (tier2 real data)
// =====================================================================
{
  const s = pres.addSlide();
  s.background = { color: WHT };
  titleBar(s, "Validation — three tiers", "Analysis → Monte-Carlo → real Bundle Protocol/CGR");

  // left: tier2 crossover chart (r3_sweep, real)
  const etas2 = ["0.6", "1.0", "1.5", "2.0", "3.0", "6.0"];
  s.addChart(pres.charts.LINE, [
    { name: "single-copy CGR", labels: etas2, values: [50972, 50536, 49533, 48914, 46475, 40189] },
    { name: "2-copy CGR router", labels: etas2, values: [7989, 7809, 7650, 7574, 7166, 6844] },
  ], {
    ...chartBase, x: 0.45, y: 1.5, w: 4.45, h: 2.95,
    chartColors: ["9DABC9", VIOL], lineSize: 2.5, lineDataSymbol: "circle", lineDataSymbolSize: 5,
    showLegend: true, legendPos: "t",
    catAxisTitle: "energy adequacy η", showCatAxisTitle: true, catAxisTitleFontSize: 10, catAxisTitleColor: MUT,
    valAxisTitle: "mean PAoI (s)", showValAxisTitle: true, valAxisTitleFontSize: 10, valAxisTitleColor: MUT,
  });
  s.addText("dtnsim (real BP/CGR stack), 10 seeds, 95% CIs — two copies cut PAoI ~6× by hedging relay faults.", {
    x: 0.45, y: 4.47, w: 4.45, h: 0.32, fontFace: BODY, fontSize: 9.5, italic: true, color: MUT, align: "center", margin: 0,
  });

  // right: stat grid
  const stats = [
    { big: "0.0%", lab: "delay error vs closed form\n(2453.9 s vs 2453.9 s, full\nmixed residual histogram)", c: VIOL },
    { big: "0.06%", lab: "error on a real Iridium-NEXT\nTLE contact plan\n(101 passes, Skyfield)", c: TEAL },
    { big: "1.1%", lab: "additive-residual error on the\n3-hop heterogeneous chain\n(sensor→UAV→LEO→gateway)", c: ORNG },
    { big: "14 / 14", lab: "experiments pass\n(E1–E14, incl. the η★ = 3.82\nceiling flip)", c: AMBR },
  ];
  stats.forEach((st, i) => {
    const x = 5.15 + (i % 2) * 2.25, y = 1.5 + Math.floor(i / 2) * 1.7;
    card(s, x, y, 2.1, 1.55);
    s.addText(st.big, { x, y: y + 0.14, w: 2.1, h: 0.5, fontFace: HDR, fontSize: 26, bold: true, color: st.c, align: "center", margin: 0 });
    s.addText(st.lab, { x: x + 0.08, y: y + 0.66, w: 1.94, h: 0.85, fontFace: BODY, fontSize: 8.8, color: MUT, align: "center", margin: 0, lineSpacingMultiple: 1.0 });
  });

  footer(s, 13);
  s.addNotes("Every claim is triple-validated: closed form, model-exact Monte-Carlo (Tier 1, E1-E14 all pass), and dtnsim - a real Bundle Protocol / CGR simulator from the RUCoP lineage, extended with our energy module and a CGR-native k-copy router. Highlights: exact delay match on the synthetic plan; 0.06% on a real Iridium TLE contact plan; residual additivity on the full heterogeneous chain to 1.1%; and the 6x PAoI cut from 2-copy CGR routing under relay faults. Scenario files are public.");
}

// =====================================================================
// SLIDE 14 — GROUND TRUTH: REAL EPHEMERIS + FLIGHT SOFTWARE
// =====================================================================
{
  const s = pres.addSlide();
  s.background = { color: WHT };
  titleBar(s, "Validation — ground truth", "Real ephemeris and flight software close the loop");

  // left: two-copy gain by pair phasing (real Iridium pairs, horizontal bars)
  s.addChart(pres.charts.BAR, [
    {
      name: "two-copy gain",
      labels: ["anti-phased pair (ρ = −0.51)", "independent ideal ⅔(1−δ)", "near-indep. pair (ρ = +0.07)", "phase-locked pair (ρ = +0.88)"],
      values: [0.410, 0.606, 0.635, 0.952],
    },
  ], {
    ...chartBase, x: 0.4, y: 1.5, w: 4.55, h: 2.9, barDir: "bar",
    chartColors: [TEAL], barGapWidthPct: 55,
    invertedColors: ["9DABC9"],
    showLegend: false,
    valAxisTitle: "E[Rmin,2] / E[R1]  (lower = fresher)", showValAxisTitle: true,
    valAxisTitleFontSize: 9.5, valAxisTitleColor: MUT,
    valAxisMaxVal: 1.0,
    catAxisLabelFontSize: 8.5,
    showValue: true, dataLabelPosition: "outEnd", dataLabelColor: INK, dataLabelFontSize: 9,
    dataLabelFormatCode: "0.00",
  });
  s.addText("44 real Iridium-NEXT pairs over Svalbard: the gain is set by pass-phase alignment — plannable from the contact plan → phase-aware copy placement.", {
    x: 0.4, y: 4.42, w: 4.55, h: 0.55, fontFace: BODY, fontSize: 9.5, italic: true, color: MUT, align: "center", margin: 0,
  });

  // right top: ION card
  card(s, 5.15, 1.5, 4.35, 1.85);
  s.addText("ION 4.1.4 — reference BP flight software", { x: 5.45, y: 1.64, w: 3.8, h: 0.3, fontFace: BODY, fontSize: 12.5, bold: true, color: NAVY2, margin: 0 });
  statCallout(s, 5.35, 2.0, 1.32, "974/974", "bundles delivered\nlossless, 2 h run", TEAL, 17);
  statCallout(s, 6.72, 2.0, 1.32, "24.34 s", "residual, exact per\nbundle (law: 24.30 s)", VIOL, 17);
  statCallout(s, 8.09, 2.0, 1.32, "2.5 ± 0.5 s", "dispatch lag = the\nmodel's Tₛ, measured", AMBR, 17);
  s.addText("delay = R + Tₛ decomposition validated in flight code; Tₛ ≈ 0.04% at operational periods.", {
    x: 5.45, y: 3.02, w: 3.8, h: 0.3, fontFace: BODY, fontSize: 9, italic: true, color: MUT, margin: 0 });

  // right bottom: E15 card
  card(s, 5.15, 3.55, 4.35, 1.42, CARD2);
  s.addText("Bursty harvest (E15)", { x: 5.45, y: 3.68, w: 3.8, h: 0.28, fontFace: BODY, fontSize: 12.5, bold: true, color: NAVY2, margin: 0 });
  s.addText([
    { text: "k* = ⌊η⌋ unchanged", options: { bold: true, color: TEAL } },
    { text: " up to harvest dwell ≈ 10 periods; work conservation ≤ 3×10⁻⁴ under all correlation (distribution-free). Correlation moves the ", options: { color: INK } },
    { text: "tail", options: { bold: true, color: ORNG } },
    { text: " (p99 +72%), not the threshold; boundary at dwell ≈ 50.", options: { color: INK } },
  ], { x: 5.45, y: 3.98, w: 3.8, h: 0.92, fontFace: BODY, fontSize: 10, margin: 0, lineSpacingMultiple: 1.05 });

  footer(s, 14);
  s.addNotes("New ground-truth tier. Left: 44 real Iridium pairs - the two-copy gain runs 0.41 to 0.95 purely on pass-phase alignment; anti-phased beats even the independent ideal, phase-locked makes replication worthless. Contact plans are known, so this is computable at planning time: phase-aware copy placement, now a numbered contribution. Right: ION flight software - 974/974 lossless, the residual law exact per bundle, and the 2.5 s dispatch lag is literally the model's T_s measured in flight code. Below: bursty harvest keeps the threshold, inflates only the tail.");
}

// =====================================================================
// SLIDE 15 — CONCLUSION (dark)
// =====================================================================
{
  const s = pres.addSlide();
  s.background = { color: NAVY };
  // faint orbit art echo
  s.addShape(pres.shapes.OVAL, { x: 6.9, y: -3.4, w: 7.4, h: 7.4, fill: { type: "none" }, line: { color: "223252", width: 1 } });
  s.addShape(pres.shapes.OVAL, { x: 7.9, y: -2.6, w: 5.6, h: 5.6, fill: { type: "none" }, line: { color: "1D2B49", width: 1 } });
  s.addShape(pres.shapes.OVAL, { x: 8.6, y: 0.35, w: 0.12, h: 0.12, fill: { color: VIOL }, line: { type: "none" } });

  titleBar(s, "Takeaways", "Freshness has a price in copies — now we know it", { dark: true, kickerColor: AMBR });

  const tk = [
    { h: "A residual-wait law, not a queueing delay", b: "One alternating-renewal model covers LEO / UAV / terrestrial; mean quadratic, peak linear — and peak can drop below mean past an exact CV threshold.", c: VIOL },
    { h: "Replication is priced by dispersion", b: "A second copy buys ½ E|Y⁽¹⁾−Y⁽²⁾| of freshness — phase mixing tells you exactly when latencies compose.", c: TEAL },
    { h: "k∗ tracks the energy budget", b: "Launch ⌊η⌋ copies — or ⌈η⌉ when a skip is worth it — capped at Kₘₐₓ. An O(1) rule that rides the optimum on top of CGR.", c: AMBR },
    { h: "Validated where DTN insiders live", b: "Model-exact MC + real BP/CGR stack + ION flight software + real Iridium ephemeris — where phase-aware copy placement emerges as a plannable design rule.", c: ORNG },
  ];
  tk.forEach((t, i) => {
    const x = 0.55 + (i % 2) * 4.6, y = 1.5 + Math.floor(i / 2) * 1.42;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 4.4, h: 1.26, fill: { color: "18233F" }, line: { color: "27355A", width: 1 }, rectRadius: 0.07 });
    s.addShape(pres.shapes.OVAL, { x: x + 0.2, y: y + 0.19, w: 0.13, h: 0.13, fill: { color: t.c }, line: { type: "none" } });
    s.addText(t.h, { x: x + 0.44, y: y + 0.09, w: 3.85, h: 0.32, fontFace: BODY, fontSize: 12, bold: true, color: WHT, margin: 0 });
    s.addText(t.b, { x: x + 0.44, y: y + 0.42, w: 3.85, h: 0.78, fontFace: BODY, fontSize: 9.8, color: ICE, margin: 0, lineSpacingMultiple: 1.03 });
  });

  s.addText([
    { text: "Ongoing:  ", options: { bold: true, color: AMBR } },
    { text: "regime-aware adaptation under extreme harvest persistence • RUCoP’s route set under the degree cap • tail-constrained policy", options: { color: ICE } },
  ], { x: 0.55, y: 4.5, w: 8.95, h: 0.35, fontFace: BODY, fontSize: 11.5, margin: 0 });

  footer(s, 15, true);
  s.addNotes("Close on the four takeaways: (1) scheduled gating gives a residual-wait law - one renewal model, all segments, with the AoI/PAoI inversion; (2) replication is priced by latency dispersion via the Gini identity; (3) the optimal copy count tracks the energy budget - floor or ceiling of eta, an O(1) policy over CGR; (4) validated down to a real BP/CGR stack and real Iridium ephemeris. Ongoing: correlated harvests, composing with RUCoP routes, tail constraints. Thank you.");
}

pres.writeFile({ fileName: "/Users/tiffanyzhang/haoyu/jn/slides/paoi-dtn-deck.pptx" }).then(() => console.log("deck written"));
