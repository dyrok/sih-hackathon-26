"use client";

import { useState } from "react";
import Link from "next/link";
import { useT } from "@saarthi/i18n";
import { Button, CareStateChip, EmptyState, IconPhoneCall, Segmented, Skeleton, useApi } from "@saarthi/ui";
import { getQueue, telemanasHandoff } from "@saarthi/api/counsellor";
import { LoadError } from "../../components/LoadError";
import { useRole } from "../../components/session";

const MODES = [
  { value: "facilitated_call", labelKey: "cons.telemanas.mode.facilitated_call" },
  { value: "self_referral", labelKey: "cons.telemanas.mode.self_referral" },
];

/**
 * F06 screen 6. A referral, not an export: the handoff writes one row into the
 * case timeline (14416 is the channel) and no clinical content crosses over.
 */
export default function TelemanasPage() {
  const { t } = useT();
  const role = useRole();
  const queue = useApi(() => getQueue(), [], { cacheKey: "cons.queue" });

  const [caseId, setCaseId] = useState("");
  const [mode, setMode] = useState("facilitated_call");
  const [busy, setBusy] = useState(false);
  const [doneFor, setDoneFor] = useState<string | null>(null);
  const [errorKey, setErrorKey] = useState<string | null>(null);

  const rows = queue.data?.queue ?? [];
  const canWrite = role === "counsellor";

  const submit = async () => {
    if (!caseId || busy) return;
    setBusy(true);
    setErrorKey(null);
    try {
      await telemanasHandoff(caseId, mode);
      setDoneFor(caseId);
    } catch {
      setErrorKey("cons.error.generic");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="cons-detail">
      <div className="cons-head">
        <h1 className="cons-title">{t("cons.telemanas.title")}</h1>
        <p className="cons-guide">{t("cons.telemanas.explain")}</p>
        <p className="cons-meta">{t("settings.helpline")}</p>
      </div>

      <section className="cons-card" aria-labelledby="cons-tm-heading">
        <h2 className="cons-card__title" id="cons-tm-heading">
          {t("cons.telemanas.record")}
        </h2>

        {!canWrite && role !== null ? <p className="cons-card__note">{t("cons.telemanas.readOnly")}</p> : null}

        {queue.loading && rows.length === 0 ? (
          <Skeleton lines={3} height="48px" />
        ) : !queue.data ? (
          <LoadError error={queue.error} onRetry={queue.reload} />
        ) : rows.length === 0 ? (
          <EmptyState icon={IconPhoneCall} titleKey="cons.telemanas.noCases" bodyKey="queue.empty.audit" />
        ) : (
          <>
            <fieldset className="cons-picker">
              <legend className="cons-picker__legend">{t("cons.telemanas.case")}</legend>
              <ul className="cons-picker__list">
                {rows.map((row) => (
                  <li key={row.case_id}>
                    <label className="cons-picker__opt">
                      <input
                        className="cons-picker__input"
                        type="radio"
                        name="cons-tm-case"
                        value={row.case_id}
                        checked={caseId === row.case_id}
                        disabled={busy || !canWrite}
                        onChange={() => {
                          setCaseId(row.case_id);
                          setDoneFor(null);
                        }}
                      />
                      <span className="cons-picker__label">
                        <span>{row.pseudonym_id ?? row.case_id}</span>
                        <CareStateChip state={row.tier} />
                      </span>
                    </label>
                  </li>
                ))}
              </ul>
            </fieldset>

            <div className="cons-stack cons-stack--tight">
              <span className="sa-field__label">{t("cons.telemanas.mode")}</span>
              <Segmented
                name="cons-tm-mode"
                options={MODES}
                value={mode}
                ariaLabelKey="cons.telemanas.mode"
                disabled={busy || !canWrite}
                onChange={setMode}
              />
            </div>

            <div className="cons-inline">
              <Button onClick={submit} loading={busy} disabled={!caseId || !canWrite}>
                {t("cons.telemanas.record")}
              </Button>
            </div>
          </>
        )}

        {doneFor ? (
          <p className="cons-callout" role="status">
            {t("cons.telemanas.recorded")}{" "}
            <Link className="cons-back" href={`/case/${doneFor}`}>
              {t("cons.telemanas.openCase")}
            </Link>
          </p>
        ) : null}
        {errorKey ? (
          <p className="cons-card__note" role="alert">
            {t(errorKey)}
          </p>
        ) : null}
      </section>
    </div>
  );
}
