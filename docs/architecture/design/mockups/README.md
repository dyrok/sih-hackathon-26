# UX-002 — check-in and privacy panel mockups

> Owner: neel · Status: [x] complete · Last updated: 2026-09-09
> Spec: [design.md](../design.md) · [F02](../../../features/F02-jawan-app.md) screens 2, 5 and 6

Eleven artboards: the 10-second check-in flow and the privacy panel, each in
English and romanised Hindi, plus a page of design notes.

**Published canvas:** https://claude.ai/code/artifact/f1768503-c71e-41de-b298-8c974462d860

## What is source and what is output

| | |
|---|---|
| `*.dc.html` + `canvas.json` | the artboards. Source. Committed. |
| `saarthi-checkin-and-privacy.html` | the published canvas (~2 MB, carries its own editor). Build output, git-ignored. |

## How these stay true

The artboards are **generated from the app itself**, not drawn beside it:

- every colour, size, radius, control height and line-height is read from
  `web/packages/tokens/dist/tokens.css`, `web/packages/ui/src/ui.css` and
  `web/apps/jawan/app/globals.css` — no rounding, no 8px-grid snapping;
- every string is looked up by key in `web/packages/i18n/src/{en,hi}.json`, so a
  renamed key breaks the generator instead of silently ageing the mockup.

Where a mockup and the running app disagree, one of them is a bug — the mockup
cannot be "the old design" by accident.

## Regenerating

```bash
python3 scripts/build-mockups.py          # rewrite the artboards from tokens + i18n
```

Then re-seed and republish the canvas with the `/design` skill, passing every
artboard and `canvas.json`. The canvas keeps its URL when republished from the
same file path.

## Coverage

| Page | Artboards |
|---|---|
| Check-in flow | Home → check-in sheet → saved-with-undo, EN and HI |
| Privacy panel | consent panel and who-viewed-my-data receipts, EN and HI |
| Design notes | palette, type ramp, and the eight rules these screens exist to test |

The check-in sheet artboard carries a **State** lever — idle / picked / error —
so the 9-state rule (design.md §6) can be inspected without three more frames.
