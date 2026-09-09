"use client";

import { useState } from "react";
import { useT } from "@saarthi/i18n";
import { Button, ConfirmDialog, ErrorState, Skeleton, Toast, useApi } from "@saarthi/ui";
import { getConsent, grantConsent, withdrawBundle } from "@saarthi/api/jawan";
import type { ConsentBundle, ConsentBundleId } from "@saarthi/api/jawan";
import { purgeQueueForTables } from "@saarthi/sync";
import { BUNDLE_CACHE_KEYS, BUNDLE_TABLES, CACHE, forgetCache } from "../../../lib/cache";
import { formatDay } from "../../../lib/format";
import { SubScreen } from "../../../components/SubScreen";

export default function ConsentPage() {
  const { t, locale } = useT();
  const { data, error, loading, reload } = useApi(getConsent, [], { cacheKey: CACHE.consent });

  const [confirming, setConfirming] = useState<ConsentBundleId | null>(null);
  const [busy, setBusy] = useState<ConsentBundleId | null>(null);
  const [withdrawn, setWithdrawn] = useState(false);
  const [failed, setFailed] = useState(false);

  const grant = async (bundle: ConsentBundle) => {
    setBusy(bundle.bundle_id);
    setFailed(false);
    try {
      await grantConsent({
        bundle_id: bundle.bundle_id,
        purpose_string: t(bundle.purpose_key),
        data_categories: bundle.data_categories,
        language: locale,
      });
      reload();
    } catch {
      setFailed(true);
    } finally {
      setBusy(null);
    }
  };

  const withdraw = async (id: ConsentBundleId) => {
    setConfirming(null);
    setBusy(id);
    setFailed(false);
    try {
      await withdrawBundle(id);
      // Withdrawal has to leave nothing behind on the device: anything captured
      // under this scope that is still queued is dropped, and the cached reads
      // that belong to it are forgotten (F02 definition of done).
      const tables = BUNDLE_TABLES[id];
      if (tables.length > 0) await purgeQueueForTables(tables);
      await forgetCache(BUNDLE_CACHE_KEYS[id]);
      setWithdrawn(true);
      reload();
    } catch {
      setFailed(true);
    } finally {
      setBusy(null);
    }
  };

  return (
    <SubScreen backHref="/me" titleKey="consent.sheet.title" leadKey="consent.subtitle">
      <p className="consent-silent">{t("consent.withdraw.silent")}</p>

      {loading && data === null ? <Skeleton lines={5} height="80px" /> : null}

      {data === null && error !== null ? (
        <ErrorState titleKey="error.network" bodyKey="sync.error.recovery" onRetry={reload} />
      ) : null}

      <ul className="consent-list">
        {(data?.bundles ?? []).map((bundle) => (
          <li className="consent-card" key={bundle.bundle_id}>
            <p className="consent-card__label">{t(bundle.label_key)}</p>
            <p className="consent-card__purpose">{t(bundle.purpose_key)}</p>

            <dl className="consent-card__facts">
              <dt>{t("consent.data.label")}</dt>
              <dd>{bundle.data_categories.join(", ")}</dd>
              <dt>{t("consent.retention.label")}</dt>
              <dd>{t("consent.retention.days", { n: bundle.retention_days })}</dd>
            </dl>

            <p className="consent-card__state">
              {bundle.granted && bundle.granted_at
                ? t("consent.granted", { when: formatDay(bundle.granted_at, locale) })
                : t("consent.off")}
            </p>

            {/* Granting and withdrawing are one tap from the same place — the
                asymmetry that makes withdrawal feel expensive is the thing
                design.md §6 and F02 screen 5 forbid. */}
            {bundle.granted ? (
              <Button
                variant="secondary"
                loading={busy === bundle.bundle_id}
                onClick={() => setConfirming(bundle.bundle_id)}
              >
                {t("consent.withdraw.action")}
              </Button>
            ) : (
              <Button
                variant="secondary"
                loading={busy === bundle.bundle_id}
                onClick={() => void grant(bundle)}
              >
                {t("consent.grant.action")}
              </Button>
            )}
          </li>
        ))}
      </ul>

      {failed ? (
        <p className="sheet__error" role="alert">
          {t("sync.error.recovery")}
        </p>
      ) : null}

      {confirming ? (
        <ConfirmDialog
          titleKey="consent.withdraw.action"
          bodyKey="consent.withdraw.confirm"
          confirmKey="consent.withdraw.action"
          cancelKey="common.cancel"
          tone="grave"
          onConfirm={() => void withdraw(confirming)}
          onCancel={() => setConfirming(null)}
        />
      ) : null}

      {withdrawn ? (
        <Toast messageKey="consent.withdrawn" timeoutMs={6000} onDismiss={() => setWithdrawn(false)} />
      ) : null}
    </SubScreen>
  );
}
