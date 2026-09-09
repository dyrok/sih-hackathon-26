"use client";

import type { TextareaHTMLAttributes } from "react";
import { useFieldContext } from "./Field";

export type TextAreaProps = TextareaHTMLAttributes<HTMLTextAreaElement>;

/** Multi-line input. Grows to its rows; never a fixed-height box (Devanagari matras clip). */
export function TextArea({ className, rows = 4, ...rest }: TextAreaProps) {
  const field = useFieldContext();
  return (
    <textarea
      rows={rows}
      {...rest}
      id={rest.id ?? field?.id}
      aria-describedby={rest["aria-describedby"] ?? field?.describedBy}
      aria-invalid={rest["aria-invalid"] ?? (field?.invalid ? true : undefined)}
      required={rest.required ?? field?.required}
      className={`sa-input sa-textarea${className ? ` ${className}` : ""}`}
    />
  );
}
