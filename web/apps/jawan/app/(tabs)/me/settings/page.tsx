"use client";

import { useCallback, useEffect, useState, useSyncExternalStore } from "react";
import { useRouter } from "next/navigation";
import { useT } from "@saarthi/i18n";
import { Button, ConfirmDialog, LanguageToggle, Toast } from "@saarthi/ui";
import { clearSession } from "@saarthi/api";
import { allQueued, clearAll, getSyncSnapshot, subscribeSync } from "@saarthi/sync";
import type { QueueItem } from "@saarthi/sync";
import { formatDateTime } from "../../../lib/format";
import { stopSyncEngine } from "../../../lib/sync";
import { SubScreen } from "../../../components/SubScreen";

export default function SettingsPage() {
  const { t, locale } = useT();
  const router = useRouter();
  const snapshot = useSyncExternalStore(subscribeSync, getSyncSnapshot, getSyncSnapshot);

  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [confirmClear, setConfirmClear] = useState(false);
  const [cleared, setCleared] = useState(false);

  const refresh = useCallback(() => {
    void allQueued()
      .then(setQueue)
      .catch(() => setQueue([]));
  }, []);

  useEffect(refresh, [refresh, snapshot.queued, snapshot.lastSyncedAt]);

  // An item the server refused stays in the queue with its reason attached.
  // Showing it is the honest thing: silently retrying forever, or silently
  // dropping it, both leave the person believing something was sent.
  const rejected = queue.filter((item) => item.conflict);

  const clearLocal = async () => {
    setConfirmClear(false);
    await clearAll();
    refresh();
    setCleared(true);
  };

  const signOut = () => {
    stopSyncEngine();
    clearSession();
    router.replace("/login");
  };

  return (
    <SubScreen backHref="/me" titleKey="settings.title">
      <section className="settings-block">
        <h2 className="settings-block__title">{t("settings.language")}</h2>
        <LanguageToggle />
      </section>

      <section className="settings-block">
        <h2 className="settings-block__title">{t("settings.syncStatus")}</h2>
        <p className="settings-line">
          {snapshot.queued > 0
            ? t("sync.pill.queued", { n: snapshot.queued })
            : snapshot.state === "offline"
              ? t("sync.pill.offline")
              : t("sync.pill.synced")}
        </p>
        {snapshot.lastSyncedAt ? (
          <p className="settings-line settings-line--quiet">
            {t("settings.lastSynced", { when: formatDateTime(snapshot.lastSyncedAt, locale) })}
          </p>
        ) : null}
        {snapshot.conflicts > 0 ? (
          <p className="settings-line settings-line--quiet">
            {t("settings.conflicts", { n: snapshot.conflicts })}
          </p>
        ) : null}
        {rejected.length > 0 ? (
          <>
            <p className="settings-line settings-line--quiet">
              {t("settings.rejected", { n: rejected.length })}
            </p>
            <ul className="settings-rejects">
              {rejected.map((item) => (
                <li key={item.client_uuid}>{item.conflict}</li>
              ))}
            </ul>
          </>
        ) : null}
        {snapshot.state === "error" ? (
          <p className="settings-line settings-line--quiet">{t("sync.error.recovery")}</p>
        ) : null}
      </section>

      <section className="settings-block">
        <h2 className="settings-block__title">{t("settings.about")}</h2>
        <p className="settings-line">{t("app.tagline")}</p>
        <a className="settings-helpline" href="tel:14416">
          {t("settings.helpline")}
        </a>
      </section>

      <section className="settings-block">
        <Button variant="secondary" onClick={() => setConfirmClear(true)}>
          {t("settings.clearLocal")}
        </Button>
        <Button variant="quiet" onClick={signOut}>
          {t("nav.signOut")}
        </Button>
      </section>

      {confirmClear ? (
        <ConfirmDialog
          titleKey="settings.clearLocal"
          bodyKey="settings.clearLocal.confirm"
          confirmKey="settings.clearLocal"
          cancelKey="common.cancel"
          tone="grave"
          onConfirm={() => void clearLocal()}
          onCancel={() => setConfirmClear(false)}
        />
      ) : null}

      {cleared ? (
        <Toast messageKey="settings.cleared" timeoutMs={5000} onDismiss={() => setCleared(false)} />
      ) : null}
    </SubScreen>
  );
}
