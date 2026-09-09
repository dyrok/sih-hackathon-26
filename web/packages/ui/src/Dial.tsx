"use client";

import { useId } from "react";
import { useT } from "@saarthi/i18n";
import { SuppressedCell } from "./SuppressedCell";

export type DialProps = {
  /** 0–100, or null when there is no number to show. */
  value: number | null;
  labelKey: string;
  suppressed?: boolean;
  reasonKey?: string;
  vars?: Record<string, string | number>;
};

/**
 * 0–100 arc gauge, hand-drawn SVG. The number is always present as text as well
 * as as an arc — an operator at 200% zoom, or a screen-reader user, must get the
 * same reading as someone looking at the sweep.
 */
export function Dial({ value, labelKey, suppressed, reasonKey, vars }: DialProps) {
  const { t } = useT();
  const labelId = useId();
  const hidden = suppressed || value === null;
  const shown = hidden ? 0 : Math.min(100, Math.max(0, value));

  return (
    <div className="sa-dial">
      <svg className="sa-dial__svg" viewBox="0 0 100 58" width={120} height={70} aria-hidden="true" focusable="false">
        <path className="sa-dial__track" d="M8 50 A 42 42 0 0 1 92 50" fill="none" strokeWidth={8} strokeLinecap="round" />
        {hidden ? null : (
          <path
            className="sa-dial__fill"
            d="M8 50 A 42 42 0 0 1 92 50"
            fill="none"
            strokeWidth={8}
            strokeLinecap="round"
            pathLength={100}
            strokeDasharray="100"
            strokeDashoffset={100 - shown}
          />
        )}
      </svg>
      {hidden ? (
        <p className="sa-dial__suppressed">
          <SuppressedCell reasonKey={reasonKey} vars={vars} />
        </p>
      ) : (
        <p
          className="sa-dial__value"
          role="meter"
          aria-labelledby={labelId}
          aria-valuenow={shown}
          aria-valuemin={0}
          aria-valuemax={100}
        >
          {shown}
        </p>
      )}
      <p className="sa-dial__label" id={labelId}>
        {t(labelKey)}
      </p>
    </div>
  );
}
