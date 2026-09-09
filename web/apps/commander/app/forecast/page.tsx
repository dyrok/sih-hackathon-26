"use client";

import { useState } from "react";
import { useT } from "@saarthi/i18n";
import { EmptyState, IconGrid, Skeleton, Sparkline, SuppressedCell, useApi } from "@saarthi/ui";
import { getForecast } from "@saarthi/api/commander";
import type { Forecast } from "@saarthi/api/commander";
import { useUnits } from "../units";
import { AssumptionPanel, DataNotice, RuleDeltaList, ScreenHead } from "../parts";

/** Backend accepts 1–26 weeks; these are the planning horizons worth a click. */
const HORIZONS = [4, 8, 12, 26];

/**
 * F07 screen 5 — attrition pressure over a chosen horizon.
 *
 * The disclaimer is the screen's guidance line rather than a footnote: this is a
 * rotation-planning input, and a forward line that reads as a verdict on people
 * is exactly the misuse ADR-0003 exists to prevent. The line itself is a plain
 * SVG of the unit index — deliberately not the personal 90-day trend component,
 * which belongs to the jawan app alone.
 */
export default function ForecastPage() {
  const { t } = useT();
  const { unitId, loading: unitsLoading, error: unitsError, reload: reloadUnits } = useUnits();
  const [horizon, setHorizon] = useState(8);

  const forecast = useApi<Forecast | null>(
    () => (unitId ? getForecast(unitId, horizon) : Promise.resolve(null)),
    [unitId, horizon],
    { cacheKey: unitId ? `commander.forecast.${unitId}.${horizon}` : undefined },
  );

  const reload = () => {
    reloadUnits();
    forecast.reload();
  };

  if (!unitId && !unitsLoading) {
    return (
      <div className="cmd-screen">
        <ScreenHead titleKey="forecast.title" guideKey="forecast.disclaimer" />
        <DataNotice error={unitsError} onRetry={reload} />
        <EmptyState icon={IconGrid} titleKey="units.none" />
      </div>
    );
  }

  const f = forecast.data;
  const points = f?.points ?? [];
  const values = points.map((p) => p.index);
  const first = points[0];
  const last = points[points.length - 1];
  const max = values.length > 0 ? Math.max(...values) : 1;
  const min = values.length > 0 ? Math.min(...values) : 0;

  return (
    <div className="cmd-screen">
      <ScreenHead
        titleKey="forecast.title"
        guideKey={f?.disclaimer_key ?? "forecast.disclaimer"}
        aside={unitId ? <span className="cmd-unitid">{unitId}</span> : null}
      />
      <DataNotice error={forecast.error ?? unitsError} onRetry={reload} />

      <fieldset className="cmd-horizon">
        <legend className="cmd-horizon__legend">{t("forecast.horizon", { n: horizon })}</legend>
        <div className="cmd-horizon__opts">
          {HORIZONS.map((n) => (
            <label
              key={n}
              className={`cmd-horizon__opt${n === horizon ? " cmd-horizon__opt--on" : ""}`}
            >
              <input
                className="cmd-horizon__input"
                type="radio"
                name="forecast-horizon"
                value={n}
                checked={n === horizon}
                aria-label={t("forecast.horizon", { n })}
                onChange={() => setHorizon(n)}
              />
              <span aria-hidden="true">{n}</span>
            </label>
          ))}
        </div>
      </fieldset>

      {!f ? (
        forecast.loading ? (
          <div className="cmd-panel">
            <Skeleton lines={5} />
          </div>
        ) : null
      ) : f.suppressed ? (
        <p className="cmd-panel cmd-note">
          <SuppressedCell reasonKey={f.reason_key ?? undefined} vars={{ k: f.k }} />
        </p>
      ) : (
        <>
          <section className="cmd-panel">
            <div className="cmd-chart">
              <Sparkline
                points={values}
                min={Math.floor(min) - 1}
                max={Math.ceil(max) + 1}
                ariaLabelKey="forecast.title"
                width={640}
                height={160}
              />
            </div>
            <div className="cmd-chart__axis">
              <span>{first?.as_of}</span>
              <span>{last?.as_of}</span>
            </div>
            <dl className="cmd-stats">
              <div className="cmd-stats__row">
                <dt className="cmd-stats__key">{t("trend.today")}</dt>
                <dd className="cmd-stats__val">{f.index_now}</dd>
              </div>
              <div className="cmd-stats__row">
                <dt className="cmd-stats__key">
                  {t("forecast.horizon", { n: f.horizon_weeks ?? horizon })}
                </dt>
                <dd className="cmd-stats__val">
                  {f.index_horizon}
                  {typeof f.index_delta === "number" ? (
                    <span className="cmd-stats__delta">
                      {f.index_delta > 0 ? `+${f.index_delta}` : `${f.index_delta}`}
                    </span>
                  ) : null}
                </dd>
              </div>
            </dl>
          </section>

          <RuleDeltaList rows={f.drivers ?? []} titleKey="forecast.drivers" />
          {f.assumption_snapshot ? <AssumptionPanel snapshot={f.assumption_snapshot} /> : null}
        </>
      )}
    </div>
  );
}
