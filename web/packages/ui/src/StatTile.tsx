"use client";

import { useId } from "react";
import type { ReactNode } from "react";
import { useT } from "@saarthi/i18n";
import { SuppressedCell } from "./SuppressedCell";

export type StatTileProps = {
  labelKey: string;
  value: ReactNode;
  unitKey?: string;
  suppressed?: boolean;
  reasonKey?: string;
  hintKey?: string;
  vars?: Record<string, string | number>;
};

/**
 * One aggregate number with its label. When `suppressed` the tile shows the
 * explainer where the number would be — quietly, never styled as an error
 * (design.md §4: suppression is the design, not a failure).
 */
export function StatTile({ labelKey, value, unitKey, suppressed, reasonKey, hintKey, vars }: StatTileProps) {
  const { t } = useT();
  const labelId = useId();
  return (
    <div className="sa-stat">
      <p className="sa-stat__label" id={labelId}>
        {t(labelKey)}
      </p>
      {suppressed ? (
        <p className="sa-stat__suppressed">
          <SuppressedCell reasonKey={reasonKey} vars={vars} />
        </p>
      ) : (
        <p className="sa-stat__value" aria-describedby={labelId}>
          {value}
          {unitKey ? <span className="sa-stat__unit">{t(unitKey)}</span> : null}
        </p>
      )}
      {hintKey ? <p className="sa-stat__hint">{t(hintKey)}</p> : null}
    </div>
  );
}
