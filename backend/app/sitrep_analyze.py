"""Heuristic sitrep analysis — a demo larp, not a clinical instrument.

The officer is dictating a *duty log*. We also derive a private tone/mood
hint from the same words plus a cheap on-device energy sketch. Labels only
(no invented percentages). The wellness fields never enter unit aggregates.
"""

from __future__ import annotations

import re

FATIGUE = ("tired", "long", "exhausted", "drained", "voice is going", "thak", "late")
INCIDENT = ("incident", "firing", "casualty", "contact", "ied", "blast", "ambush")
LEAVE = ("leave", "chhutti", "backlog")
POSITIVE = ("good", "fine", "steady", "clear", "sports", "parade went well")
NIGHT = ("night", "picquet", "2100", "perimeter")

QUESTION_BANK = (
    {"id": "hours", "need": ("long", "hours", "duty", "picquet", "perimeter", "feet")},
    {"id": "sleep", "need": ("tired", "voice", "night", "long", "exhausted")},
    {"id": "incident", "need": INCIDENT},
    {"id": "leave", "need": LEAVE},
    {"id": "tomorrow", "need": ()},
)


def _blob(text: str) -> str:
    return " ".join((text or "").lower().split())


def _has(blob: str, words: tuple[str, ...]) -> bool:
    return any(w in blob for w in words)


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", (text or "").strip())
    return [p.strip() for p in parts if len(p.strip()) > 8]


def pick_questions(transcript: str, limit: int = 2) -> list[str]:
    blob = _blob(transcript)
    picked: list[str] = []
    for q in QUESTION_BANK:
        if len(picked) >= limit:
            break
        if not q["need"] or _has(blob, q["need"]):
            if q["id"] not in picked:
                picked.append(q["id"])
    if "tomorrow" not in picked and len(picked) < limit:
        picked.append("tomorrow")
    return picked[:limit]


def analyze(
    transcript: str,
    *,
    rms_mean: float | None = None,
    rms_var: float | None = None,
    answers: list[dict] | None = None,
) -> dict:
    blob = _blob(transcript)
    bullets = _sentences(transcript)[:8]
    flags: list[str] = []
    if _has(blob, FATIGUE):
        flags.append("fatigue_language")
    if _has(blob, INCIDENT):
        flags.append("incident_load")
    if _has(blob, NIGHT):
        flags.append("night_duty")
    if _has(blob, LEAVE):
        flags.append("admin_backlog")

    tone = "calm"
    if rms_var is not None and rms_var > 0.004:
        tone = "strained"
    elif rms_mean is not None and rms_mean < 0.02:
        tone = "flat"
    if "fatigue_language" in flags:
        tone = "strained" if tone != "flat" else "flat"

    mood = 7
    if "fatigue_language" in flags:
        mood -= 2
    if "incident_load" in flags:
        mood -= 2
    if tone == "strained":
        mood -= 1
    if _has(blob, POSITIVE):
        mood += 1
    mood = max(1, min(9, mood))
    mood_label = "light" if mood >= 7 else "heavy" if mood <= 4 else "steady"

    if answers:
        joined = " ".join(str(a.get("answer", "")) for a in answers).lower()
        if any(w in joined for w in ("no sleep", "4 hour", "three hour", "nahi soya")):
            flags.append("short_sleep")
            mood = max(1, mood - 1)
            mood_label = "heavy" if mood <= 4 else mood_label

    if bullets:
        summary = bullets[0]
        if len(bullets) > 1:
            summary = "%s (+%d more)" % (bullets[0], len(bullets) - 1)
    else:
        summary = "Duty log captured."

    wellness = {
        "calm": "You sounded even. Private note only — this is not a unit score.",
        "strained": "The last stretch sounded heavier than the start. Private note only.",
        "flat": "Delivery was flat — often just fatigue. Private note only.",
    }[tone]
    if "short_sleep" in flags:
        wellness = "Short sleep flagged from your own answers. Private note only."

    return {
        "work_summary": summary,
        "work_bullets": bullets or [transcript.strip() or "Duty log captured."],
        "tone_label": tone,
        "mood_label": mood_label,
        "mood_score": mood,
        "wellness_summary": wellness,
        "flags": flags,
        "questions": pick_questions(transcript),
        "heuristic": True,
    }
