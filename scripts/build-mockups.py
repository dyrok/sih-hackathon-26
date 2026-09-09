# -*- coding: utf-8 -*-
"""UX-002 — emit the .dc.html mockup artboards for the check-in flow and the
privacy panel, in English and romanised Hindi.

The screens are generated from one template plus the app's OWN i18n table, for
the same reason the app is: a mockup that drifts from the shipped strings is a
mockup nobody trusts. Every colour, size, radius and control height below is
lifted from web/packages/tokens/dist/tokens.css, web/packages/ui/src/ui.css and
web/apps/jawan/app/globals.css — no rounding, no 8px-grid snapping.
"""
from __future__ import annotations

import json
import pathlib

REPO = pathlib.Path(__file__).resolve().parents[1]
OUT = REPO / "docs/architecture/design/mockups"
I18N = REPO / "web/packages/i18n/src"

en = json.loads((I18N / "en.json").read_text(encoding="utf-8"))
hi = json.loads((I18N / "hi.json").read_text(encoding="utf-8"))

W, H = 390, 844

# --- tokens, resolved exactly as dist/tokens.css emits them -----------------
T = {
    "surface": "#f7f6f2",
    "raised": "#ffffff",
    "ink": "#2f332c",
    "ink2": "#61635a",
    "olive": "#5a6b33",
    "oliveSoft": "#ecefe0",
    "saffron": "#d98a1e",
    "green": "#4a8a55",
    "amber": "#e0a020",
    "red": "#c04535",
    "s1": "4px",
    "s2": "16px",
    "s3": "36px",
    "xs": "12px",
    "sm": "16px",
    "md": "21px",
    "lg": "27px",
    "xl": "35px",
    "lh": "1.5",
    "lhhi": "1.6",
}

FONT = "'Noto Sans', system-ui, -apple-system, sans-serif"

HEAD = """<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;600;700&display=swap">
  <style>
    body {{ margin: 0; font-family: {font}; }}
    a {{ color: {olive}; }}
    a:hover {{ color: {ink}; }}
    * {{ box-sizing: border-box; }}
  </style>
</helmet>
""".format(font=FONT, olive=T["olive"], ink=T["ink"])

TAIL = """</x-dc>
{script}
</body>
</html>
"""

STATIC_SCRIPT = """<script data-dc-script data-props='{{"$preview":{{"width":{w},"height":{h}}}}}'>
class Component extends DCLogic {{}}
</script>""".format(w=W, h=H)


def icon(paths: str, size: int = 22, color: str | None = None) -> str:
    c = color or "currentColor"
    return (
        '<svg width="%d" height="%d" viewBox="0 0 24 24" fill="none" stroke="%s" '
        'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">%s</svg>'
        % (size, size, c, paths)
    )


ICONS = {
    "clipboard": '<rect x="5" y="4" width="14" height="17" rx="2" /><path d="M9 4a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2" /><path d="M9 10h6M9 14h6M9 18h3" />',
    "heart": '<path d="M12 20s-7-4.5-9-9a5 5 0 0 1 9-3 5 5 0 0 1 9 3c-2 4.5-9 9-9 9Z" />',
    "user": '<circle cx="12" cy="8" r="4" /><path d="M4 20c1.5-3.5 4.5-5 8-5s6.5 1.5 8 5" />',
    "clock": '<circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" />',
    "shield": '<path d="M12 3 5 6v5c0 5 3 8 7 10 4-2 7-5 7-10V6l-7-3Z" />',
    "mic": '<rect x="9" y="3" width="6" height="11" rx="3" /><path d="M5 11a7 7 0 0 0 14 0M12 18v3M9 21h6" />',
    "arrow": '<path d="M15 18l-6-6 6-6" />',
    "lock": '<rect x="5" y="11" width="14" height="9" rx="2" /><path d="M8 11V8a4 4 0 0 1 8 0v3" />',
    "check": '<path d="M4 12.5 9 17.5 20 6.5" />',
}

# ---------------------------------------------------------------------------
# Screen chrome
# ---------------------------------------------------------------------------


def shell(body: str, *, lang: str, active: str, dim: bool = False, overlay: str = "") -> str:
    """The real app chrome: top bar (brand + sync pill), main, 3-tab bottom bar.

    Deliberately NO fake status bar and no fake keyboard — on a real phone the
    OS draws those on top of the layout, and a painted copy reads as doubled up.
    """
    d = en if lang == "en" else hi
    lh = T["lh"] if lang == "en" else T["lhhi"]
    tabs = [("roster", "nav.roster", "clipboard"), ("welfare", "nav.welfare", "heart"), ("me", "nav.me", "user")]
    tab_html = "".join(
        '<div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:2px;'
        'padding:8px 0 10px;min-height:56px;color:%s">%s'
        '<span style="font-size:%s;font-weight:600">%s</span></div>'
        % (T["olive"] if tid == active else T["ink2"], icon(ICONS[ic], 22), T["xs"], d[key])
        for tid, key, ic in tabs
    )
    dimmer = (
        '<div style="position:absolute;inset:0;background:rgb(47 51 44 / 0.45);"></div>' if dim else ""
    )
    return (
        '<div style="position:relative;width:%dpx;height:%dpx;overflow:hidden;'
        'background:%s;color:%s;font-family:%s;font-size:%s;line-height:%s">'
        # top bar
        '<div style="display:flex;align-items:center;justify-content:space-between;gap:%s;padding:%s %s 0">'
        '<span style="font-size:%s;font-weight:700;color:%s;letter-spacing:0.02em">SAARTHI</span>'
        '<span style="display:inline-flex;align-items:center;gap:6px;font-size:%s;color:%s;'
        'background:%s;border-radius:999px;padding:4px 12px;min-height:28px">%s</span>'
        "</div>"
        '<div style="padding:%s;padding-bottom:96px">%s</div>'
        "%s%s"
        # bottom tabs
        '<div style="position:absolute;bottom:0;left:0;right:0;display:flex;background:%s;'
        'border-top:1px solid %s">%s</div>'
        "</div>"
        % (
            W,
            H,
            T["surface"],
            T["ink"],
            FONT,
            T["sm"],
            lh,
            T["s2"],
            T["s2"],
            T["s2"],
            T["md"],
            T["olive"],
            T["xs"],
            T["ink2"],
            T["oliveSoft"],
            d["sync.pill.synced"],
            T["s2"],
            body,
            dimmer,
            overlay,
            T["raised"],
            T["oliveSoft"],
            tab_html,
        )
    )


def title(text: str, first: bool = True) -> str:
    return '<h1 style="font-size:%s;font-weight:700;margin:%s 0 0">%s</h1>' % (
        T["md"],
        "0" if first else T["s3"],
        text,
    )


def lead(text: str) -> str:
    return '<p style="font-size:%s;color:%s;margin:%s 0 %s">%s</p>' % (
        T["sm"],
        T["ink2"],
        T["s1"],
        T["s2"],
        text,
    )


def card(inner: str, radius: int = 12, pad: str | None = None, extra: str = "") -> str:
    return (
        '<div style="background:%s;border:1px solid %s;border-radius:%dpx;padding:%s;%s">%s</div>'
        % (T["raised"], T["oliveSoft"], radius, pad or T["s2"], extra, inner)
    )


# ---------------------------------------------------------------------------
# Screen 1 — roster home with the calm check-in card
# ---------------------------------------------------------------------------


def home(lang: str) -> str:
    d = en if lang == "en" else hi
    checkin_card = (
        '<div style="background:%s;border:1px solid %s;border-radius:16px;padding:%s;'
        'display:flex;flex-direction:column;gap:%s">'
        '<p style="font-size:%s;font-weight:700;margin:0">%s</p>'
        '<p style="font-size:%s;color:%s;margin:0">%s</p>'
        '<div style="align-self:flex-start;background:%s;color:%s;min-height:48px;padding:0 %s;'
        'border-radius:8px;font-weight:600;font-size:%s;display:inline-flex;align-items:center;'
        'margin-top:%s">%s</div>'
        "</div>"
        % (
            T["raised"], T["oliveSoft"], T["s2"], T["s1"],
            T["md"], d["home.checkin.title"],
            T["xs"], T["ink2"], d["screen.disclaimer"],
            T["saffron"], T["raised"], T["s2"], T["sm"], T["s1"], d["home.checkin.open"],
        )
    )
    services = [
        ("home.card.roster", "clipboard", d["roster.nextDuty"].replace("{when}", "Tue 09 Sep · 06:00")),
        ("home.card.leave", "user", d["roster.leaveBalance"].replace("{n}", "12")),
        ("home.card.payslip", "clock", d["roster.payslip"].replace("{month}", "Aug 2026")),
        ("home.card.canteen", "heart", ""),
        ("home.card.grievance", "clipboard", ""),
        ("home.card.welfare", "heart", ""),
    ]
    tiles = "".join(
        '<div style="background:%s;border:1px solid %s;border-radius:12px;padding:%s;'
        'display:flex;flex-direction:column;gap:%s;min-height:96px">'
        '<span style="color:%s">%s</span>'
        '<p style="font-size:%s;font-weight:600;margin:0">%s</p>'
        '%s</div>'
        % (
            T["raised"], T["oliveSoft"], T["s2"], T["s1"], T["olive"], icon(ICONS[ic], 22),
            T["sm"], d[key],
            ('<p style="font-size:%s;color:%s;margin:0">%s</p>' % (T["xs"], T["ink2"], detail)) if detail else "",
        )
        for key, ic, detail in services
    )
    body = (
        title(d["nav.roster"])
        + '<div style="height:%s"></div>' % T["s2"]
        + checkin_card
        + '<h2 style="font-size:%s;font-weight:700;margin:%s 0 0">%s</h2>' % (T["md"], T["s3"], d["home.section.services"])
        + '<div style="display:grid;grid-template-columns:1fr 1fr;gap:%s;margin-top:%s">%s</div>' % (T["s2"], T["s2"], tiles)
        + '<p style="font-size:%s;color:%s;margin:%s 0 0">%s</p>' % (T["xs"], T["ink2"], T["s2"], d["roster.demoNote"])
    )
    return HEAD + shell(body, lang=lang, active="roster") + TAIL.format(script=STATIC_SCRIPT)


# ---------------------------------------------------------------------------
# Screen 2 — the 10-second check-in sheet (the hero)
# ---------------------------------------------------------------------------

EMOJI = ["\U0001F61E", "\U0001F615", "\U0001F610", "\U0001F642", "\U0001F604"]


def checkin(lang: str, *, tweakable: bool) -> str:
    d = en if lang == "en" else hi
    lh = T["lh"] if lang == "en" else T["lhhi"]

    def emoji_row(selected: int | None) -> str:
        cells = []
        for i, face in enumerate(EMOJI, start=1):
            on = selected == i
            cells.append(
                '<div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:%s;'
                'border:2px solid %s;border-radius:12px;padding:%s;min-height:64px;background:%s">'
                '<span style="font-size:24px;line-height:1">%s</span>'
                '<span style="font-size:%s;color:%s;text-align:center">%s</span></div>'
                % (
                    T["s1"],
                    T["olive"] if on else "transparent",
                    T["s1"],
                    T["oliveSoft"] if on else "transparent",
                    face,
                    T["xs"],
                    T["ink2"],
                    d["checkin.emoji.%d" % i],
                )
            )
        return (
            '<div style="display:flex;justify-content:space-between;gap:%s;margin-bottom:%s">%s</div>'
            % (T["s1"], T["s2"], "".join(cells))
        )

    def slider(value: int) -> str:
        pct = value * 10
        return (
            '<div style="margin-bottom:%s">'
            '<span style="display:block;font-size:%s;font-weight:700;margin-bottom:%s">%s</span>'
            '<div style="display:flex;align-items:center;gap:%s">'
            '<div style="flex:1;position:relative;height:48px;display:flex;align-items:center">'
            '<div style="height:4px;width:100%%;border-radius:999px;background:%s"></div>'
            '<div style="position:absolute;left:0;height:4px;width:%d%%;border-radius:999px;background:%s"></div>'
            '<div style="position:absolute;left:calc(%d%% - 10px);width:20px;height:20px;border-radius:50%%;background:%s"></div>'
            "</div>"
            '<span style="font-size:%s;font-weight:700;color:%s;min-width:36px;text-align:center;'
            'font-variant-numeric:tabular-nums">%d</span>'
            "</div></div>"
            % (
                T["s2"], T["xs"], T["s1"], d["checkin.slider.label"], T["s2"],
                T["oliveSoft"], pct, T["olive"], pct, T["olive"],
                T["md"], T["olive"], value,
            )
        )

    note_field = (
        '<div style="margin-bottom:%s">'
        '<span style="display:block;font-size:%s;font-weight:600;color:%s;margin-bottom:%s">%s</span>'
        '<div style="display:flex;gap:%s;align-items:stretch">'
        '<div style="flex:1;min-height:48px;padding:0 %s;background:%s;border:1px solid %s;'
        'border-radius:8px;display:flex;align-items:center;font-size:%s;color:%s">%s</div>'
        '<div style="width:48px;min-height:48px;border:1px solid %s;border-radius:8px;color:%s;'
        'display:flex;align-items:center;justify-content:center;background:%s">%s</div>'
        "</div>"
        '<p style="display:flex;align-items:center;gap:6px;font-size:%s;color:%s;margin:%s 0 0">%s%s</p>'
        "</div>"
        % (
            T["s2"], T["xs"], T["ink2"], T["s1"], d["checkin.optional.label"], T["s1"],
            T["s2"], T["raised"], T["oliveSoft"], T["sm"], T["ink2"], d["checkin.optional.placeholder"],
            T["oliveSoft"], T["olive"], T["raised"], icon(ICONS["mic"], 22),
            T["xs"], T["ink2"], T["s1"], icon(ICONS["lock"], 14), " " + d["voice.privacy.line"],
        )
    )

    consent_row = (
        '<div style="display:flex;align-items:center;gap:8px;font-size:%s;color:%s;'
        'margin:%s 0 %s;min-height:44px">'
        '<span style="width:20px;height:20px;border-radius:4px;background:%s;color:%s;'
        'display:inline-flex;align-items:center;justify-content:center;flex:none">%s</span>'
        "<span>%s</span></div>"
        % (
            T["xs"], T["ink2"], T["s2"], T["s1"],
            T["olive"], T["raised"], icon(ICONS["check"], 14, T["raised"]),
            d["consent.checkin.agree"],
        )
    )

    actions = (
        '<div style="display:flex;justify-content:flex-end;gap:%s;margin-top:%s">'
        '<div style="min-height:40px;padding:0 %s;color:%s;font-weight:600;font-size:%s;'
        'display:inline-flex;align-items:center">%s</div>'
        '<div style="min-height:48px;padding:0 %s;border-radius:8px;background:%s;color:%s;'
        'font-weight:600;font-size:%s;display:inline-flex;align-items:center">%s</div>'
        "</div>"
        % (
            T["s2"], T["s2"], T["s2"], T["olive"], T["sm"], d["common.cancel"],
            T["s2"], T["saffron"], T["raised"], T["sm"], d["checkin.submit"],
        )
    )

    error_line = (
        '<p style="font-size:%s;font-weight:600;color:%s;margin:0 0 %s">%s</p>'
        % (T["xs"], T["amber"], T["s1"], d["checkin.error.mood"])
    )

    def sheet(selected, value, show_error):
        return (
            '<div style="position:absolute;left:0;right:0;bottom:0;background:%s;'
            'border-radius:16px 16px 0 0;padding:%s;max-height:92%%;overflow:hidden">'
            '<h2 style="font-size:%s;font-weight:700;margin:0">%s</h2>'
            '<p style="font-size:%s;color:%s;margin:%s 0 %s">%s</p>'
            "%s%s%s%s%s%s"
            "</div>"
            % (
                T["raised"], T["s2"],
                T["md"], d["checkin.title"],
                T["xs"], T["ink2"], T["s1"], T["s2"], d["screen.disclaimer"],
                emoji_row(selected),
                error_line if show_error else "",
                slider(value),
                note_field,
                consent_row,
                actions,
            )
        )

    if not tweakable:
        overlay = sheet(4, 6, False)
        return HEAD + shell("", lang=lang, active="roster", dim=True, overlay=overlay) + TAIL.format(
            script=STATIC_SCRIPT
        )

    # The English hero carries one lever: the control's state, so the 9-state
    # rule (design.md §6) can be inspected without three more artboards.
    variants = {
        "idle": sheet(None, 5, False),
        "picked": sheet(4, 6, False),
        "error": sheet(None, 5, True),
    }
    body = (
        '<sc-if value="{{isIdle}}" hint-placeholder-val="{{ true }}">' + variants["idle"] + "</sc-if>"
        '<sc-if value="{{isPicked}}" hint-placeholder-val="{{ false }}">' + variants["picked"] + "</sc-if>"
        '<sc-if value="{{isError}}" hint-placeholder-val="{{ false }}">' + variants["error"] + "</sc-if>"
    )
    script = (
        "<script data-dc-script data-props='"
        + json.dumps(
            {
                "state": {
                    "editor": "enum",
                    "default": "picked",
                    "options": ["idle", "picked", "error"],
                    "section": "State",
                },
                "$preview": {"width": W, "height": H},
            },
            separators=(",", ":"),
        ).replace("'", "&#39;")
        + "'>\n"
        "class Component extends DCLogic {\n"
        "  renderVals() {\n"
        "    const s = this.props.state ?? 'picked';\n"
        "    return { isIdle: s === 'idle', isPicked: s === 'picked', isError: s === 'error' };\n"
        "  }\n"
        "}\n"
        "</script>"
    )
    return HEAD + shell("", lang=lang, active="roster", dim=True, overlay=body) + TAIL.format(script=script)


# ---------------------------------------------------------------------------
# Screen 3 — saved, with undo (undo beats confirm)
# ---------------------------------------------------------------------------


def saved(lang: str) -> str:
    d = en if lang == "en" else hi
    done_card = (
        '<div style="background:%s;border:1px solid %s;border-radius:16px;padding:%s;'
        'display:flex;flex-direction:column;gap:%s">'
        '<p style="font-size:%s;font-weight:700;margin:0">%s</p>'
        '<p style="font-size:%s;color:%s;margin:0">%s</p>'
        "</div>"
        % (
            T["raised"], T["oliveSoft"], T["s2"], T["s1"],
            T["md"], d["home.checkin.doneToday"],
            T["xs"], T["ink2"], d["checkin.thanks"],
        )
    )
    trend = (
        '<div style="margin-top:%s">%s</div>'
        % (
            T["s2"],
            card(
                '<p style="font-size:%s;font-weight:600;margin:0 0 %s">%s</p>'
                '<svg viewBox="0 0 320 72" width="100%%" height="72" role="img" aria-label="%s">'
                '<polyline points="4,52 44,48 84,56 124,40 164,44 204,30 244,34 284,24" fill="none" '
                'stroke="%s" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />'
                '<circle cx="284" cy="24" r="5" fill="%s" />'
                "</svg>"
                '<p style="font-size:%s;color:%s;margin:%s 0 0">%s</p>'
                % (
                    T["sm"], T["s1"], d["trend.title"], d["trend.axis.days"],
                    T["olive"], T["saffron"],
                    T["xs"], T["ink2"], T["s1"], d["trend.ownonly"],
                )
            ),
        )
    )
    undobar = (
        '<div style="position:absolute;left:%s;right:%s;bottom:76px;display:flex;align-items:center;'
        'gap:%s;padding:12px %s;border-radius:12px;background:%s;color:%s;font-size:%s;min-height:48px">'
        '<span style="flex:1">%s</span>'
        '<span style="min-height:44px;padding:0 %s;border:1px solid currentColor;border-radius:999px;'
        'font-size:%s;font-weight:700;display:inline-flex;align-items:center">%s</span>'
        "</div>"
        % (
            T["s2"], T["s2"], T["s2"], T["s2"], T["ink"], T["raised"], T["xs"],
            d["checkin.thanks"], T["s2"], T["xs"], d["checkin.undo"],
        )
    )
    body = title(d["nav.roster"]) + '<div style="height:%s"></div>' % T["s2"] + done_card + trend
    return HEAD + shell(body, lang=lang, active="roster", overlay=undobar) + TAIL.format(script=STATIC_SCRIPT)


# ---------------------------------------------------------------------------
# Screen 4 — consent panel
# ---------------------------------------------------------------------------

BUNDLES = [
    ("consent.scope.checkin", "consent.purpose.checkin", "mood · stress · sleep", 90, True, "12 Aug"),
    ("consent.scope.instrument", "consent.purpose.instrument", "PHQ-9 · GAD-7 · PSS-10", 90, True, "12 Aug"),
    ("consent.scope.voice", "consent.purpose.voice", "pace · pauses", 90, False, None),
    ("consent.scope.passive", "consent.purpose.passive", "sleep proxy", 90, True, "02 Sep"),
    ("consent.scope.pulse", "consent.purpose.pulse", "1–5 rating", 365, True, "02 Sep"),
    ("consent.scope.buddy", "consent.purpose.buddy", "one word", 365, False, None),
]


def consent(lang: str) -> str:
    d = en if lang == "en" else hi
    rows = []
    for label, purpose, cats, days, on, since in BUNDLES:
        state = (
            d["consent.granted"].replace("{when}", since) if on else d["consent.off"]
        )
        action = d["consent.withdraw.action"] if on else d["consent.grant.action"]
        rows.append(
            '<li style="background:%s;border:1px solid %s;border-radius:12px;padding:%s;'
            'display:flex;flex-direction:column;gap:%s">'
            '<div style="display:flex;align-items:flex-start;justify-content:space-between;gap:%s">'
            '<p style="font-weight:700;margin:0">%s</p>'
            '<span style="min-height:40px;padding:0 %s;border-radius:8px;background:%s;color:%s;'
            'font-size:%s;font-weight:600;display:inline-flex;align-items:center;flex:none">%s</span>'
            "</div>"
            '<p style="font-size:%s;color:%s;margin:0">%s</p>'
            '<dl style="display:grid;grid-template-columns:auto 1fr;gap:%s;margin:0;font-size:%s">'
            '<dt style="color:%s;font-weight:600">%s</dt><dd style="margin:0">%s</dd>'
            '<dt style="color:%s;font-weight:600">%s</dt><dd style="margin:0">%s</dd>'
            "</dl>"
            '<p style="font-size:%s;font-weight:600;color:%s;margin:0">%s</p>'
            "</li>"
            % (
                T["raised"], T["oliveSoft"], T["s2"], T["s1"], T["s2"],
                d[label],
                T["s2"], T["oliveSoft"] if on else T["olive"], T["ink"] if on else T["raised"],
                T["xs"], action,
                T["xs"], T["ink2"], d[purpose],
                T["s1"], T["xs"],
                T["ink2"], d["consent.data.label"], cats,
                T["ink2"], d["consent.retention.label"], d["consent.retention.days"].replace("{n}", str(days)),
                T["xs"], T["olive"] if on else T["ink2"], state,
            )
        )
    silent = (
        '<p style="padding:%s;border-left:4px solid %s;background:%s;border-radius:8px;'
        'margin:0 0 %s;font-size:%s">%s</p>'
        % (T["s2"], T["olive"], T["oliveSoft"], T["s2"], T["xs"], d["consent.withdraw.silent"])
    )
    body = (
        '<div style="display:inline-flex;align-items:center;gap:%s;min-height:48px;font-size:%s;'
        'font-weight:600;color:%s">%s<span>%s</span></div>'
        % (T["s1"], T["sm"], T["olive"], icon(ICONS["arrow"], 20), d["me.title"])
        + '<h1 style="font-size:%s;font-weight:700;margin:%s 0 0">%s</h1>' % (T["lg"], T["s1"], d["consent.sheet.title"])
        + lead(d["consent.subtitle"])
        + silent
        + '<ul style="list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:%s">%s</ul>'
        % (T["s1"], "".join(rows))
    )
    return HEAD + shell(body, lang=lang, active="me") + TAIL.format(script=STATIC_SCRIPT)


# ---------------------------------------------------------------------------
# Screen 5 — who viewed my data (the receipt, design.md §5)
# ---------------------------------------------------------------------------


def receipts(lang: str) -> str:
    d = en if lang == "en" else hi
    entries = [
        ("whoViewed.role.counsellor", "12 Sep 2026 · 09:14", None, "Red-tier outreach"),
        ("whoViewed.role.counsellor", "12 Sep 2026 · 09:12", "whoViewed.unmask.line", "red_outreach_24h"),
        ("whoViewed.role.welfare_officer", "12 Sep 2026 · 09:11", None, "Second key given"),
        ("whoViewed.role.counsellor", "04 Sep 2026 · 17:40", None, "Case review"),
    ]
    rows = []
    for role, when, line_key, why in entries:
        rows.append(
            '<li style="background:%s;border:1px solid %s;border-radius:12px;padding:%s;'
            'display:flex;flex-direction:column;gap:%s">'
            '<span style="align-self:flex-start;padding:%s %s;border-radius:999px;background:%s;'
            'color:%s;font-size:%s;font-weight:700">%s</span>'
            '<span style="font-size:%s;color:%s;font-variant-numeric:tabular-nums">%s</span>'
            "%s"
            '<span style="font-size:%s;color:%s">%s</span>'
            "</li>"
            % (
                T["raised"], T["oliveSoft"], T["s2"], T["s1"],
                T["s1"], "10px", T["oliveSoft"], T["olive"], T["xs"], d[role],
                T["xs"], T["ink2"], when,
                ('<span style="font-size:%s">%s</span>' % (T["sm"], d[line_key])) if line_key else "",
                T["xs"], T["ink2"], d["whoViewed.why"].replace("{why}", why),
            )
        )
    notice = (
        '<div style="display:flex;flex-direction:column;gap:%s;padding:%s;border:1px solid %s;'
        'border-radius:12px;background:%s;margin-bottom:%s">'
        '<span style="font-size:%s;color:%s;font-variant-numeric:tabular-nums">12 Sep 2026 · 09:12</span>'
        '<span style="font-size:%s">%s</span></div>'
        % (
            T["s1"], T["s2"], T["olive"], T["oliveSoft"], T["s2"],
            T["xs"], T["ink2"], T["sm"], d["whoViewed.breakglass.line"],
        )
    )
    body = (
        '<div style="display:inline-flex;align-items:center;gap:%s;min-height:48px;font-size:%s;'
        'font-weight:600;color:%s">%s<span>%s</span></div>'
        % (T["s1"], T["sm"], T["olive"], icon(ICONS["arrow"], 20), d["me.title"])
        + '<h1 style="font-size:%s;font-weight:700;margin:%s 0 0">%s</h1>' % (T["lg"], T["s1"], d["receipt.header"])
        + lead(d["whoViewed.title"])
        + notice
        + '<ul style="list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:%s">%s</ul>'
        % (T["s1"], "".join(rows))
        + '<p style="font-size:%s;color:%s;margin:%s 0 0">%s</p>'
        % (T["xs"], T["ink2"], T["s2"], d["whoViewed.footer"])
        + '<p style="font-size:%s;color:%s;margin:%s 0 0">%s</p>'
        % (T["xs"], T["ink2"], T["s1"], d["expiry.explain"])
    )
    return HEAD + shell(body, lang=lang, active="me") + TAIL.format(script=STATIC_SCRIPT)


# ---------------------------------------------------------------------------
# Spec sheet — the decisions a reviewer needs in order to argue with the design
# ---------------------------------------------------------------------------


def redlines() -> str:
    swatch = lambda name, value, role: (
        '<div style="display:flex;align-items:center;gap:%s">'
        '<span style="width:44px;height:44px;border-radius:8px;background:%s;border:1px solid %s;flex:none"></span>'
        '<div><p style="margin:0;font-weight:600;font-size:%s">%s</p>'
        '<p style="margin:0;font-size:%s;color:%s;font-variant-numeric:tabular-nums">%s · %s</p></div></div>'
        % (T["s2"], value, T["oliveSoft"], T["sm"], name, T["xs"], T["ink2"], value, role)
    )
    colors = "".join(
        swatch(n, v, r)
        for n, v, r in [
            ("surface/base", T["surface"], "warm paper, never white"),
            ("ink/primary", T["ink"], "body text"),
            ("brand/olive", T["olive"], "the uniform · primary"),
            ("brand/olive-soft", T["oliveSoft"], "selected, chips"),
            ("accent/saffron", T["saffron"], "one CTA per screen"),
            ("state/green", T["green"], "leaf · all good"),
            ("state/amber", T["amber"], "sun · a little care"),
            ("state/red", T["red"], "hand-heart · talk it out"),
        ]
    )
    ramp = "".join(
        '<p style="margin:0 0 %s;font-size:%s;line-height:1.2">%s <span style="font-size:%s;color:%s">%s</span></p>'
        % (T["s1"], size, label, T["xs"], T["ink2"], size)
        for label, size in [
            ("Screen title", T["lg"]),
            ("Section title", T["md"]),
            ("Body", T["sm"]),
            ("Detail", T["xs"]),
        ]
    )
    rules = [
        ("Welfare, not discipline", "No red violation stamps, no risk badge beside a person. Care states carry an icon and a word — colour is never the only signal."),
        ("Three taps, no network", "Emoji → slider → Save. The write lands in IndexedDB first; the network is never on the critical path."),
        ("Saffron is rare", "One primary call to action per screen. Everything else is olive or quiet."),
        ("Undo beats confirm", "Reversible actions get an undo bar. Only consent withdrawal and break-glass ask twice."),
        ("Spacing is 4 / 16 / 36", "No in-between values. What looks like a stray number is a border, a radius or a 48px touch target."),
        ("Labels stay visible", "Placeholders show format only. Every icon-only control carries a name for a screen reader."),
        ("The receipt is not a warning", "Who, when, why — olive role chips, tabular timestamps, zero alarm colour. Turning surveillance into accountability is the goal."),
        ("Hindi has room", "Line-height 1.6 against 1.5, and no fixed-height text container anywhere — matras clip otherwise."),
    ]
    rule_html = "".join(
        '<div style="display:flex;flex-direction:column;gap:%s"><p style="margin:0;font-weight:700;font-size:%s">%s</p>'
        '<p style="margin:0;font-size:%s;color:%s;max-width:60ch">%s</p></div>'
        % (T["s1"], T["sm"], head, T["sm"], T["ink2"], body)
        for head, body in rules
    )
    body = (
        '<div style="width:900px;min-height:1180px;background:%s;color:%s;font-family:%s;'
        'font-size:%s;line-height:%s;padding:%s">'
        '<h1 style="font-size:%s;font-weight:700;margin:0">Check-in and privacy panel — design notes</h1>'
        '<p style="font-size:%s;color:%s;margin:%s 0 %s;max-width:70ch">'
        "Every value on these artboards is lifted from the shipped token package and component styles, "
        "and every string from the app's own en/hi dictionary. Where a mockup and the running app disagree, "
        "the app is the bug — or this file is out of date.</p>"
        '<h2 style="font-size:%s;font-weight:700;margin:%s 0 %s">Colour</h2>'
        '<div style="display:grid;grid-template-columns:repeat(2, minmax(0, 1fr));gap:%s">%s</div>'
        '<h2 style="font-size:%s;font-weight:700;margin:%s 0 %s">Type</h2>'
        '<div style="display:flex;flex-direction:column;gap:%s">%s</div>'
        '<h2 style="font-size:%s;font-weight:700;margin:%s 0 %s">The rules these screens are testing</h2>'
        '<div style="display:flex;flex-direction:column;gap:%s">%s</div>'
        "</div>"
        % (
            T["surface"], T["ink"], FONT, T["sm"], T["lh"], T["s3"],
            T["xl"],
            T["sm"], T["ink2"], T["s2"], T["s3"],
            T["lg"], T["s3"], T["s2"], T["s2"], colors,
            T["lg"], T["s3"], T["s2"], T["s1"], ramp,
            T["lg"], T["s3"], T["s2"], T["s2"], rule_html,
        )
    )
    script = (
        "<script data-dc-script data-props='"
        + json.dumps({"$preview": {"width": 900, "height": 1180}}, separators=(",", ":"))
        + "'>\nclass Component extends DCLogic {}\n</script>"
    )
    return HEAD + body + TAIL.format(script=script)


# ---------------------------------------------------------------------------

FILES = {
    "Main.dc.html": lambda: checkin("en", tweakable=True),
    "Home.dc.html": lambda: home("en"),
    "Saved.dc.html": lambda: saved("en"),
    "HomeHi.dc.html": lambda: home("hi"),
    "CheckInHi.dc.html": lambda: checkin("hi", tweakable=False),
    "SavedHi.dc.html": lambda: saved("hi"),
    "Consent.dc.html": lambda: consent("en"),
    "Receipts.dc.html": lambda: receipts("en"),
    "ConsentHi.dc.html": lambda: consent("hi"),
    "ReceiptsHi.dc.html": lambda: receipts("hi"),
    "Redlines.dc.html": redlines,
}

GAP_X, GAP_Y = 110, 150
ROW1_Y, ROW2_Y = 0, H + GAP_Y


def col(i: int) -> int:
    return i * (W + GAP_X)


CANVAS = {
    "pages": [
        {"id": "page-1", "name": "Check-in flow"},
        {"id": "page-2", "name": "Privacy panel"},
        {"id": "page-3", "name": "Design notes"},
    ],
    "artboards": [
        {"file": "Home.dc.html", "x": col(0), "y": ROW1_Y, "w": W, "h": H, "page": "page-1", "title": "1 · Home (EN)"},
        {"file": "Main.dc.html", "x": col(1), "y": ROW1_Y, "w": W, "h": H, "page": "page-1", "title": "2 · Check-in sheet (EN)"},
        {"file": "Saved.dc.html", "x": col(2), "y": ROW1_Y, "w": W, "h": H, "page": "page-1", "title": "3 · Saved + undo (EN)"},
        {"file": "HomeHi.dc.html", "x": col(0), "y": ROW2_Y, "w": W, "h": H, "page": "page-1", "title": "1 · Home (HI)"},
        {"file": "CheckInHi.dc.html", "x": col(1), "y": ROW2_Y, "w": W, "h": H, "page": "page-1", "title": "2 · Check-in sheet (HI)"},
        {"file": "SavedHi.dc.html", "x": col(2), "y": ROW2_Y, "w": W, "h": H, "page": "page-1", "title": "3 · Saved + undo (HI)"},
        {"file": "Consent.dc.html", "x": col(0), "y": ROW1_Y, "w": W, "h": H, "page": "page-2", "title": "Consent panel (EN)"},
        {"file": "Receipts.dc.html", "x": col(1), "y": ROW1_Y, "w": W, "h": H, "page": "page-2", "title": "Who viewed my data (EN)"},
        {"file": "ConsentHi.dc.html", "x": col(0), "y": ROW2_Y, "w": W, "h": H, "page": "page-2", "title": "Consent panel (HI)"},
        {"file": "ReceiptsHi.dc.html", "x": col(1), "y": ROW2_Y, "w": W, "h": H, "page": "page-2", "title": "Who viewed my data (HI)"},
        {"file": "Redlines.dc.html", "x": 0, "y": 0, "w": 900, "h": 1180, "page": "page-3", "title": "Design notes"},
    ],
    "annotations": [
        {
            "id": "note-checkin",
            "x": 0,
            "y": -130,
            "w": 900,
            "page": "page-1",
            "text": "The 10-second check-in (F02 screen 2). Three taps: emoji, slider, Save.\n"
            "Top row English, bottom row Hindi — same layout, +0.1 line-height, no fixed-height text box.\n"
            "The sheet artboard has a State lever: idle / picked / error.",
        },
        {
            "id": "note-privacy",
            "x": 0,
            "y": -130,
            "w": 900,
            "page": "page-2",
            "text": "The privacy panel (F02 screens 5 and 6). Withdrawing is the same tap depth as granting,\n"
            "and the receipt is designed as a receipt, not a warning: who, when, why — no alarm colour.",
        },
    ],
    "launch": {"view": "canvas", "page": "page-1"},
}

OUT.mkdir(parents=True, exist_ok=True)
for name, make in FILES.items():
    (OUT / name).write_text(make(), encoding="utf-8")
(OUT / "canvas.json").write_text(json.dumps(CANVAS, indent=2) + "\n", encoding="utf-8")
print("wrote %d artboards + canvas.json to %s" % (len(FILES), OUT))
