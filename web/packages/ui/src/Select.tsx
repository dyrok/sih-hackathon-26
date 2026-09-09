"use client";

import type { SelectHTMLAttributes } from "react";
import { useT } from "@saarthi/i18n";
import { useFieldContext } from "./Field";

export type SelectOption = { value: string; labelKey: string };

export type SelectProps = Omit<SelectHTMLAttributes<HTMLSelectElement>, "children"> & {
  options: SelectOption[];
  /** Rendered as a disabled first option so the empty state is explicit. */
  placeholderKey?: string;
};

/** Native select — option labels go through i18n, never literal text. */
export function Select({ className, options, placeholderKey, ...rest }: SelectProps) {
  const { t } = useT();
  const field = useFieldContext();
  return (
    <select
      {...rest}
      id={rest.id ?? field?.id}
      aria-describedby={rest["aria-describedby"] ?? field?.describedBy}
      aria-invalid={rest["aria-invalid"] ?? (field?.invalid ? true : undefined)}
      required={rest.required ?? field?.required}
      className={`sa-select${className ? ` ${className}` : ""}`}
    >
      {placeholderKey ? (
        <option value="" disabled>
          {t(placeholderKey)}
        </option>
      ) : null}
      {options.map((o) => (
        <option key={o.value} value={o.value}>
          {t(o.labelKey)}
        </option>
      ))}
    </select>
  );
}
