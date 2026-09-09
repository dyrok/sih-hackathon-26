"use client";

import { useId } from "react";
import { useT } from "@saarthi/i18n";

export type CheckboxProps = {
  labelKey: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  id?: string;
  disabled?: boolean;
  hintKey?: string;
  errorKey?: string;
};

/** 20px box inside a 44px hit area (design.md §6 target rule). */
export function Checkbox({ labelKey, checked, onChange, id, disabled, hintKey, errorKey }: CheckboxProps) {
  const { t } = useT();
  const auto = useId();
  const inputId = id ?? auto;
  const hintId = hintKey ? `${inputId}-hint` : undefined;
  const errorId = errorKey ? `${inputId}-error` : undefined;
  const describedBy = [hintId, errorId].filter(Boolean).join(" ") || undefined;

  return (
    <div className="sa-checkbox">
      <label className="sa-checkbox__row" htmlFor={inputId}>
        <input
          id={inputId}
          className="sa-checkbox__input"
          type="checkbox"
          checked={checked}
          disabled={disabled}
          aria-describedby={describedBy}
          aria-invalid={errorKey ? true : undefined}
          onChange={(e) => onChange(e.target.checked)}
        />
        <span className="sa-checkbox__label">{t(labelKey)}</span>
      </label>
      {hintKey ? (
        <p className="sa-checkbox__hint" id={hintId}>
          {t(hintKey)}
        </p>
      ) : null}
      {errorKey ? (
        <p className="sa-checkbox__error" id={errorId} role="alert">
          {t(errorKey)}
        </p>
      ) : null}
    </div>
  );
}
