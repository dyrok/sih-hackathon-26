"use client";

import { useEffect } from "react";
import { useT } from "@saarthi/i18n";
import { IconX } from "./Icons";

export type ToastProps = {
  messageKey: string;
  vars?: Record<string, string | number>;
  onDismiss?: () => void;
  /** Auto-dismiss after this many ms. Omit to keep it until dismissed. */
  timeoutMs?: number;
};

/**
 * Quiet confirmation strip. `role="status"` (polite) — a saved check-in must
 * never interrupt a screen reader mid-sentence.
 */
export function Toast({ messageKey, vars, onDismiss, timeoutMs }: ToastProps) {
  const { t } = useT();

  useEffect(() => {
    if (!timeoutMs || !onDismiss) return;
    const id = setTimeout(onDismiss, timeoutMs);
    return () => clearTimeout(id);
  }, [timeoutMs, onDismiss]);

  return (
    <div className="sa-toast" role="status">
      <span className="sa-toast__msg">{t(messageKey, vars)}</span>
      {onDismiss ? (
        <button type="button" className="sa-toast__close" aria-label={t("a11y.close")} onClick={onDismiss}>
          <IconX width={18} height={18} />
        </button>
      ) : null}
    </div>
  );
}
