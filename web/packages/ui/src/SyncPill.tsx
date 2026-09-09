"use client";

import { useSyncExternalStore } from "react";
import { getSyncSnapshot, subscribeSync } from "@saarthi/sync";
import { useT } from "@saarthi/i18n";

/**
 * Quiet sync indicator (ADR-0005): queued data is never error-styled.
 * Only a genuine sync failure shows the recovery line — blame-free.
 */
export function SyncPill() {
  const { t } = useT();
  const snap = useSyncExternalStore(subscribeSync, getSyncSnapshot);

  if (snap.state === "error") {
    return <span className="sa-syncpill sa-syncpill--error">{t("sync.error.recovery")}</span>;
  }
  if (snap.state === "syncing") {
    return <span className="sa-syncpill sa-syncpill--idle">{t("sync.pill.syncing")}</span>;
  }
  if (snap.queued > 0) {
    return <span className="sa-syncpill sa-syncpill--idle">{t("sync.pill.queued", { n: snap.queued })}</span>;
  }
  return <span className="sa-syncpill sa-syncpill--idle">{t("sync.pill.synced")}</span>;
}
