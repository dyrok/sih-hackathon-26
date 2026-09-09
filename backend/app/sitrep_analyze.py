"""Sitrep analysis — Laguna (OpenRouter) with a local heuristic fallback.

The officer is dictating a *duty log*. Tone/mood stay private to that officer
and never enter unit aggregates (ADR-0003). Labels only — no invented
percentages. Seed data always uses the heuristic so fixtures stay deterministic.
"""

from __future__ import annotations

import json
import re

import httpx

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


_ALLOWED_TONE = {"calm", "strained", "flat"}
_ALLOWED_MOOD = {"light", "steady", "heavy"}
_ALLOWED_Q = {"hours", "sleep", "incident", "leave", "tomorrow"}
_ALLOWED_FLAGS = {
    "fatigue_language",
    "incident_load",
    "night_duty",
    "admin_backlog",
    "short_sleep",
    "llm",
}

_SYSTEM = """You write a CRPF officer's private duty-log notes.
Return ONLY compact JSON, no markdown.
Rules:
- work_summary: one sentence of what they DID (operations, not feelings).
- work_bullets: 2-6 short duty bullets from the transcript.
- tone_label: exactly calm, strained, or flat.
- mood_label: exactly light, steady, or heavy.
- mood_score: integer 1-9, higher is lighter. Do not invent a percentage.
- wellness_summary: one or two sentences, private to the officer, not a diagnosis, not a unit score.
- flags: subset of fatigue_language, incident_load, night_duty, admin_backlog, short_sleep.
- questions: 1-2 ids from hours, sleep, incident, leave, tomorrow.
Never name another person. Never produce a command-facing risk score."""


def _coerce(raw: dict, fallback: dict) -> dict:
    tone = raw.get("tone_label") if raw.get("tone_label") in _ALLOWED_TONE else fallback["tone_label"]
    mood_label = raw.get("mood_label") if raw.get("mood_label") in _ALLOWED_MOOD else fallback["mood_label"]
    try:
        mood = int(raw.get("mood_score", fallback["mood_score"]))
    except (TypeError, ValueError):
        mood = fallback["mood_score"]
    mood = max(1, min(9, mood))
    bullets = raw.get("work_bullets")
    if not isinstance(bullets, list) or not bullets:
        bullets = fallback["work_bullets"]
    bullets = [str(b).strip() for b in bullets if str(b).strip()][:8]
    questions = [q for q in raw.get("questions") or [] if q in _ALLOWED_Q][:2]
    if not questions:
        questions = fallback["questions"]
    flags = [f for f in raw.get("flags") or [] if f in _ALLOWED_FLAGS]
    summary = str(raw.get("work_summary") or "").strip() or fallback["work_summary"]
    wellness = str(raw.get("wellness_summary") or "").strip() or fallback["wellness_summary"]
    return {
        "work_summary": summary[:400],
        "work_bullets": bullets,
        "tone_label": tone,
        "mood_label": mood_label,
        "mood_score": mood,
        "wellness_summary": wellness[:500],
        "flags": flags,
        "questions": questions,
        "heuristic": False,
    }


def _extract_json(text: str) -> dict | None:
    text = (text or "").strip()
    if not text:
        return None
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        pass
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        data = json.loads(text[start : end + 1])
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None


def analyze_with_llm(
    transcript: str,
    *,
    rms_mean: float | None = None,
    rms_var: float | None = None,
    answers: list[dict] | None = None,
    fallback: dict,
) -> dict | None:
    from .config import get_settings

    settings = get_settings()
    key = (settings.openrouter_api_key or "").strip()
    if not key:
        return None
    payload = {
        "transcript": transcript,
        "voice_energy": {"rms_mean": rms_mean, "rms_var": rms_var},
        "officer_answers": answers or [],
    }
    models = [settings.openrouter_model]
    for extra in ("poolside/laguna-s-2.1:free", "poolside/laguna-xs-2.1:free"):
        if extra not in models:
            models.append(extra)
    last_status = None
    try:
        with httpx.Client(timeout=35.0) as client:
            for model in models:
                r = client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": "Bearer " + key,
                        "Content-Type": "application/json",
                        "HTTP-Referer": "http://127.0.0.1:3300",
                        "X-Title": "SAARTHI sitrep",
                    },
                    json={
                        "model": model,
                        "messages": [
                            {
                                "role": "user",
                                "content": _SYSTEM + "\n\nINPUT:\n" + json.dumps(payload),
                            }
                        ],
                        "temperature": 0.2,
                        "max_tokens": 500,
                    },
                )
                last_status = r.status_code
                if r.status_code == 429:
                    continue
                r.raise_for_status()
                msg = (r.json().get("choices") or [{}])[0].get("message") or {}
                content = msg.get("content") or msg.get("reasoning") or ""
                parsed = _extract_json(content if isinstance(content, str) else "")
                if not parsed:
                    continue
                out = _coerce(parsed, fallback)
                if "llm" not in out["flags"]:
                    out["flags"] = [*out["flags"], "llm"]
                return out
    except Exception:
        return None
    if last_status:
        # Visible in the API log; never includes the key.
        print("sitrep: Laguna unavailable (HTTP %s); using heuristic" % last_status)
    return None


def analyze(
    transcript: str,
    *,
    rms_mean: float | None = None,
    rms_var: float | None = None,
    answers: list[dict] | None = None,
    use_llm: bool = False,
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

    heuristic = {
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
    if use_llm:
        llm = analyze_with_llm(
            transcript,
            rms_mean=rms_mean,
            rms_var=rms_var,
            answers=answers,
            fallback=heuristic,
        )
        if llm:
            return llm
    return heuristic
