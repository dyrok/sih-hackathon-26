#!/usr/bin/env python3
"""13-page landscape PDF matching the idea deck (PM-003)."""
from __future__ import annotations

from reportlab.lib.colors import Color, HexColor, white
from reportlab.lib.pagesizes import landscape
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

W, H = 13.333 * inch, 7.5 * inch
CREAM = HexColor("#F4EFE6")
INK = HexColor("#1F2A24")
SOFT = HexColor("#4A5550")
MOSS = HexColor("#3F5C4A")
MOSS_LT = HexColor("#6B8F78")
TERR = HexColor("#B5694A")
PAPER = HexColor("#FFFBF5")
LINE = HexColor("#D9D0C3")
OUT = __file__.replace("build-pdf.py", "SAARTHI-idea-presentation.pdf")


def footer(c: canvas.Canvas, n: int) -> None:
    c.setFillColor(MOSS_LT)
    c.setFont("Times-Roman", 8)
    c.drawString(0.5 * inch, 0.22 * inch, "SAARTHI   |   PS 26186   |   CRPF / MHA   |   content deck  -  paste into official SIH template")
    c.drawRightString(W - 0.5 * inch, 0.22 * inch, f"{n:02d} / 13")


def bg(c: canvas.Canvas) -> None:
    c.setFillColor(CREAM)
    c.rect(0, 0, W, H, fill=1, stroke=0)


def card(c: canvas.Canvas, x, y, w, h) -> None:
    c.setFillColor(PAPER)
    c.setStrokeColor(LINE)
    c.setLineWidth(0.6)
    c.roundRect(x, y, w, h, 4, fill=1, stroke=1)


def wrapped(c, text, x, y, w, font, size, color, leading=None):
    c.setFillColor(color)
    c.setFont(font, size)
    leading = leading or size * 1.25
    from reportlab.pdfbase.pdfmetrics import stringWidth
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if stringWidth(trial, font, size) <= w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    for i, line in enumerate(lines):
        c.drawString(x, y - i * leading, line)
    return len(lines)


def page_end(c, n):
    footer(c, n)
    c.showPage()


def main() -> None:
    c = canvas.Canvas(OUT, pagesize=(W, H))
    c.setTitle("SAARTHI  -  SIH 2026 PS 26186")
    c.setAuthor("kv  |  SAARTHI")

    # 1
    bg(c)
    c.setFillColor(MOSS)
    c.rect(0, 0, 0.16 * inch, H, fill=1, stroke=0)
    c.setFillColor(MOSS)
    c.setFont("Courier", 11)
    c.drawString(0.7 * inch, H - 0.7 * inch, "SMART INDIA HACKATHON  2026")
    c.setFillColor(INK)
    c.setFont("Times-Bold", 48)
    c.drawString(0.7 * inch, H - 1.7 * inch, "SAARTHI")
    c.setFillColor(TERR)
    c.setFont("Times-Italic", 16)
    c.drawString(0.7 * inch, H - 2.2 * inch, "सारथी   -   the charioteer who guides")
    c.setFillColor(SOFT)
    c.setFont("Helvetica", 14)
    c.drawString(0.7 * inch, H - 2.7 * inch, "Predictive personnel stress & welfare monitoring for uniformed forces")
    meta = [
        ("PS ID", "26186"),
        ("Org", "CRPF / Ministry of Home Affairs"),
        ("Theme", "Software   |   MedTech / HealthTech"),
        ("Rule", "Welfare, not discipline"),
    ]
    for i, (k, v) in enumerate(meta):
        x = 0.7 * inch + (i % 2) * 6.1 * inch
        y = H - 4.3 * inch - (i // 2) * 1.05 * inch
        card(c, x, y, 5.8 * inch, 0.9 * inch)
        c.setFillColor(MOSS)
        c.setFont("Courier", 10)
        c.drawString(x + 0.2 * inch, y + 0.55 * inch, k)
        c.setFillColor(INK)
        c.setFont("Helvetica", 13)
        c.drawString(x + 0.2 * inch, y + 0.25 * inch, v)
    page_end(c, 1)

    # 2
    bg(c)
    c.setFillColor(INK)
    c.setFont("Times-Bold", 24)
    c.drawString(0.5 * inch, H - 0.7 * inch, "The problem")
    c.setFillColor(SOFT)
    c.setFont("Helvetica", 14)
    c.drawString(0.5 * inch, H - 1.05 * inch, "Stress is caught after incidents  -  not before.")
    card(c, 0.5 * inch, H - 3.5 * inch, 12.3 * inch, 2.2 * inch)
    c.setFillColor(TERR)
    c.setFont("Times-Bold", 48)
    c.drawString(0.8 * inch, H - 2.4 * inch, "654")
    c.setFillColor(INK)
    c.setFont("Helvetica", 13)
    wrapped(c, "CAPF suicides in 5 years", 3.4 * inch, H - 2.1 * inch, 2.8 * inch, "Helvetica", 13, INK)
    c.setFillColor(MOSS)
    c.setFont("Times-Bold", 32)
    c.drawString(7.2 * inch, H - 2.35 * inch, "~50,000")
    wrapped(c, "resignations in the same window", 10.0 * inch, H - 2.1 * inch, 2.5 * inch, "Helvetica", 12, INK)
    c.setFillColor(SOFT)
    c.setFont("Times-Italic", 9)
    wrapped(
        c,
        'Source: ThePrint, 654 suicides, 50,000 resignations in 5 years - the crisis stalking Indias CAPFs. One statistic. Cited.',
        0.8 * inch,
        H - 3.25 * inch,
        11.6 * inch,
        "Times-Italic",
        9,
        SOFT,
    )
    pts = [
        ("Today", "Manual observation + self-report. Help arrives late."),
        ("Stigma", "A named mental-health app is dead on arrival in ACR culture."),
        ("Need", "Predictive welfare, privacy in architecture, not in a promise."),
    ]
    for i, (t, b) in enumerate(pts):
        x = 0.5 * inch + i * 4.15 * inch
        card(c, x, 0.55 * inch, 3.95 * inch, 1.85 * inch)
        c.setFillColor(MOSS)
        c.setFont("Courier", 11)
        c.drawString(x + 0.2 * inch, 1.95 * inch, t)
        wrapped(c, b, x + 0.2 * inch, 1.55 * inch, 3.5 * inch, "Helvetica", 12, INK)
    page_end(c, 2)

    # 3
    bg(c)
    c.setFillColor(INK)
    c.setFont("Times-Bold", 24)
    c.drawString(0.5 * inch, H - 0.7 * inch, "Team & roles")
    c.setFillColor(SOFT)
    c.setFont("Helvetica", 12)
    c.drawString(0.5 * inch, H - 1.05 * inch, "Six members. Each answers their own domain. >= 1 female member (SIH rule).")
    people = [
        ("kv", "PM  |  backend", "Engines, privacy law, architecture"),
        ("neel", "Co-backbone", "Apps, dashboards, design, RBAC"),
        ("ayush", "ML assistant", "Citations, instrument factsheet"),
        ("manan", "Compliance", "Statute pack, privacy walkthrough"),
        ("risa", "Presentation", "Official-template deck + practice"),
        ("tejas", "QA / demo", "Manual tests, fallback video"),
    ]
    for i, (name, role, job) in enumerate(people):
        col, row = i % 3, i // 3
        x = 0.5 * inch + col * 4.2 * inch
        y = H - 3.55 * inch - row * 2.45 * inch
        card(c, x, y, 4.0 * inch, 2.25 * inch)
        c.setFillColor(MOSS if i < 2 else TERR)
        c.rect(x, y, 0.1 * inch, 2.25 * inch, fill=1, stroke=0)
        c.setFillColor(INK)
        c.setFont("Times-Bold", 20)
        c.drawString(x + 0.3 * inch, y + 1.6 * inch, name)
        c.setFillColor(MOSS)
        c.setFont("Courier", 11)
        c.drawString(x + 0.3 * inch, y + 1.2 * inch, role)
        wrapped(c, job, x + 0.3 * inch, y + 0.75 * inch, 3.4 * inch, "Helvetica", 12, SOFT)
    page_end(c, 3)

    # 4
    bg(c)
    c.setFillColor(INK)
    c.setFont("Times-Bold", 24)
    c.drawString(0.5 * inch, H - 0.7 * inch, "Solution in one loop")
    steps = [
        ("1", "Detect", "HR signals the force already holds. Zero extra work."),
        ("2", "Explain", "Rules engine. Top-3 factors. No black box."),
        ("3", "Help", "Buddy -> counsellor <= 24 h -> roster change -> Tele-MANAS."),
        ("4", "Verify", "Trend down. Who-viewed receipt. Loop closed."),
    ]
    for i, (n, t, b) in enumerate(steps):
        x = 0.5 * inch + i * 3.2 * inch
        card(c, x, H - 4.55 * inch, 3.05 * inch, 3.4 * inch)
        c.setFillColor(TERR)
        c.setFont("Times-Bold", 28)
        c.drawString(x + 0.2 * inch, H - 1.7 * inch, n)
        c.setFillColor(INK)
        c.setFont("Times-Bold", 16)
        c.drawString(x + 0.2 * inch, H - 2.25 * inch, t)
        wrapped(c, b, x + 0.2 * inch, H - 2.7 * inch, 2.65 * inch, "Helvetica", 12, SOFT)
    card(c, 0.5 * inch, 0.55 * inch, 12.3 * inch, 1.85 * inch)
    c.setFillColor(MOSS)
    c.setFont("Courier", 11)
    c.drawString(0.75 * inch, 1.95 * inch, "THE FIREWALL")
    wrapped(
        c,
        "An individual risk score cannot reach command, ACR, promotion or posting. Not a policy sentence  -  there is no API that can carry it there.",
        0.75 * inch,
        1.5 * inch,
        11.8 * inch,
        "Helvetica",
        13,
        INK,
    )
    page_end(c, 4)

    # 5
    bg(c)
    c.setFillColor(INK)
    c.setFont("Times-Bold", 24)
    c.drawString(0.5 * inch, H - 0.7 * inch, "How help is routed")
    c.setFillColor(SOFT)
    c.setFont("Times-Italic", 11)
    wrapped(
        c,
        "Grandma test: jawan keeps doing duty -> counsellor gets an explainable alert in 24 hours -> commander never sees a name.",
        0.5 * inch,
        H - 1.1 * inch,
        12.3 * inch,
        "Times-Italic",
        11,
        SOFT,
    )
    ladder = [
        ("Green", "0-39", "Self-help nudge", "App", HexColor("#6B8F78")),
        ("Amber", "40-59", "Buddy + informal JCO check", "72 h", HexColor("#C4A35A")),
        ("Red", "60-79", "Counsellor outreach", "<= 24 h", HexColor("#B5694A")),
        ("Critical", "80+", "Immediate contact + duty mod", "Now", HexColor("#7A2E2E")),
    ]
    for i, (name, band, resp, sla, col) in enumerate(ladder):
        y = H - 2.45 * inch - i * 1.15 * inch
        card(c, 0.5 * inch, y, 12.3 * inch, 1.05 * inch)
        c.setFillColor(col)
        c.rect(0.5 * inch, y, 0.16 * inch, 1.05 * inch, fill=1, stroke=0)
        c.setFillColor(INK)
        c.setFont("Times-Bold", 16)
        c.drawString(0.9 * inch, y + 0.42 * inch, name)
        c.setFillColor(MOSS)
        c.setFont("Courier", 12)
        c.drawString(3.3 * inch, y + 0.42 * inch, band)
        c.setFillColor(INK)
        c.setFont("Helvetica", 13)
        c.drawString(5.3 * inch, y + 0.42 * inch, resp)
        c.setFillColor(TERR)
        c.drawRightString(12.5 * inch, y + 0.42 * inch, sla)
    page_end(c, 5)

    # 6
    bg(c)
    c.setFillColor(INK)
    c.setFont("Times-Bold", 24)
    c.drawString(0.5 * inch, H - 0.7 * inch, "What we built vs what we used")
    cols = [
        ("Built", MOSS, ["Rules engine v1 (explainable)", "HR signal features (20)", "k-anonymity >= 5 aggregator", "Dual-key unmask + who-viewed", "Append-only hash-chained audit"]),
        ("Off the shelf", TERR, ["FastAPI + PostgreSQL / SQLite", "Expo / React Native (apps)", "Next.js consoles", "On-device voice features only", "Tele-MANAS 14416 recorded handoff"]),
        ("Deliberately not", INK, ["No ML accuracy claims (no labels)", "No iOS in v1", "No blockchain / IoT combo", "No foreign SaaS on welfare data", "On-prem / MeghRaj deployable"]),
    ]
    for i, (title, col, items) in enumerate(cols):
        x = 0.5 * inch + i * 4.2 * inch
        card(c, x, 0.55 * inch, 4.0 * inch, 5.7 * inch)
        c.setFillColor(col)
        c.rect(x, 5.55 * inch, 4.0 * inch, 0.7 * inch, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(x + 0.2 * inch, 5.78 * inch, title)
        c.setFillColor(INK)
        for j, line in enumerate(items):
            wrapped(c, line, x + 0.25 * inch, 5.15 * inch - j * 0.85 * inch, 3.5 * inch, "Helvetica", 12, INK)
    page_end(c, 6)

    # 7
    bg(c)
    c.setFillColor(INK)
    c.setFont("Times-Bold", 22)
    c.drawString(0.5 * inch, H - 0.7 * inch, "Two-tier output   -   the split is the product")
    card(c, 0.5 * inch, 0.55 * inch, 6.0 * inch, 5.7 * inch)
    card(c, 6.8 * inch, 0.55 * inch, 6.0 * inch, 5.7 * inch)
    c.setFillColor(MOSS)
    c.setFont("Courier", 11)
    c.drawString(0.75 * inch, 5.85 * inch, "COUNSELLOR")
    c.setFillColor(TERR)
    c.drawString(7.05 * inch, 5.85 * inch, "COMMANDER")
    c.setFillColor(INK)
    c.setFont("Times-Bold", 20)
    c.drawString(0.75 * inch, 5.4 * inch, "Sees a person")
    c.drawString(7.05 * inch, 5.4 * inch, "Sees a unit")
    left = ["Pseudonym until dual-key unmask", "Score + top-3 factors", "Consent artefact required", "Every read lands in who-viewed"]
    right = ["Aggregates only, k >= 5", "No names, no scores, no IDs", "Personnel lookup returns 403", "Complement cells also suppressed"]
    for i, t in enumerate(left):
        wrapped(c, t, 0.75 * inch, 4.7 * inch - i * 0.9 * inch, 5.4 * inch, "Helvetica", 13, SOFT)
    for i, t in enumerate(right):
        wrapped(c, t, 7.05 * inch, 4.7 * inch - i * 0.9 * inch, 5.4 * inch, "Helvetica", 13, SOFT)
    page_end(c, 7)

    # 8
    bg(c)
    c.setFillColor(INK)
    c.setFont("Times-Bold", 22)
    c.drawString(0.5 * inch, H - 0.7 * inch, "Why not a consumer wellness app?")
    rows = [
        ("", "Consumer / HRIS", "SAARTHI"),
        ("Privacy", "Policy promise", "Architectural firewall (k >= 5)"),
        ("Offline", "Cloud-first", "Low-end Android, queue + sync"),
        ("Language", "English UI", "Hindi + English, icon-first"),
        ("Care path", "App content", "Tele-MANAS 14416 recorded"),
        ("Sovereignty", "Foreign SaaS", "On-prem / NIC MeghRaj"),
        ("AI claim", "Black-box %", "Rules v1; ML only with labels"),
    ]
    colw = [2.2 * inch, 5.0 * inch, 5.1 * inch]
    y0 = H - 1.35 * inch
    rh = 0.72 * inch
    for r, row in enumerate(rows):
        y = y0 - (r + 1) * rh
        x = 0.5 * inch
        if r == 0:
            c.setFillColor(MOSS)
            c.rect(x, y, sum(colw), rh, fill=1, stroke=0)
            c.setFillColor(white)
            font = "Helvetica-Bold"
        else:
            c.setFillColor(PAPER if r % 2 else CREAM)
            c.setStrokeColor(LINE)
            c.rect(x, y, sum(colw), rh, fill=1, stroke=1)
            c.setFillColor(INK)
            font = "Helvetica"
        xx = x + 0.12 * inch
        for i, cell in enumerate(row):
            c.setFont(font, 11 if r else 11)
            c.drawString(xx, y + 0.28 * inch, cell)
            xx += colw[i]
    page_end(c, 8)

    # 9
    bg(c)
    c.setFillColor(INK)
    c.setFont("Times-Bold", 24)
    c.drawString(0.5 * inch, H - 0.7 * inch, "What works today")
    c.setFillColor(SOFT)
    c.setFont("Helvetica", 11)
    c.drawString(0.5 * inch, H - 1.05 * inch, "Backend on main. Demo persona: Constable, 34, 3rd Bn. Password for all seed users: saarthi.")
    demo = [
        ("GET /risk/ps_demo01/explanation", "Counsellor sees factors, not a black box"),
        ("GET /aggregates/unit/3BN", "Commander sees k >= 5, no names"),
        ("GET /welfare/personnel/{id}", "403  -  the judge's attack, pre-answered"),
        ("GET /app/who-viewed", "Jawan sees who opened the record"),
    ]
    for i, (ep, cap) in enumerate(demo):
        y = H - 2.3 * inch - i * 1.15 * inch
        card(c, 0.5 * inch, y, 12.3 * inch, 1.05 * inch)
        c.setFillColor(MOSS)
        c.setFont("Courier", 11)
        c.drawString(0.75 * inch, y + 0.62 * inch, ep)
        c.setFillColor(INK)
        c.setFont("Helvetica", 14)
        c.drawString(0.75 * inch, y + 0.25 * inch, cap)
    page_end(c, 9)

    # 10
    bg(c)
    c.setFillColor(INK)
    c.setFont("Times-Bold", 22)
    c.drawString(0.5 * inch, H - 0.7 * inch, "36-hour finale   -   hours attached")
    hours = [
        ("0-1", "kv + neel", "Clone, seed, pytest, API up"),
        ("1-4", "neel / kv", "Wire apps; freeze ruleset"),
        ("4-8", "risa + tejas", "Venue deck + new fallback video"),
        ("8-12", "kv + neel", "One bug pass (offline, k, dual-key)"),
        ("12-16", "rotation", "Sleep. 3 up / 3 down."),
        ("16-24", "all", "Mentor comments -> board. 3x rehearsal."),
        ("24-32", "neel / kv", "UI polish only. Q&A drill."),
        ("32-36", "tejas", "Bag: laptop, hotspot, pen drive, PDF, mp4"),
    ]
    for i, (hr, who, what) in enumerate(hours):
        col, row = (0, i) if i < 4 else (1, i - 4)
        x = 0.5 * inch + col * 6.4 * inch
        y = H - 2.25 * inch - row * 1.3 * inch
        card(c, x, y, 6.2 * inch, 1.18 * inch)
        c.setFillColor(TERR)
        c.setFont("Courier", 12)
        c.drawString(x + 0.2 * inch, y + 0.5 * inch, hr)
        c.setFillColor(MOSS)
        c.setFont("Helvetica", 11)
        c.drawString(x + 1.7 * inch, y + 0.7 * inch, who)
        c.setFillColor(INK)
        c.setFont("Helvetica", 12)
        c.drawString(x + 1.7 * inch, y + 0.3 * inch, what)
    page_end(c, 10)

    # 11
    bg(c)
    c.setFillColor(INK)
    c.setFont("Times-Bold", 22)
    c.drawString(0.5 * inch, H - 0.7 * inch, "Pilot KPIs   -   no invented numbers")
    kpis = [
        (">= 30%", "Voluntary participation", "Reasoned estimate (roster-first)"),
        ("<= 24 h", "Red flag -> counsellor", "Design target (FR-09)"),
        ("0", "Scores reaching command", "Architectural guarantee"),
        ("0", "Punitive outcomes", "Monitored trust signal"),
    ]
    for i, (num, label, kind) in enumerate(kpis):
        x = 0.5 * inch + i * 3.2 * inch
        card(c, x, 3.55 * inch, 3.05 * inch, 2.85 * inch)
        c.setFillColor(TERR)
        c.setFont("Times-Bold", 26)
        c.drawString(x + 0.2 * inch, 5.7 * inch, num)
        wrapped(c, label, x + 0.2 * inch, 5.15 * inch, 2.65 * inch, "Helvetica", 12, INK)
        wrapped(c, kind, x + 0.2 * inch, 4.35 * inch, 2.65 * inch, "Helvetica", 10, SOFT)
    card(c, 0.5 * inch, 0.55 * inch, 12.3 * inch, 2.75 * inch)
    c.setFillColor(MOSS)
    c.setFont("Courier", 11)
    c.drawString(0.75 * inch, 2.85 * inch, "SCALE (REASONED, NOT ADJECTIVES)")
    wrapped(
        c,
        "Technical High  -  rules recompute a battalion on one box.  Adoption Med  -  needs officer-first buy-in.  Outcome evidence Low->Med  -  labels accrue over months.",
        0.75 * inch,
        2.4 * inch,
        11.8 * inch,
        "Helvetica",
        13,
        INK,
    )
    page_end(c, 11)

    # 12
    bg(c)
    c.setFillColor(INK)
    c.setFont("Times-Bold", 24)
    c.drawString(0.5 * inch, H - 0.7 * inch, "What we will not build")
    c.setFillColor(SOFT)
    c.setFont("Times-Italic", 11)
    c.drawString(0.5 * inch, H - 1.05 * inch, 'Reads as maturity. Preempts: what will you NOT build?')
    nos = [
        ("No facial emotion / CCTV", "Contested science. Reads as surveillance."),
        ("No phone or relationship monitoring", "Trust-killing. Fails DPDP necessity."),
        ("No scores in ACR / promotion / posting", "Firewall is architectural."),
        ("No ML on day one", "Zero labels. Honest rules instead."),
        ("No clinical diagnosis", "Reflection support, not a condition."),
        ("No automated weapon restriction", "Counsellor recommends. Commander decides."),
    ]
    for i, (t, b) in enumerate(nos):
        col, row = i % 2, i // 2
        x = 0.5 * inch + col * 6.4 * inch
        y = H - 2.7 * inch - row * 1.65 * inch
        card(c, x, y, 6.2 * inch, 1.5 * inch)
        wrapped(c, t, x + 0.25 * inch, y + 1.05 * inch, 5.7 * inch, "Times-Bold", 13, INK)
        wrapped(c, b, x + 0.25 * inch, y + 0.55 * inch, 5.7 * inch, "Helvetica", 12, SOFT)
    page_end(c, 12)

    # 13
    bg(c)
    c.setFillColor(MOSS)
    c.rect(0, 0, 0.16 * inch, H, fill=1, stroke=0)
    c.setFillColor(MOSS)
    c.setFont("Courier", 12)
    c.drawString(0.7 * inch, H - 0.9 * inch, "THE NUMBER TO REMEMBER")
    c.setFillColor(TERR)
    c.setFont("Times-Bold", 96)
    c.drawString(0.7 * inch, H - 2.7 * inch, "0")
    c.setFillColor(INK)
    c.setFont("Helvetica", 16)
    wrapped(
        c,
        "individual risk scores that can reach command. Guaranteed by architecture  -  not by a promise.",
        0.7 * inch,
        H - 3.4 * inch,
        11.8 * inch,
        "Helvetica",
        16,
        INK,
    )
    c.setFillColor(MOSS)
    c.setFont("Courier", 10)
    c.drawString(0.7 * inch, 2.3 * inch, "Repo  github.com/dyrok/sih-hackathon-26      |      Demo  python -m app.seed && uvicorn app.main:app")
    c.setFillColor(INK)
    c.setFont("Times-Italic", 18)
    c.drawString(0.7 * inch, 1.6 * inch, "Welfare, not discipline.")
    page_end(c, 13)

    c.save()
    print("wrote", OUT)


if __name__ == "__main__":
    main()
