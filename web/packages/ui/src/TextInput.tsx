"use client";

import type { InputHTMLAttributes } from "react";
import { useFieldContext } from "./Field";

export type TextInputProps = InputHTMLAttributes<HTMLInputElement>;

/** Single-line input. 48px min height, visible focus ring, never `outline: none`. */
export function TextInput({ className, ...rest }: TextInputProps) {
  const field = useFieldContext();
  return (
    <input
      type="text"
      {...rest}
      id={rest.id ?? field?.id}
      aria-describedby={rest["aria-describedby"] ?? field?.describedBy}
      aria-invalid={rest["aria-invalid"] ?? (field?.invalid ? true : undefined)}
      required={rest.required ?? field?.required}
      className={`sa-input${className ? ` ${className}` : ""}`}
    />
  );
}
