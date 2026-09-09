"use client";

import { useId } from "react";
import { useT } from "@saarthi/i18n";

export type SliderProps = {
  labelKey: string;
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
  id?: string;
  disabled?: boolean;
  /** Optional key rendered after the number, e.g. a unit. */
  unitKey?: string;
};

/**
 * Labelled range with the number shown in text as well as position — a slider
 * whose value only exists as a thumb position is unreadable at 200% zoom and
 * silent to a screen reader.
 */
export function Slider({
  labelKey,
  value,
  onChange,
  min = 0,
  max = 10,
  step = 1,
  id,
  disabled,
  unitKey,
}: SliderProps) {
  const { t } = useT();
  const auto = useId();
  const inputId = id ?? auto;
  return (
    <div className="sa-slider">
      <label className="sa-slider__label" htmlFor={inputId}>
        {t(labelKey)}
      </label>
      <div className="sa-slider__row">
        <input
          id={inputId}
          className="sa-slider__input"
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          disabled={disabled}
          onChange={(e) => onChange(Number(e.target.value))}
        />
        <output className="sa-slider__value" htmlFor={inputId}>
          {value}
          {unitKey ? <span className="sa-slider__unit">{t(unitKey)}</span> : null}
        </output>
      </div>
    </div>
  );
}
