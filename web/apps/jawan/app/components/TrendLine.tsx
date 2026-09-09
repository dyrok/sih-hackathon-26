"use client";

/**
 * TrendLine — the personal 90-day check-in line.
 *
 * This component exists in apps/jawan and nowhere else (design-client-apps.md
 * §3, enforced by scripts/lint-boundaries.mjs). It draws the person's own
 * baseline and their own points. There is no peer series, no unit mean, no
 * ranking and no band — the only comparison offered is with yourself.
 *
 * Drawn by hand in SVG: no chart library ships to a 2 GB phone (ADR-0005).
 */

export type TrendPointView = {
  /** YYYY-MM-DD, local. */
  date: string;
  /** 0-10, higher is a lighter day (the check-in's own framing). */
  value: number;
};

type Props = {
  points: TrendPointView[];
  /** Last day of the window, YYYY-MM-DD. */
  today: string;
  /** Window length in days. */
  days: number;
  /** Days the engine recorded a follow-up on — ticks, never numbers. */
  markers?: string[];
  /** Screen-reader text. The SVG itself is decorative. */
  summary: string;
};

const W = 320;
const H = 132;
const PAD_X = 10;
const PAD_Y = 12;
const MAX_VALUE = 10;

const DAY_MS = 86_400_000;

function dayIndex(date: string, end: string, days: number): number {
  const a = new Date(`${date}T00:00:00`).getTime();
  const b = new Date(`${end}T00:00:00`).getTime();
  if (Number.isNaN(a) || Number.isNaN(b)) return days - 1;
  const back = Math.round((b - a) / DAY_MS);
  return Math.min(days - 1, Math.max(0, days - 1 - back));
}

export function TrendLine({ points, today, days, markers = [], summary }: Props) {
  const plotW = W - PAD_X * 2;
  const plotH = H - PAD_Y * 2;

  const x = (date: string) => PAD_X + (dayIndex(date, today, days) / Math.max(1, days - 1)) * plotW;
  const y = (value: number) => PAD_Y + (1 - Math.min(MAX_VALUE, Math.max(0, value)) / MAX_VALUE) * plotH;

  const ordered = [...points].sort((a, b) => a.date.localeCompare(b.date));
  const path = ordered
    .map((p, i) => `${i === 0 ? "M" : "L"}${x(p.date).toFixed(1)} ${y(p.value).toFixed(1)}`)
    .join(" ");

  const own = ordered.length > 0 ? ordered.reduce((acc, p) => acc + p.value, 0) / ordered.length : 0;
  const last = ordered[ordered.length - 1];

  return (
    <figure className="trendline">
      <svg
        className="trendline__svg"
        viewBox={`0 0 ${W} ${H}`}
        width="100%"
        height={H}
        role="presentation"
        aria-hidden="true"
        focusable="false"
      >
        {/* The person's own mean — the only baseline on this chart. */}
        {ordered.length > 1 ? (
          <line
            className="trendline__baseline"
            x1={PAD_X}
            x2={W - PAD_X}
            y1={y(own).toFixed(1)}
            y2={y(own).toFixed(1)}
          />
        ) : null}

        {path ? <path className="trendline__line" d={path} fill="none" /> : null}

        {ordered.map((p) => (
          <circle
            key={p.date}
            className={`trendline__dot${last && p.date === last.date ? " trendline__dot--today" : ""}`}
            cx={x(p.date).toFixed(1)}
            cy={y(p.value).toFixed(1)}
            r={last && p.date === last.date ? 5 : 3}
          />
        ))}

        {markers.map((date) => (
          <line
            key={`m-${date}`}
            className="trendline__marker"
            x1={x(date).toFixed(1)}
            x2={x(date).toFixed(1)}
            y1={H - PAD_Y}
            y2={H - 2}
          />
        ))}
      </svg>
      <figcaption className="sa-sr-only">{summary}</figcaption>
    </figure>
  );
}
