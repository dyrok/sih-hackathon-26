"use client";

import { useEffect } from "react";
import { useT } from "@saarthi/i18n";
import { IconX } from "./Icons";

export type UndoBarProps = {
  messageKey: string;
  actionKey: string;
  onAction: () => void;
  onDismiss: () => void;
  timeoutMs: number;
  vars?: Record<string, string | number>;
};

/**
 * Undo beats confirm for anything reversible (design.md §6) — a check-in edit,
 * a buddy word, a tracker note. The user acts first and the system offers a way
 * back, instead of interrogating them before every tap.
 */
export function UndoBar({ messageKey, actionKey, onAction, onDismiss, timeoutMs, vars }: UndoBarProps) {
  const { t } = useT();

  useEffect(() => {
    const id = setTimeout(onDismiss, timeoutMs);
    return () => clearTimeout(id);
  }, [timeoutMs, onDismiss]);

  return (
    <div className="sa-undobar" role="status">
      <span className="sa-undobar__msg">{t(messageKey, vars)}</span>
      <button type="button" className="sa-undobar__action" onClick={onAction}>
        {t(actionKey)}
      </button>
      <button type="button" className="sa-undobar__close" aria-label={t("a11y.close")} onClick={onDismiss}>
        <IconX width={18} height={18} />
      </button>
    </div>
  );
}
