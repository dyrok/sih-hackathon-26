"use client";

import { useT } from "@saarthi/i18n";

export type SuppressedCellProps = {
  /** Defaults to the shared k-anonymity explainer. */
  reasonKey?: string;
  vars?: Record<string, string | number>;
};

/**
 * The k < 5 state, as one component, so every surface suppresses identically
 * (F08). It reads as a deliberate design choice, not as a failure: no error
 * colour, no warning icon, just the reason in plain words.
 */
export function SuppressedCell({ reasonKey = "common.suppressed", vars }: SuppressedCellProps) {
  const { t } = useT();
  return (
    <span className="sa-suppressed">
      <span className="sa-suppressed__dash" aria-hidden="true">
        —
      </span>
      <span className="sa-suppressed__reason">{t(reasonKey, vars)}</span>
    </span>
  );
}
