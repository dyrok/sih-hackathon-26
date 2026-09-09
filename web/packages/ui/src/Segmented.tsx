"use client";

import { useT } from "@saarthi/i18n";

export type SegmentedOption = { value: string; labelKey: string };

export type SegmentedProps = {
  name: string;
  options: SegmentedOption[];
  value: string;
  onChange: (value: string) => void;
  ariaLabelKey: string;
  disabled?: boolean;
};

/**
 * A radio group drawn as chips. Real <input type="radio"> under the hood, so
 * arrow-key walking, form semantics and screen-reader announcement come from
 * the platform rather than from a pile of ARIA (design.md §9).
 */
export function Segmented({ name, options, value, onChange, ariaLabelKey, disabled }: SegmentedProps) {
  const { t } = useT();
  return (
    <div className="sa-segmented" role="radiogroup" aria-label={t(ariaLabelKey)}>
      {options.map((o) => {
        const selected = o.value === value;
        return (
          <label
            key={o.value}
            className={`sa-segmented__opt${selected ? " sa-segmented__opt--selected" : ""}`}
          >
            <input
              className="sa-segmented__input"
              type="radio"
              name={name}
              value={o.value}
              checked={selected}
              disabled={disabled}
              onChange={() => onChange(o.value)}
            />
            <span className="sa-segmented__label">{t(o.labelKey)}</span>
          </label>
        );
      })}
    </div>
  );
}
