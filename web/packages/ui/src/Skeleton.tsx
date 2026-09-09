"use client";

import { useT } from "@saarthi/i18n";

export type SkeletonProps = {
  lines?: number;
  /** CSS length for each line, e.g. "16px". Defaults to a body line. */
  height?: string;
};

/**
 * Loading placeholder. Shimmer-free by default (ADR-0005: low-end Android runs
 * reduced motion), so this is a quiet block, not an animation budget.
 */
export function Skeleton({ lines = 3, height }: SkeletonProps) {
  const { t } = useT();
  const rows = Array.from({ length: Math.max(1, lines) }, (_, i) => i);
  return (
    <div className="sa-skeleton" aria-busy="true" role="status">
      <span className="sa-sr-only">{t("common.loading")}</span>
      {rows.map((i) => (
        <span
          key={i}
          className="sa-skeleton__line"
          aria-hidden="true"
          style={height ? { height } : undefined}
        />
      ))}
    </div>
  );
}
