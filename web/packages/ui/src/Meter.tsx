"use client";

import { useId } from "react";
import type { ReactNode } from "react";
import { useT } from "@saarthi/i18n";

export type MeterProps = {
  labelKey: string;
  value: number;
  min?: number;
  max?: number;
  /** Text shown next to the bar; defaults to the raw value. */
  valueText?: ReactNode;
  hintKey?: string;
  vars?: Record<string, string | number>;
};

/**
 * Horizontal proportion bar with a real `role="meter"`. Olive fill only — a
 * proportion is not a severity, so this never changes colour with its value.
 */
export function Meter({ labelKey, value, min = 0, max = 100, valueText, hintKey, vars }: MeterProps) {
  const { t } = useT();
  const labelId = useId();
  const span = Math.max(1e-6, max - min);
  const pct = Math.round(Math.min(1, Math.max(0, (value - min) / span)) * 100);

  return (
    <div className="sa-meter">
      <div className="sa-meter__head">
        <span className="sa-meter__label" id={labelId}>
          {t(labelKey, vars)}
        </span>
        <span className="sa-meter__value">{valueText ?? value}</span>
      </div>
      <div
        className="sa-meter__track"
        role="meter"
        aria-labelledby={labelId}
        aria-valuenow={value}
        aria-valuemin={min}
        aria-valuemax={max}
      >
        <div className="sa-meter__fill" style={{ width: `${pct}%` }} />
      </div>
      {hintKey ? <p className="sa-meter__hint">{t(hintKey)}</p> : null}
    </div>
  );
}
