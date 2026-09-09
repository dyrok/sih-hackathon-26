"use client";

import type { ReactNode } from "react";
import { useT } from "@saarthi/i18n";

export type FactorChipProps = {
  labelKey: string;
  value: ReactNode;
  /** 0–1 relative contribution. Drawn as a rule under the chip, never as a score. */
  weight?: number;
  vars?: Record<string, string | number>;
};

/**
 * One explainability chip: "47 duty days", "sleep −30%". The counsellor console
 * shows the top three of these instead of a single opaque number (design.md §4)
 * — a case is a story with reasons, not a rating.
 */
export function FactorChip({ labelKey, value, weight, vars }: FactorChipProps) {
  const { t } = useT();
  const pct = weight == null ? null : Math.round(Math.min(1, Math.max(0, weight)) * 100);
  return (
    <span className="sa-factor">
      <span className="sa-factor__text">
        <span className="sa-factor__label">{t(labelKey, vars)}</span>
        <span className="sa-factor__value">{value}</span>
      </span>
      {pct === null ? null : (
        <span className="sa-factor__weight" aria-hidden="true">
          <span className="sa-factor__weightfill" style={{ width: `${pct}%` }} />
        </span>
      )}
    </span>
  );
}
