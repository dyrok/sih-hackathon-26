"use client";

import { useState } from "react";
import Link from "next/link";
import { useT } from "@saarthi/i18n";
import {
  Button,
  ConfirmDialog,
  EmptyState,
  ErrorState,
  Field,
  IconUsers,
  Segmented,
  Skeleton,
  TextInput,
  useApi,
} from "@saarthi/ui";
import { getBuddy, getConsent, pairBuddy, setBuddyState, unpairBuddy } from "@saarthi/api/jawan";
import type { BuddyStateName } from "@saarthi/api/jawan";
import { CACHE } from "../../../lib/cache";
import { SubScreen } from "../../../components/SubScreen";

const STATE_OPTIONS = [
  { value: "ok", labelKey: "buddy.state.ok" },
  { value: "quiet", labelKey: "buddy.state.quiet" },
  { value: "sos", labelKey: "buddy.state.sos" },
];

export default function BuddyPage() {
  const { t } = useT();
  const consent = useApi(getConsent, [], { cacheKey: CACHE.consent });
  const buddy = useApi(getBuddy, [], { cacheKey: CACHE.buddy });

  const [code, setCode] = useState("");
  const [pairError, setPairError] = useState(false);
  const [busy, setBusy] = useState(false);
  const [confirmUnpair, setConfirmUnpair] = useState(false);
  const [stateError, setStateError] = useState(false);

  const granted = consent.data?.bundles.find((b) => b.bundle_id === "buddy")?.granted ?? null;
  const data = buddy.data;
  const buddyState = data?.buddy?.state ?? null;

  const pair = async () => {
    if (busy || code.trim().length === 0) return;
    setBusy(true);
    setPairError(false);
    try {
      await pairBuddy(code.trim());
      setCode("");
      buddy.reload();
    } catch {
      setPairError(true);
    } finally {
      setBusy(false);
    }
  };

  const changeState = async (next: BuddyStateName) => {
    setStateError(false);
    try {
      await setBuddyState(next);
      buddy.reload();
    } catch {
      setStateError(true);
    }
  };

  const unpair = async () => {
    setConfirmUnpair(false);
    try {
      await unpairBuddy();
      buddy.reload();
    } catch {
      setStateError(true);
    }
  };

  if (granted === false) {
    return (
      <SubScreen backHref="/welfare" titleKey="buddy.title" leadKey="buddy.intro">
        <p className="screen-lead">{t("buddy.needConsent")}</p>
        <Link className="hub-row" href="/me/consent">
          <span className="hub-row__text">
            <span className="hub-row__label">{t("me.consent")}</span>
            <span className="hub-row__detail">{t("consent.turnOn")}</span>
          </span>
        </Link>
      </SubScreen>
    );
  }

  return (
    <SubScreen backHref="/welfare" titleKey="buddy.title" leadKey="buddy.intro">
      {buddy.loading && data === null ? <Skeleton lines={4} height="56px" /> : null}

      {data === null && buddy.error !== null ? (
        <ErrorState titleKey="error.network" bodyKey="sync.error.recovery" onRetry={buddy.reload} />
      ) : null}

      {buddyState === "sos" ? (
        <section className="buddy-sos" role="status">
          <p className="buddy-sos__line">{t("buddy.sos.banner")}</p>
          <a className="buddy-sos__call" href="tel:14416">
            {t("buddy.sos.helpline")}
          </a>
          <p className="buddy-sos__jco">{t("buddy.sos.jco")}</p>
        </section>
      ) : null}

      {data?.paired ? (
        <>
          <div className="buddy-word">
            <p className="buddy-word__label">{t("buddy.theirState")}</p>
            <p className="buddy-word__value">{t(`buddy.state.${buddyState ?? "ok"}`)}</p>
          </div>

          <p className="buddy-word__label">{t("buddy.myState")}</p>
          <Segmented
            name="buddy-state"
            options={STATE_OPTIONS}
            value={data.my_state}
            ariaLabelKey="buddy.myState"
            onChange={(value) => void changeState(value as BuddyStateName)}
          />

          <Button variant="quiet" onClick={() => setConfirmUnpair(true)}>
            {t("buddy.unpair")}
          </Button>
        </>
      ) : null}

      {data !== null && !data.paired ? (
        <>
          <EmptyState icon={IconUsers} titleKey="buddy.empty" bodyKey="buddy.intro" />
          <Field
            labelKey="buddy.code.label"
            htmlFor="buddy-code"
            errorKey={pairError ? "buddy.pairError" : undefined}
          >
            <TextInput
              id="buddy-code"
              value={code}
              placeholder={t("buddy.code.placeholder")}
              autoComplete="off"
              onChange={(e) => setCode(e.target.value)}
            />
          </Field>
          <Button onClick={() => void pair()} loading={busy} disabled={code.trim().length === 0}>
            {t("buddy.pair")}
          </Button>
        </>
      ) : null}

      {stateError ? (
        <p className="sheet__error" role="alert">
          {t("sync.error.recovery")}
        </p>
      ) : null}

      <p className="footnote">{t("buddy.private")}</p>

      {confirmUnpair ? (
        <ConfirmDialog
          titleKey="buddy.unpair"
          bodyKey="buddy.unpairConfirm"
          confirmKey="buddy.unpair"
          cancelKey="common.cancel"
          tone="grave"
          onConfirm={() => void unpair()}
          onCancel={() => setConfirmUnpair(false)}
        />
      ) : null}
    </SubScreen>
  );
}
