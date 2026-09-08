"use client";

import { useT } from "@saarthi/i18n";
import { IconHandHeart, IconLeaf, IconPhone, IconSun } from "./Icons";

export type CareState = "green" | "amber" | "red" | "critical";

const ICONS = {
  green: IconLeaf,
  amber: IconSun,
  red: IconHandHeart,
  critical: IconPhone,
} as const;

const LABEL_KEYS = {
  green: "care.chip.green",
  amber: "care.chip.amber",
  red: "care.chip.red",
  critical: "care.chip.critical",
} as const;

/**
 * Care-state chip (ADR-0004 welfare framing): leaf / sun / hand-heart / phone.
 * Never a red "risk" stamp — icon + text label, never color alone.
 */
export function CareStateChip({ state }: { state: CareState }) {
  const { t } = useT();
  const Icon = ICONS[state];
  return (
    <span className={`sa-chip sa-chip--${state}`}>
      <Icon width={16} height={16} />
      {t(LABEL_KEYS[state])}
    </span>
  );
}
