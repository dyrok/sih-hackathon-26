"use client";

import { BaseDialog } from "./BaseDialog";
import { Button } from "./Button";
import { useT } from "@saarthi/i18n";

export type ConfirmDialogProps = {
  titleKey: string;
  bodyKey: string;
  confirmKey: string;
  cancelKey: string;
  /** "grave" is reserved for consent withdrawal and break-glass unmask. */
  tone?: "default" | "grave";
  onConfirm: () => void;
  onCancel: () => void;
};

/**
 * The ONLY confirm pattern in the product. Everything reversible uses UndoBar
 * instead (design.md §6); this exists for the two irreversible actions —
 * consent withdrawal and break-glass unmask. Cancel takes focus on open and
 * stays first in the tab order.
 */
export function ConfirmDialog({
  titleKey,
  bodyKey,
  confirmKey,
  cancelKey,
  tone = "default",
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  const { t } = useT();
  return (
    <BaseDialog
      titleKey={titleKey}
      onClose={onCancel}
      className={`sa-confirm sa-confirm--${tone}`}
      variant="modal"
      footer={
        <>
          <Button variant="quiet" onClick={onCancel} autoFocus>
            {t(cancelKey)}
          </Button>
          <Button variant={tone === "grave" ? "secondary" : "primary"} onClick={onConfirm}>
            {t(confirmKey)}
          </Button>
        </>
      }
    >
      <p className="sa-confirm__body">{t(bodyKey)}</p>
    </BaseDialog>
  );
}
