// SAARTHI — SIH 2026 PS 26186 · 13-slide idea deck (PM-003 content)
// Official SIH template is NOT in this repo. Risa must paste these
// beats into the official PPT (DECK-001) — do not restyle the template.
// Palette: cream / moss / terracotta — welfare, not alarm.
// Run: node build-deck.js

const pptxgen = require("pptxgenjs");

const CREAM = "F4EFE6";
const INK = "1F2A24";
const INK_SOFT = "4A5550";
const MOSS = "3F5C4A";
const MOSS_LT = "6B8F78";
const TERR = "B5694A";
const PAPER = "FFFbf5";
const LINE = "D9D0C3";

const F_H = "Georgia";
const F_B = "Calibri";
const F_M = "Consolas";

const pres = new pptxgen();
pres.defineLayout({ name: "WIDE", width: 13.333, height: 7.5 });
pres.layout = "WIDE";
pres.author = "kv · SAARTHI";
pres.title = "SAARTHI — SIH 2026 PS 26186";
pres.subject = "Idea presentation content deck. Rebuild inside official SIH template before portal upload.";

function footer(slide, n) {
  slide.addText("SAARTHI  ·  PS 26186  ·  CRPF / MHA  ·  content deck — paste into official SIH template", {
    x: 0.5, y: 7.15, w: 10.5, h: 0.22,
    fontFace: F_M, fontSize: 10, color: MOSS_LT, margin: 0,
  });
  slide.addText(String(n).padStart(2, "0") + " / 13", {
    x: 11.6, y: 7.15, w: 1.2, h: 0.22,
    fontFace: F_M, fontSize: 10, color: MOSS, align: "right", margin: 0,
  });
}

function bg(slide) {
  slide.background = { color: CREAM };
}

function card(slide, x, y, w, h) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h,
    fill: { color: PAPER },
    line: { color: LINE, width: 1 },
  });
}

// ----- 1 Title -----
{
  const s = pres.addSlide();
  bg(s);
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 0.18, h: 7.5, fill: { color: MOSS } });
  s.addText("SMART INDIA HACKATHON  2026", {
    x: 0.7, y: 0.55, w: 12, h: 0.3,
    fontFace: F_M, fontSize: 12, color: MOSS, charSpacing: 3, margin: 0,
  });
  s.addText("SAARTHI", {
    x: 0.7, y: 1.4, w: 12, h: 1.1,
    fontFace: F_H, fontSize: 60, color: INK, bold: true, margin: 0,
  });
  s.addText("सारथी  —  the charioteer who guides", {
    x: 0.7, y: 2.5, w: 12, h: 0.4,
    fontFace: F_H, fontSize: 18, color: TERR, italic: true, margin: 0,
  });
  s.addText("Predictive personnel stress & welfare monitoring for uniformed forces", {
    x: 0.7, y: 3.15, w: 11.5, h: 0.4,
    fontFace: F_B, fontSize: 18, color: INK_SOFT, margin: 0,
  });
  const meta = [
    ["PS ID", "26186"],
    ["Org", "CRPF / Ministry of Home Affairs"],
    ["Theme", "Software  ·  MedTech / HealthTech"],
    ["Rule", "Welfare, not discipline"],
  ];
  meta.forEach((row, i) => {
    const x = 0.7 + (i % 2) * 6.1;
    const y = 4.2 + Math.floor(i / 2) * 0.95;
    card(s, x, y, 5.8, 0.8);
    s.addText(row[0], { x: x + 0.2, y: y + 0.08, w: 5.4, h: 0.25, fontFace: F_M, fontSize: 11, color: MOSS, margin: 0 });
    s.addText(row[1], { x: x + 0.2, y: y + 0.35, w: 5.4, h: 0.35, fontFace: F_B, fontSize: 16, color: INK, margin: 0 });
  });
  footer(s, 1);
}

// ----- 2 Problem -----
{
  const s = pres.addSlide();
  bg(s);
  s.addText("The problem", {
    x: 0.5, y: 0.35, w: 12, h: 0.45,
    fontFace: F_H, fontSize: 28, color: INK, margin: 0,
  });
  s.addText("Stress is caught after incidents — not before.", {
    x: 0.5, y: 0.9, w: 12, h: 0.4,
    fontFace: F_B, fontSize: 18, color: INK_SOFT, margin: 0,
  });
  card(s, 0.5, 1.55, 12.3, 2.4);
  s.addText("654", {
    x: 0.8, y: 1.75, w: 3.2, h: 1.2,
    fontFace: F_H, fontSize: 64, color: TERR, bold: true, margin: 0,
  });
  s.addText("CAPF suicides\nin 5 years", {
    x: 4.1, y: 1.95, w: 3.2, h: 0.9,
    fontFace: F_B, fontSize: 18, color: INK, margin: 0,
  });
  s.addText("~50,000", {
    x: 7.5, y: 1.75, w: 2.6, h: 1.2,
    fontFace: F_H, fontSize: 40, color: MOSS, bold: true, margin: 0,
  });
  s.addText("resignations\nin the same window", {
    x: 10.2, y: 1.95, w: 2.4, h: 0.9,
    fontFace: F_B, fontSize: 16, color: INK, margin: 0,
  });
  s.addText("Source: ThePrint, “654 suicides, 50,000 resignations in 5 years — the crisis stalking India’s CAPFs”. One statistic. Cited. Not invented.", {
    x: 0.8, y: 3.35, w: 11.7, h: 0.4,
    fontFace: F_B, fontSize: 12, color: INK_SOFT, italic: true, margin: 0,
  });
  const pts = [
    ["Today", "Manual observation + self-report. Help arrives late."],
    ["Stigma", "A named “mental-health app” is dead on arrival in ACR culture."],
    ["Need", "Predictive welfare, privacy in architecture, not in a promise."],
  ];
  pts.forEach((p, i) => {
    const x = 0.5 + i * 4.15;
    card(s, x, 4.2, 3.95, 2.0);
    s.addText(p[0], { x: x + 0.2, y: 4.35, w: 3.55, h: 0.35, fontFace: F_M, fontSize: 12, color: MOSS, margin: 0 });
    s.addText(p[1], { x: x + 0.2, y: 4.8, w: 3.55, h: 1.15, fontFace: F_B, fontSize: 16, color: INK, margin: 0 });
  });
  footer(s, 2);
}

// ----- 3 Team -----
{
  const s = pres.addSlide();
  bg(s);
  s.addText("Team & roles", {
    x: 0.5, y: 0.35, w: 12, h: 0.45,
    fontFace: F_H, fontSize: 28, color: INK, margin: 0,
  });
  s.addText("Six members. Each answers their own domain. ≥ 1 female member (SIH rule).", {
    x: 0.5, y: 0.85, w: 12, h: 0.3,
    fontFace: F_B, fontSize: 14, color: INK_SOFT, margin: 0,
  });
  const people = [
    ["kv", "PM · backend", "Engines, privacy law, architecture"],
    ["neel", "Co-backbone", "Apps, dashboards, design, RBAC"],
    ["ayush", "ML assistant", "Citations, instrument factsheet"],
    ["manan", "Compliance", "Statute pack, privacy walkthrough"],
    ["risa", "Presentation", "Official-template deck + practice"],
    ["tejas", "QA / demo", "Manual tests, fallback video"],
  ];
  people.forEach((p, i) => {
    const col = i % 3;
    const row = Math.floor(i / 3);
    const x = 0.5 + col * 4.2;
    const y = 1.4 + row * 2.55;
    card(s, x, y, 4.0, 2.35);
    s.addShape(pres.shapes.RECTANGLE, { x, y, w: 0.12, h: 2.35, fill: { color: i < 2 ? MOSS : TERR } });
    s.addText(p[0], { x: x + 0.35, y: y + 0.25, w: 3.45, h: 0.45, fontFace: F_H, fontSize: 24, color: INK, margin: 0 });
    s.addText(p[1], { x: x + 0.35, y: y + 0.75, w: 3.45, h: 0.35, fontFace: F_M, fontSize: 13, color: MOSS, margin: 0 });
    s.addText(p[2], { x: x + 0.35, y: y + 1.25, w: 3.45, h: 0.8, fontFace: F_B, fontSize: 15, color: INK_SOFT, margin: 0 });
  });
  footer(s, 3);
}

// ----- 4 Solution -----
{
  const s = pres.addSlide();
  bg(s);
  s.addText("Solution in one loop", {
    x: 0.5, y: 0.35, w: 12, h: 0.45,
    fontFace: F_H, fontSize: 28, color: INK, margin: 0,
  });
  const steps = [
    ["1", "Detect", "HR signals the force already holds. Zero extra work."],
    ["2", "Explain", "Rules engine. Top-3 factors. No black box."],
    ["3", "Help", "Buddy → counsellor ≤ 24 h → roster change → Tele-MANAS."],
    ["4", "Verify", "Trend down. Who-viewed receipt. Loop closed."],
  ];
  steps.forEach((st, i) => {
    const x = 0.5 + i * 3.2;
    card(s, x, 1.15, 3.05, 3.35);
    s.addText(st[0], { x: x + 0.2, y: 1.3, w: 2.65, h: 0.7, fontFace: F_H, fontSize: 36, color: TERR, margin: 0 });
    s.addText(st[1], { x: x + 0.2, y: 2.1, w: 2.65, h: 0.45, fontFace: F_H, fontSize: 22, color: INK, margin: 0 });
    s.addText(st[2], { x: x + 0.2, y: 2.65, w: 2.65, h: 1.5, fontFace: F_B, fontSize: 15, color: INK_SOFT, margin: 0 });
  });
  card(s, 0.5, 4.7, 12.3, 1.95);
  s.addText("The firewall", {
    x: 0.75, y: 4.9, w: 11.8, h: 0.35, fontFace: F_M, fontSize: 13, color: MOSS, margin: 0,
  });
  s.addText("An individual risk score cannot reach command, ACR, promotion or posting. Not a policy sentence — there is no API that can carry it there.", {
    x: 0.75, y: 5.35, w: 11.8, h: 1.0, fontFace: F_B, fontSize: 18, color: INK, margin: 0,
  });
  footer(s, 4);
}

// ----- 5 Methodology -----
{
  const s = pres.addSlide();
  bg(s);
  s.addText("How help is routed", {
    x: 0.5, y: 0.35, w: 12, h: 0.45,
    fontFace: F_H, fontSize: 28, color: INK, margin: 0,
  });
  s.addText("Grandma test: jawan keeps doing duty → counsellor gets an explainable alert in 24 hours → commander never sees a name.", {
    x: 0.5, y: 0.85, w: 12.3, h: 0.4,
    fontFace: F_B, fontSize: 14, color: INK_SOFT, italic: true, margin: 0,
  });
  const ladder = [
    ["Green", "0–39", "Self-help nudge", "App"],
    ["Amber", "40–59", "Buddy + informal JCO check", "72 h"],
    ["Red", "60–79", "Counsellor outreach", "≤ 24 h"],
    ["Critical", "80+", "Immediate contact + duty mod", "Now"],
  ];
  ladder.forEach((r, i) => {
    const y = 1.45 + i * 1.2;
    card(s, 0.5, y, 12.3, 1.1);
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.5, y, w: 0.18, h: 1.1,
      fill: { color: ["6B8F78", "C4A35A", "B5694A", "7A2E2E"][i] },
    });
    s.addText(r[0], { x: 0.95, y: y + 0.18, w: 2.2, h: 0.7, fontFace: F_H, fontSize: 22, color: INK, valign: "middle", margin: 0 });
    s.addText(r[1], { x: 3.3, y: y + 0.18, w: 1.8, h: 0.7, fontFace: F_M, fontSize: 16, color: MOSS, valign: "middle", margin: 0 });
    s.addText(r[2], { x: 5.3, y: y + 0.18, w: 5.0, h: 0.7, fontFace: F_B, fontSize: 18, color: INK, valign: "middle", margin: 0 });
    s.addText(r[3], { x: 10.4, y: y + 0.18, w: 2.1, h: 0.7, fontFace: F_B, fontSize: 16, color: TERR, valign: "middle", align: "right", margin: 0 });
  });
  footer(s, 5);
}

// ----- 6 Stack -----
{
  const s = pres.addSlide();
  bg(s);
  s.addText("What we built vs what we used", {
    x: 0.5, y: 0.35, w: 12, h: 0.45,
    fontFace: F_H, fontSize: 28, color: INK, margin: 0,
  });
  const cols = [
    ["Built", MOSS, ["Rules engine v1 (explainable)", "HR signal features (20)", "k-anonymity ≥ 5 aggregator", "Dual-key unmask + who-viewed", "Append-only hash-chained audit"]],
    ["Off the shelf", TERR, ["FastAPI + PostgreSQL / SQLite", "Expo / React Native (apps)", "Next.js consoles", "On-device voice features only", "Tele-MANAS 14416 as a recorded handoff"]],
    ["Deliberately not", INK, ["No ML accuracy claims (no labels)", "No iOS in v1", "No blockchain / IoT combo", "No foreign SaaS on welfare data", "On-prem / MeghRaj deployable"]],
  ];
  cols.forEach((c, i) => {
    const x = 0.5 + i * 4.2;
    card(s, x, 1.1, 4.0, 5.5);
    s.addShape(pres.shapes.RECTANGLE, { x, y: 1.1, w: 4.0, h: 0.7, fill: { color: c[1] } });
    s.addText(c[0], { x: x + 0.2, y: 1.22, w: 3.6, h: 0.5, fontFace: F_B, fontSize: 18, color: "FFFFFF", margin: 0 });
    c[2].forEach((line, j) => {
      s.addText(line, {
        x: x + 0.25, y: 2.05 + j * 0.8, w: 3.5, h: 0.7,
        fontFace: F_B, fontSize: 15, color: INK, margin: 0,
      });
    });
  });
  footer(s, 6);
}

// ----- 7 Architecture -----
{
  const s = pres.addSlide();
  bg(s);
  s.addText("Two-tier output  —  the split is the product", {
    x: 0.5, y: 0.35, w: 12.3, h: 0.45,
    fontFace: F_H, fontSize: 26, color: INK, margin: 0,
  });
  card(s, 0.5, 1.1, 6.0, 5.5);
  s.addText("COUNSELLOR", { x: 0.75, y: 1.3, w: 5.5, h: 0.35, fontFace: F_M, fontSize: 13, color: MOSS, margin: 0 });
  s.addText("Sees a person", {
    x: 0.75, y: 1.75, w: 5.5, h: 0.5, fontFace: F_H, fontSize: 24, color: INK, margin: 0,
  });
  [
    "Pseudonym until dual-key unmask",
    "Score + top-3 factors",
    "Consent artefact required",
    "Every read lands in who-viewed",
  ].forEach((t, i) => {
    s.addText(t, { x: 0.75, y: 2.5 + i * 0.85, w: 5.5, h: 0.7, fontFace: F_B, fontSize: 18, color: INK_SOFT, margin: 0 });
  });
  card(s, 6.8, 1.1, 6.0, 5.5);
  s.addText("COMMANDER", { x: 7.05, y: 1.3, w: 5.5, h: 0.35, fontFace: F_M, fontSize: 13, color: TERR, margin: 0 });
  s.addText("Sees a unit", {
    x: 7.05, y: 1.75, w: 5.5, h: 0.5, fontFace: F_H, fontSize: 24, color: INK, margin: 0,
  });
  [
    "Aggregates only, k ≥ 5",
    "No names, no scores, no IDs",
    "Personnel lookup returns 403",
    "Complement cells also suppressed",
  ].forEach((t, i) => {
    s.addText(t, { x: 7.05, y: 2.5 + i * 0.85, w: 5.5, h: 0.7, fontFace: F_B, fontSize: 18, color: INK_SOFT, margin: 0 });
  });
  footer(s, 7);
}

// ----- 8 Differentiation -----
{
  const s = pres.addSlide();
  bg(s);
  s.addText("Why not a consumer wellness app?", {
    x: 0.5, y: 0.35, w: 12.3, h: 0.45,
    fontFace: F_H, fontSize: 26, color: INK, margin: 0,
  });
  const rows = [
    [
      { text: " ", options: { fill: { color: MOSS }, color: "FFFFFF", bold: true } },
      { text: "Consumer / HRIS", options: { fill: { color: MOSS }, color: "FFFFFF", bold: true } },
      { text: "SAARTHI", options: { fill: { color: MOSS }, color: "FFFFFF", bold: true } },
    ],
    ["Privacy", "Policy promise", "Architectural firewall (k ≥ 5)"],
    ["Offline", "Cloud-first", "Low-end Android, queue + sync"],
    ["Language", "English UI", "Hindi + English, icon-first"],
    ["Care path", "App content", "Tele-MANAS 14416 recorded"],
    ["Sovereignty", "Foreign SaaS", "On-prem / NIC MeghRaj"],
    ["AI claim", "Black-box %", "Rules v1; ML only with labels"],
  ];
  s.addTable(rows, {
    x: 0.5, y: 1.05, w: 12.3, h: 5.5,
    colW: [2.3, 5.0, 5.0],
    border: { pt: 0.5, color: LINE },
    fontFace: F_B,
    fontSize: 14,
    color: INK,
    valign: "middle",
    align: "left",
  });
  footer(s, 8);
}

// ----- 9 Prototype -----
{
  const s = pres.addSlide();
  bg(s);
  s.addText("What works today", {
    x: 0.5, y: 0.35, w: 12, h: 0.45,
    fontFace: F_H, fontSize: 28, color: INK, margin: 0,
  });
  s.addText("Backend on main. Demo persona: Constable, 34, 3rd Bn. Password for all seed users: saarthi.", {
    x: 0.5, y: 0.85, w: 12.3, h: 0.35,
    fontFace: F_B, fontSize: 14, color: INK_SOFT, margin: 0,
  });
  const demo = [
    ["GET /risk/ps_demo01/explanation", "Counsellor sees factors, not a black box"],
    ["GET /aggregates/unit/3BN", "Commander sees k ≥ 5, no names"],
    ["GET /welfare/personnel/{id}", "403 — the judge’s attack, pre-answered"],
    ["GET /app/who-viewed", "Jawan sees who opened the record"],
  ];
  demo.forEach((d, i) => {
    const y = 1.4 + i * 1.15;
    card(s, 0.5, y, 12.3, 1.05);
    s.addText(d[0], { x: 0.75, y: y + 0.12, w: 12, h: 0.35, fontFace: F_M, fontSize: 14, color: MOSS, margin: 0 });
    s.addText(d[1], { x: 0.75, y: y + 0.5, w: 12, h: 0.4, fontFace: F_B, fontSize: 18, color: INK, margin: 0 });
  });
  footer(s, 9);
}

// ----- 10 36h -----
{
  const s = pres.addSlide();
  bg(s);
  s.addText("36-hour finale  —  hours attached", {
    x: 0.5, y: 0.35, w: 12.3, h: 0.45,
    fontFace: F_H, fontSize: 26, color: INK, margin: 0,
  });
  const hours = [
    ["0–1", "kv + neel", "Clone, seed, pytest, API up"],
    ["1–4", "neel / kv", "Wire apps; freeze ruleset"],
    ["4–8", "risa + tejas", "Venue deck + new fallback video"],
    ["8–12", "kv + neel", "One bug pass (offline, k, dual-key)"],
    ["12–16", "rotation", "Sleep. 3 up / 3 down."],
    ["16–24", "all", "Mentor comments → board. 3× rehearsal."],
    ["24–32", "neel / kv", "UI polish only. Q&A drill."],
    ["32–36", "tejas", "Bag: laptop, hotspot, pen drive, PDF, mp4"],
  ];
  hours.forEach((h, i) => {
    const col = i < 4 ? 0 : 1;
    const row = i % 4;
    const x = 0.5 + col * 6.4;
    const y = 1.05 + row * 1.35;
    card(s, x, y, 6.2, 1.22);
    s.addText(h[0], { x: x + 0.2, y: y + 0.15, w: 1.6, h: 0.9, fontFace: F_M, fontSize: 16, color: TERR, valign: "middle", margin: 0 });
    s.addText(h[1], { x: x + 1.9, y: y + 0.15, w: 4.05, h: 0.4, fontFace: F_B, fontSize: 14, color: MOSS, margin: 0 });
    s.addText(h[2], { x: x + 1.9, y: y + 0.55, w: 4.05, h: 0.5, fontFace: F_B, fontSize: 15, color: INK, margin: 0 });
  });
  footer(s, 10);
}

// ----- 11 Impact -----
{
  const s = pres.addSlide();
  bg(s);
  s.addText("Pilot KPIs  —  no invented numbers", {
    x: 0.5, y: 0.35, w: 12.3, h: 0.45,
    fontFace: F_H, fontSize: 26, color: INK, margin: 0,
  });
  const kpis = [
    ["≥ 30%", "Voluntary participation", "Reasoned estimate (roster-first)"],
    ["≤ 24 h", "Red flag → counsellor", "Design target (FR-09)"],
    ["0", "Scores reaching command", "Architectural guarantee"],
    ["0", "Punitive outcomes", "Monitored trust signal"],
  ];
  kpis.forEach((k, i) => {
    const x = 0.5 + (i % 4) * 3.2;
    card(s, x, 1.1, 3.05, 3.15);
    s.addText(k[0], { x: x + 0.15, y: 1.3, w: 2.75, h: 1.1, fontFace: F_H, fontSize: 32, color: TERR, margin: 0 });
    s.addText(k[1], { x: x + 0.15, y: 2.5, w: 2.75, h: 0.8, fontFace: F_B, fontSize: 16, color: INK, margin: 0 });
    s.addText(k[2], { x: x + 0.15, y: 3.4, w: 2.75, h: 0.6, fontFace: F_B, fontSize: 13, color: INK_SOFT, margin: 0 });
  });
  card(s, 0.5, 4.5, 12.3, 2.15);
  s.addText("Scale (reasoned, not adjectives)", {
    x: 0.75, y: 4.7, w: 11.8, h: 0.3, fontFace: F_M, fontSize: 12, color: MOSS, margin: 0,
  });
  s.addText("Technical High — rules recompute a battalion on one box.  Adoption Med — needs officer-first buy-in.  Outcome evidence Low→Med — labels accrue over months.", {
    x: 0.75, y: 5.15, w: 11.8, h: 1.2, fontFace: F_B, fontSize: 16, color: INK, margin: 0,
  });
  footer(s, 11);
}

// ----- 12 Out of scope -----
{
  const s = pres.addSlide();
  bg(s);
  s.addText("What we will not build", {
    x: 0.5, y: 0.35, w: 12, h: 0.45,
    fontFace: F_H, fontSize: 28, color: INK, margin: 0,
  });
  s.addText("Reads as maturity. Preempts “what will you NOT build?”", {
    x: 0.5, y: 0.85, w: 12, h: 0.3,
    fontFace: F_B, fontSize: 14, color: INK_SOFT, italic: true, margin: 0,
  });
  const no = [
    ["No facial emotion / CCTV", "Contested science. Reads as surveillance."],
    ["No phone or relationship monitoring", "Trust-killing. Fails DPDP necessity."],
    ["No scores in ACR / promotion / posting", "Firewall is architectural."],
    ["No ML on day one", "Zero labels. Honest rules instead."],
    ["No clinical diagnosis", "Reflection support, not a condition."],
    ["No automated weapon restriction", "Counsellor recommends. Commander decides."],
  ];
  no.forEach((n, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = 0.5 + col * 6.4;
    const y = 1.35 + row * 1.7;
    card(s, x, y, 6.2, 1.55);
    s.addText(n[0], { x: x + 0.25, y: y + 0.2, w: 5.7, h: 0.5, fontFace: F_H, fontSize: 18, color: INK, margin: 0 });
    s.addText(n[1], { x: x + 0.25, y: y + 0.75, w: 5.7, h: 0.55, fontFace: F_B, fontSize: 15, color: INK_SOFT, margin: 0 });
  });
  footer(s, 12);
}

// ----- 13 Close -----
{
  const s = pres.addSlide();
  bg(s);
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 0.18, h: 7.5, fill: { color: MOSS } });
  s.addText("The number to remember", {
    x: 0.7, y: 0.7, w: 12, h: 0.4,
    fontFace: F_M, fontSize: 14, color: MOSS, charSpacing: 2, margin: 0,
  });
  s.addText("0", {
    x: 0.7, y: 1.2, w: 12, h: 2.0,
    fontFace: F_H, fontSize: 120, color: TERR, margin: 0,
  });
  s.addText("individual risk scores that can reach command.\nGuaranteed by architecture — not by a promise.", {
    x: 0.7, y: 3.3, w: 12, h: 1.1,
    fontFace: F_B, fontSize: 22, color: INK, margin: 0,
  });
  s.addText("Repo  github.com/dyrok/sih-hackathon-26     ·     Demo  python -m app.seed && uvicorn app.main:app", {
    x: 0.7, y: 4.7, w: 12, h: 0.4,
    fontFace: F_M, fontSize: 13, color: MOSS, margin: 0,
  });
  s.addText("Welfare, not discipline.", {
    x: 0.7, y: 5.4, w: 12, h: 0.5,
    fontFace: F_H, fontSize: 22, color: INK, italic: true, margin: 0,
  });
  footer(s, 13);
}

pres.writeFile({ fileName: __dirname + "/SAARTHI-idea-presentation.pptx" })
  .then(() => console.log("wrote SAARTHI-idea-presentation.pptx"))
  .catch((err) => {
    console.error(err);
    process.exit(1);
  });
