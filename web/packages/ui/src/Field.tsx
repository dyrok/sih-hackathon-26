"use client";

import { createContext, useContext } from "react";
import type { ReactNode } from "react";
import { useT } from "@saarthi/i18n";

type FieldContextValue = {
  id: string;
  describedBy?: string;
  invalid: boolean;
  required: boolean;
};

const FieldContext = createContext<FieldContextValue | null>(null);

/** Controls read their id / aria wiring from the Field that wraps them. */
export function useFieldContext(): FieldContextValue | null {
  return useContext(FieldContext);
}

export type FieldProps = {
  labelKey: string;
  htmlFor: string;
  hintKey?: string;
  errorKey?: string;
  required?: boolean;
  children: ReactNode;
};

/**
 * Label + control wrapper. The label is ALWAYS visible (design.md §6) —
 * placeholders only ever carry a format example, never the label itself,
 * because a placeholder disappears exactly when a low-literacy user needs it.
 */
export function Field({ labelKey, htmlFor, hintKey, errorKey, required, children }: FieldProps) {
  const { t } = useT();
  const hintId = hintKey ? `${htmlFor}-hint` : undefined;
  const errorId = errorKey ? `${htmlFor}-error` : undefined;
  const describedBy = [hintId, errorId].filter(Boolean).join(" ") || undefined;

  return (
    <div className={`sa-field${errorKey ? " sa-field--invalid" : ""}`}>
      <label className="sa-field__label" htmlFor={htmlFor}>
        {t(labelKey)}
        {required ? (
          <span className="sa-field__req" aria-hidden="true">
            *
          </span>
        ) : null}
      </label>
      {hintKey ? (
        <p className="sa-field__hint" id={hintId}>
          {t(hintKey)}
        </p>
      ) : null}
      <FieldContext.Provider
        value={{ id: htmlFor, describedBy, invalid: Boolean(errorKey), required: Boolean(required) }}
      >
        {children}
      </FieldContext.Provider>
      {errorKey ? (
        <p className="sa-field__error" id={errorId} role="alert">
          {t(errorKey)}
        </p>
      ) : null}
    </div>
  );
}
