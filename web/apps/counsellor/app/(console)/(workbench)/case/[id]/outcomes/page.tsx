"use client";

import { useState } from "react";
import { useT } from "@saarthi/i18n";
import { Button, Segmented, Skeleton, useApi } from "@saarthi/ui";
import { getCatalogue, recordOutcome } from "@saarthi/api/counsellor";
import { useCase } from "../../../../../components/CaseContext";
import { LoadError } from "../../../../../components/LoadError";

/**
 * F06 screen 5. The outcome is the label that makes ML v2 possible (ADR-0001),
 * and the screen says so out loud — because the same record could be misread as
 * an appraisal note, and it never is one.
 */
export default function CaseOutcomePage() {
  const { t } = useT();
  const { caseId, reload } = useCase();
  const catalogue = useApi(() => getCatalogue(), [], { cacheKey: "cons.catalogue" });

  const [outcome, setOutcome] = useState("");
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState(false);
  const [errorKey, setErrorKey] = useState<string | null>(null);

  const codes = catalogue.data?.outcome_codes ?? [];
  const options = codes.map((code) => ({ value: code, labelKey: `cons.outcome.${code}` }));

  const submit = async () => {
    if (!outcome || busy) return;
    setBusy(true);
    setErrorKey(null);
    try {
      await recordOutcome(caseId, outcome);
      setSaved(true);
      reload();
    } catch {
      setErrorKey("cons.outcome.saveError");
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="cons-card" aria-labelledby="cons-outcome-heading">
      <h2 className="cons-card__title" id="cons-outcome-heading">
        {t("cons.outcome.title")}
      </h2>
      <p className="cons-card__note">{t("cons.outcome.explain")}</p>

      {catalogue.loading && codes.length === 0 ? (
        <Skeleton lines={2} height="24px" />
      ) : codes.length === 0 ? (
        <LoadError error={catalogue.error} onRetry={catalogue.reload} />
      ) : (
        <>
          <Segmented
            name="cons-outcome"
            options={options}
            value={outcome}
            ariaLabelKey="cons.outcome.title"
            disabled={busy}
            onChange={(v) => {
              setOutcome(v);
              setSaved(false);
            }}
          />
          <div className="cons-inline">
            <Button onClick={submit} loading={busy} disabled={!outcome}>
              {t("common.save")}
            </Button>
          </div>
        </>
      )}

      {saved ? (
        <p className="cons-callout" role="status">
          {t("cons.outcome.saved")}
        </p>
      ) : null}
      {errorKey ? (
        <p className="cons-card__note" role="alert">
          {t(errorKey)}
        </p>
      ) : null}
    </section>
  );
}
