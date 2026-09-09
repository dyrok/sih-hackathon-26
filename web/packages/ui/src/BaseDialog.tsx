"use client";

import { useEffect, useId, useRef } from "react";
import type { ReactNode } from "react";
import { useT } from "@saarthi/i18n";
import { IconX } from "./Icons";

export type BaseDialogProps = {
  titleKey: string;
  subtitleKey?: string;
  onClose: () => void;
  children: ReactNode;
  footer?: ReactNode;
};

type Props = BaseDialogProps & { variant: "sheet" | "modal"; className?: string };

/**
 * Shared dialog primitive for Sheet (mobile, bottom-anchored) and Modal
 * (console, centred). Native <dialog> + showModal() buys focus trap, inert
 * background, Escape and focus restore without a single line of JS — the
 * accessibility floor in design.md §9 is not something to re-implement.
 */
export function BaseDialog({ titleKey, subtitleKey, onClose, children, footer, variant, className }: Props) {
  const { t } = useT();
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();

  useEffect(() => {
    const d = ref.current;
    if (d && !d.open) d.showModal();
  }, []);

  const close = () => {
    const d = ref.current;
    if (d && d.open) d.close();
    onClose();
  };

  return (
    <dialog
      ref={ref}
      className={`sa-dialog sa-dialog--${variant}${className ? ` ${className}` : ""}`}
      aria-labelledby={titleId}
      onCancel={(e) => {
        e.preventDefault();
        close();
      }}
      onMouseDown={(e) => {
        // The backdrop is the dialog element's own box; the inner wrapper
        // carries all the padding, so this only fires on a true outside click.
        if (e.target === e.currentTarget) close();
      }}
    >
      <div className="sa-dialog__inner">
        <div className="sa-dialog__head">
          <div className="sa-dialog__heading">
            <h2 className="sa-dialog__title" id={titleId}>
              {t(titleKey)}
            </h2>
            {subtitleKey ? <p className="sa-dialog__sub">{t(subtitleKey)}</p> : null}
          </div>
          <button type="button" className="sa-dialog__close" aria-label={t("a11y.close")} onClick={close}>
            <IconX width={20} height={20} />
          </button>
        </div>
        <div className="sa-dialog__body">{children}</div>
        {footer ? <div className="sa-dialog__footer">{footer}</div> : null}
      </div>
    </dialog>
  );
}
