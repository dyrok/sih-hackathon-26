"use client";

import { useT } from "@saarthi/i18n";
import type { TrendMarker, TrendPoint } from "@saarthi/api/counsellor";
import { formatDate } from "./format";

export type RiskTrendChartProps = {
  points: TrendPoint[];
  markers: TrendMarker[];
};

/* viewBox units. The SVG scales to its container, so these are ratios, not px. */
const W = 640;
const H = 200;
const PAD = { left: 32, right: 12, top: 12, bottom: 28 };
const PLOT_W = W - PAD.left - PAD.right;
const PLOT_H = H - PAD.top - PAD.bottom;
const Y_TICKS = [0, 50, 100];

function ms(value: string): number {
  const t = Date.parse(value);
  return Number.isNaN(t) ? 0 : t;
}

/**
 * Case risk history with the intervention markers on the same axis (F06 screen
 * 2 / TC-304), so "did the thing we did help" is a question the picture answers.
 *
 * Drawn by hand — no chart library ships to this console (ADR-0006), and a
 * hand-drawn axis is the only way to keep the score band, the care-state colours
 * and the markers on one honest scale.
 *
 * This is a *case* chart on a fixed 0–100 axis. It is not the personal 90-day
 * component from the jawan app: that one belongs to the person, renders their
 * own baseline, and by rule exists in no console.
 */
export function RiskTrendChart({ points, markers }: RiskTrendChartProps) {
  const { t, locale } = useT();

  if (points.length === 0) return <p className="cons-card__note">{t("cons.trend.empty")}</p>;

  const times = points.map((p) => ms(p.as_of));
  const first = times[0] ?? 0;
  const last = times[times.length - 1] ?? first;
  const span = Math.max(1, last - first);

  const x = (at: number) =>
    points.length === 1 ? PAD.left + PLOT_W / 2 : PAD.left + ((at - first) / span) * PLOT_W;
  const y = (score: number) => PAD.top + (1 - Math.min(100, Math.max(0, score)) / 100) * PLOT_H;

  const path = points
    .map((p, i) => `${i === 0 ? "M" : "L"}${x(ms(p.as_of)).toFixed(1)} ${y(p.score).toFixed(1)}`)
    .join(" ");

  // Only markers inside the plotted window can be drawn honestly on the axis,
  // but every marker is still listed underneath — an intervention that happened
  // after the last score must not become invisible.
  const inRange = markers.filter((m) => {
    const at = ms(m.at);
    return at >= first && at <= last;
  });

  const latest = points[points.length - 1];
  const summary = t("cons.trend.summary", {
    n: points.length,
    from: formatDate(points[0]?.as_of ?? "", locale),
    to: formatDate(latest?.as_of ?? "", locale),
    latest: latest?.score ?? 0,
  });

  return (
    <figure className="cons-trend">
      <div className="cons-trend__scroll">
        <svg
          className="cons-trend__svg"
          viewBox={`0 0 ${W} ${H}`}
          preserveAspectRatio="xMidYMid meet"
          role="img"
          aria-label={summary}
        >
          {Y_TICKS.map((v) => (
            <g key={v}>
              <line
                className="cons-trend__axis"
                x1={PAD.left}
                x2={W - PAD.right}
                y1={y(v)}
                y2={y(v)}
              />
              <text className="cons-trend__tick" x={0} y={y(v) + 4}>
                {String(v)}
              </text>
            </g>
          ))}

          {inRange.map((m, i) => (
            <line
              key={`${m.at}-${m.kind}-${i}`}
              className="cons-trend__marker"
              x1={x(ms(m.at))}
              x2={x(ms(m.at))}
              y1={PAD.top}
              y2={PAD.top + PLOT_H}
            />
          ))}

          <path className="cons-trend__line" d={path} />

          {points.map((p, i) => (
            <circle
              key={`${p.as_of}-${i}`}
              className={`cons-trend__dot cons-trend__dot--${p.tier}`}
              cx={x(ms(p.as_of))}
              cy={y(p.score)}
              r={4}
            />
          ))}

          <text className="cons-trend__tick" x={PAD.left} y={H - 8}>
            {formatDate(points[0]?.as_of ?? "", locale)}
          </text>
          <text className="cons-trend__tick" x={W - PAD.right} y={H - 8} textAnchor="end">
            {formatDate(latest?.as_of ?? "", locale)}
          </text>
        </svg>
      </div>

      <figcaption className="cons-trend__caption">{t("cons.trend.legend")}</figcaption>

      {markers.length > 0 ? (
        <ul className="cons-trend__markers">
          {markers.map((m, i) => (
            <li key={`legend-${m.at}-${i}`}>
              {t("cons.trend.markerAt", {
                when: formatDate(m.at, locale),
                label: `${t(m.label_key)} · ${m.detail}`,
              })}
            </li>
          ))}
        </ul>
      ) : null}

      <ul className="sa-sr-only">
        {points.map((p, i) => (
          <li key={`sr-${p.as_of}-${i}`}>
            {t("cons.trend.point", {
              when: formatDate(p.as_of, locale),
              score: p.score,
              tier: t(`care.chip.${p.tier}`),
            })}
          </li>
        ))}
      </ul>
    </figure>
  );
}
