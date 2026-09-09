"use client";

import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { useT } from "@saarthi/i18n";
import {
  Button,
  EmptyState,
  IconGrid,
  Skeleton,
  Slider,
  SuppressedCell,
  apiErrorStatus,
  useApi,
} from "@saarthi/ui";
import { getLevers, runSimulation } from "@saarthi/api/commander";
import type { Lever, SimulationResult } from "@saarthi/api/commander";
import { useUnits } from "../units";
import { AssumptionPanel, DataNotice, RuleDeltaList, ScreenHead, sharePct } from "../parts";

/**
 * F07 screen 4 / APP-010 — the what-if simulator.
 *
 * The form is built from `getLevers()`: nothing about a lever is hardcoded
 * here, so when the engine's validated ranges move, this screen moves with them
 * instead of quietly projecting nonsense. A 400 means a lever left its range;
 * the server's message is surfaced word for word and the input is never clamped
 * behind the operator's back. A failed or suppressed run changes nothing else
 * on the screen, and nothing here ever touches a live score.
 */
export default function SimulatorPage() {
  const { t } = useT();
  const { unitId, loading: unitsLoading, error: unitsError, reload: reloadUnits } = useUnits();

  const levers = useApi<{ levers: Record<string, Lever> }>(getLevers, [], {
    cacheKey: "commander.levers",
  });

  const [scenario, setScenario] = useState<Record<string, number>>({});
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [runError, setRunError] = useState<Error | null>(null);
  const [busy, setBusy] = useState(false);

  const specs = levers.data?.levers;

  useEffect(() => {
    if (!specs) return;
    setScenario(Object.fromEntries(Object.entries(specs).map(([name, s]) => [name, s.default])));
  }, [specs]);

  const run = async () => {
    if (busy || !unitId) return;
    setBusy(true);
    setRunError(null);
    try {
      setResult(await runSimulation(unitId, scenario));
    } catch (err) {
      // Keep the previous projection exactly as it is. A run that failed has
      // not changed anything, and pretending otherwise would be a lie.
      setRunError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setBusy(false);
    }
  };

  const submit = (e: FormEvent) => {
    e.preventDefault();
    void run();
  };

  const reset = () => {
    if (specs) {
      setScenario(Object.fromEntries(Object.entries(specs).map(([name, s]) => [name, s.default])));
    }
    setResult(null);
    setRunError(null);
  };

  if (!unitId && !unitsLoading) {
    return (
      <div className="cmd-screen">
        <ScreenHead titleKey="sim.title" guideKey="sim.intro" />
        <DataNotice error={unitsError} onRetry={reloadUnits} />
        <EmptyState icon={IconGrid} titleKey="units.none" />
      </div>
    );
  }

  const outOfRange = runError !== null && apiErrorStatus(runError) === 400;
  const projection = result && !result.suppressed ? result.projection : undefined;

  return (
    <div className="cmd-screen">
      <ScreenHead
        titleKey="sim.title"
        guideKey="sim.intro"
        aside={unitId ? <span className="cmd-unitid">{unitId}</span> : null}
      />
      <DataNotice error={levers.error ?? unitsError} onRetry={() => levers.reload()} />

      <div className="cmd-cols cmd-cols--two">
        <section className="cmd-panel">
          {!specs ? (
            levers.loading ? (
              <Skeleton lines={4} />
            ) : null
          ) : (
            <form className="cmd-form" onSubmit={submit}>
              {Object.entries(specs).map(([name, spec]) => (
                <Slider
                  key={name}
                  labelKey={spec.explain_key}
                  value={scenario[name] ?? spec.default}
                  min={spec.min}
                  max={spec.max}
                  step={1}
                  disabled={busy}
                  onChange={(v) => setScenario((s) => ({ ...s, [name]: v }))}
                />
              ))}
              <div className="cmd-actions">
                <Button variant="quiet" onClick={reset} disabled={busy}>
                  {t("sim.reset")}
                </Button>
                <Button type="submit" loading={busy}>
                  {t("sim.run")}
                </Button>
              </div>
            </form>
          )}
          <p className="cmd-note">{t("sim.notMl")}</p>
        </section>

        <section className="cmd-panel">
          {outOfRange ? (
            <p className="cmd-outofrange" role="alert">
              {t("sim.outOfRange", { message: runError.message })}
            </p>
          ) : null}
          {runError && !outOfRange ? (
            <DataNotice error={runError} onRetry={() => void run()} />
          ) : null}

          {result === null ? (
            <p className="cmd-note">{t("common.empty")}</p>
          ) : result.suppressed ? (
            <p className="cmd-note">
              <SuppressedCell
                reasonKey={result.reason_key ?? undefined}
                vars={{ k: result.k }}
              />
            </p>
          ) : projection ? (
            <>
              <h2 className="cmd-headline">
                {t("sim.result", {
                  delta: projection.fatigue_index_delta,
                  pct:
                    projection.fatigue_index_delta_pct === null
                      ? "—"
                      : projection.fatigue_index_delta_pct,
                })}
              </h2>
              <p className="cmd-subline">
                {t("sim.result.elevated", {
                  before: `${sharePct(projection.elevated_share_before, 1)}%`,
                  after: `${sharePct(projection.elevated_share_after, 1)}%`,
                })}
              </p>
            </>
          ) : null}

          {result && !result.suppressed ? (
            <RuleDeltaList rows={result.rule_deltas ?? []} titleKey="sim.rules" />
          ) : null}
          {/* Open by default: the assumptions are what make the projection
              defensible, so they sit next to the number rather than behind a
              click a reader can decline to make. */}
          {result ? <AssumptionPanel snapshot={result.assumption_snapshot} defaultOpen /> : null}
        </section>
      </div>
    </div>
  );
}
