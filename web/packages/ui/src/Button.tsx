"use client";

import type { ReactNode } from "react";

type Props = {
  children: ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  loading?: boolean;
  variant?: "primary" | "secondary" | "quiet";
  type?: "button" | "submit";
  className?: string;
  /** Dialogs focus their safe default (cancel) when they open. */
  autoFocus?: boolean;
  "aria-label"?: string;
};

export function Button({
  children,
  onClick,
  disabled,
  loading,
  variant = "primary",
  type = "button",
  className,
  autoFocus,
  "aria-label": ariaLabel,
}: Props) {
  return (
    <button
      type={type}
      className={`sa-btn sa-btn--${variant}${className ? ` ${className}` : ""}`}
      onClick={onClick}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      aria-label={ariaLabel}
      autoFocus={autoFocus}
    >
      {children}
    </button>
  );
}
