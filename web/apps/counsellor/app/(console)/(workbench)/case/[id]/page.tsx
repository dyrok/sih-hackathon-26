"use client";

import { useState } from "react";
import { useT } from "@saarthi/i18n";
import {
  Button,
  FactorChip,
  Meter,
  Skeleton,
  Timeline,
  Toast,
  useApi,
  apiErrorStatus,
} from "@saarthi/ui";
import type { TimelineEvent as RailEvent, TimelineKind } from "@saarthi/ui";
import { addAction, getCatalogue, getRiskTrend, getTimeline } from "@saarthi/api/counsellor";
import type { CaseDetail } from "@saarthi/api/counsellor";
import { useCase } from "../../../../components/CaseContext";
import { LoadError } from "../../../../components/LoadError";
import { RiskTrendChart } from "../../../../components/RiskTrendChart";
import { formatDateTime } from "../../../../components/format";

const KIND_MAP: Record<string, TimelineKind> = {
  case_opened: "care",
  action: "action",
  outcome: "outcome",
  telemanas: "action",
  note: "info",
  unmask: "access",
  break_glass: "access",
};

function str(value: unknown): string {
  if (value === null || value === undefined) return "";
  return typeof value === "string" ? value : String(value);
}

/** The score history plus the interventions, on one axis (TC-304). */
function CaseTrend({ pseudonymId }: { pseudonymId: string }) {
  const { t } = useT();
  const { data, error, loading, reload } = useApi(() => getRiskTrend(pseudonymId), [pseudonymId]);

  if (loading && !data) return <Skeleton lines={4} height="24px" />;
  // "No history yet" arrives as a 404 from the API; that is an empty state, not
  // a failure the counsellor has to act on.
  if (!data) {
    return apiErrorStatus(error) === 404 ? (
      <p className="cons-card__note">{t("cons.trend.empty")}</p>
    ) : (
      <LoadError error={error} onRetry={reload} />
    );
  }
  return <RiskTrendChart points={data.points} markers={data.markers} />;
}

function CaseTimeline({ caseId, version }: { caseId: string; version: number }) {
  const { t } = useT();
  const { data, error, loading, reload } = useApi(() => getTimeline(caseId), [caseId, version]);

  if (loading && !data) return <Skeleton lines={4} height="20px" />;
  if (!data) return <LoadError error={error} onRetry={reload} />;

  const events: RailEvent[] = data.events.map((e) => {
    const vars: Record<string, string | number> = {};
    if (e.kind === "case_opened") vars["tier"] = t(`care.chip.${str(e.detail["tier"])}`);
    if (e.kind === "action") vars["detail"] = t(`cons.action.${str(e.detail["catalogue_id"])}`);
    if (e.kind === "outcome") vars["detail"] = t(`cons.outcome.${str(e.detail["outcome"])}`);
    if (e.kind === "telemanas") vars["detail"] = str(e.detail["mode"]);
    if (e.kind === "unmask") vars["detail"] = t(`cons.unmask.status.${str(e.detail["status"])}`);
    return { at: e.at, key: e.key, vars, kind: KIND_MAP[e.kind] ?? "info" };
  });

  return <Timeline events={events} emptyKey="common.empty" />;
}

function EvidenceCard({ detail, locale }: { detail: CaseDetail; locale: string }) {
  const { t } = useT();
  const score = detail.score;

  return (
    <section className="cons-card" aria-labelledby="cons-evidence-heading">
      <h2 className="cons-card__title" id="cons-evidence-heading">
        {t("cons.case.evidence")}
      </h2>

      {score === null ? (
        <p className="cons-card__note">{t("cons.case.noScore")}</p>
      ) : (
        <>
          <Meter
            labelKey="cons.case.score"
            value={score.score}
            min={0}
            max={100}
            hintKey="cons.case.scoreHint"
          />
          <div className="cons-dl">
            <p>{t("cons.case.confidence", { value: t(`cons.confidence.${score.confidence}`) })}</p>
            <p>
              {t("cons.case.sources", {
                value: score.sources_present.map((s) => t(`cons.source.${s}`)).join(", "),
              })}
            </p>
            <p>
              {t("cons.case.engine", {
                engine: score.engine_version,
                ruleset: score.ruleset_version,
              })}
            </p>
            <p>{t("cons.case.scoreAsOf", { when: formatDateTime(score.as_of, locale) })}</p>
          </div>
          {score.hysteresis_held ? (
            <p className="cons-card__note">{t("cons.case.hysteresis")}</p>
          ) : null}
        </>
      )}

      {detail.masking ? (
        <div className="cons-callout">
          <p className="cons-callout__title">{t("cons.case.masking")}</p>
          <p className="cons-callout__body">{t("cons.case.maskingWhy")}</p>
        </div>
      ) : null}

      <p className="cons-card__note">{t("screen.disclaimer")}</p>
    </section>
  );
}

export default function CaseEvidencePage() {
  const { t, locale } = useT();
  const { caseId, detail, reload } = useCase();
  const catalogue = useApi(() => getCatalogue(), [], { cacheKey: "cons.catalogue" });
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [toastKey, setToastKey] = useState<string | null>(null);
  const [timelineVersion, setTimelineVersion] = useState(0);

  if (!detail) return null;

  const ladder = catalogue.data?.ladder[detail.tier];
  const actions = ladder?.catalogue ?? detail.ladder.catalogue ?? [];

  const runAction = async (catalogueId: string) => {
    if (busyAction) return;
    setBusyAction(catalogueId);
    setToastKey(null);
    try {
      await addAction(caseId, catalogueId);
      setToastKey("cons.action.recorded");
      setTimelineVersion((v) => v + 1);
      reload();
    } catch {
      setToastKey("cons.error.generic");
    } finally {
      setBusyAction(null);
    }
  };

  return (
    <>
      <EvidenceCard detail={detail} locale={locale} />

      <section className="cons-card" aria-labelledby="cons-factors-heading">
        <h2 className="cons-card__title" id="cons-factors-heading">
          {t("cons.case.factors")}
        </h2>
        {detail.factors.length === 0 ? (
          <p className="cons-card__note">{t("cons.case.factorsNone")}</p>
        ) : (
          <div className="cons-factors">
            {detail.factors.map((f) => (
              <FactorChip
                key={`${f.rule_id}-${f.display_key}`}
                labelKey={f.display_key}
                value={f.display_value ?? f.observed_value ?? ""}
                weight={f.weight}
              />
            ))}
          </div>
        )}
      </section>

      <section className="cons-card" aria-labelledby="cons-trend-heading">
        <h2 className="cons-card__title" id="cons-trend-heading">
          {t("cons.case.trend")}
        </h2>
        {detail.pseudonym_id ? (
          <CaseTrend pseudonymId={detail.pseudonym_id} />
        ) : (
          <p className="cons-card__note">{t("cons.trend.empty")}</p>
        )}
      </section>

      <section className="cons-card" aria-labelledby="cons-actions-heading">
        <h2 className="cons-card__title" id="cons-actions-heading">
          {t("cons.actions.title")}
        </h2>
        <p className="cons-card__note">{t("cons.actions.hint")}</p>
        {actions.length === 0 ? (
          <p className="cons-card__note">{t("cons.actions.none")}</p>
        ) : (
          <div className="cons-inline">
            {actions.map((id, i) => (
              <Button
                key={id}
                variant={i === 0 ? "primary" : "secondary"}
                loading={busyAction === id}
                disabled={busyAction !== null && busyAction !== id}
                onClick={() => runAction(id)}
              >
                {t(`cons.action.${id}`)}
              </Button>
            ))}
          </div>
        )}
        {toastKey ? <Toast messageKey={toastKey} onDismiss={() => setToastKey(null)} timeoutMs={6000} /> : null}
      </section>

      <section className="cons-card" aria-labelledby="cons-timeline-heading">
        <h2 className="cons-card__title" id="cons-timeline-heading">
          {t("cons.case.timeline")}
        </h2>
        <CaseTimeline caseId={caseId} version={timelineVersion} />
      </section>
    </>
  );
}
