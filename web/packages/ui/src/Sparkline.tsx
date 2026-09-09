"use client";

import { useT } from "@saarthi/i18n";

export type SparklineProps = {
  points: number[];
  max: number;
  ariaLabelKey: string;
  min?: number;
  width?: number;
  height?: number;
};

/**
 * A small generic SVG line, drawn by hand — no chart library ships to a 2 GB
 * phone (ADR-0005). This is NOT the personal trend: TrendLine (own 90-day
 * baseline, dot-fill animation) lives in apps/jawan and only there.
 * The SVG is decorative; the numbers are read out from the text summary.
 */
export function Sparkline({ points, max, ariaLabelKey, min = 0, width = 160, height = 40 }: SparklineProps) {
  const { t } = useT();

  if (points.length === 0) {
    return <p className="sa-sparkline__empty">{t("common.empty")}</p>;
  }

  const span = Math.max(1e-6, max - min);
  const step = points.length > 1 ? width / (points.length - 1) : 0;
  const clamp = (n: number) => Math.min(1, Math.max(0, (n - min) / span));
  const d = points
    .map((p, i) => `${i === 0 ? "M" : "L"}${(i * step).toFixed(1)} ${((1 - clamp(p)) * height).toFixed(1)}`)
    .join(" ");
  const summary = `${t(ariaLabelKey)}: ${points.join(", ")}`;

  return (
    <span className="sa-sparkline">
      <svg
        className="sa-sparkline__svg"
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="none"
        aria-hidden="true"
        focusable="false"
      >
        <path className="sa-sparkline__line" d={d} fill="none" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      <span className="sa-sr-only">{summary}</span>
    </span>
  );
}
