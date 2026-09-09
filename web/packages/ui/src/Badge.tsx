"use client";

import { useT } from "@saarthi/i18n";

export type BadgeProps = {
  labelKey: string;
  vars?: Record<string, string | number>;
  /** "attention" is a quiet olive outline, not an alarm. There is no red tone. */
  tone?: "neutral" | "attention";
};

/**
 * Small factual label — an overdue marker, a cap notice, a source tag.
 * Deliberately has no alarm variant: a badge next to a person is exactly the
 * pattern ADR-0003 forbids, so this one only ever states a fact.
 */
export function Badge({ labelKey, vars, tone = "neutral" }: BadgeProps) {
  const { t } = useT();
  return <span className={`sa-badge sa-badge--${tone}`}>{t(labelKey, vars)}</span>;
}
