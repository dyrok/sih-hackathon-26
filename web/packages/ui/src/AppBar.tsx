"use client";

import type { ReactNode } from "react";
import { useT } from "@saarthi/i18n";

export type AppBarProps = {
  /** Defaults to the product name. */
  titleKey?: string;
  /** Right-hand slot — SyncPill, language toggle, a back action. */
  right?: ReactNode;
};

/** Jawan app top bar: brand on the left, one slot on the right. Nothing else. */
export function AppBar({ titleKey = "login.title", right }: AppBarProps) {
  const { t } = useT();
  return (
    <header className="sa-appbar">
      <p className="sa-appbar__brand">{t(titleKey)}</p>
      {right ? <div className="sa-appbar__right">{right}</div> : null}
    </header>
  );
}
