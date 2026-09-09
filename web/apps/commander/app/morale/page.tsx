"use client";

import { useT } from "@saarthi/i18n";
import { Badge, Dial, EmptyState, IconGrid, Skeleton, StatTile, useApi } from "@saarthi/ui";
import { getMorale, getPulseAggregate } from "@saarthi/api/commander";
import type { Morale, PulseAggregate } from "@saarthi/api/commander";
import { useUnits } from "../units";
import { DataNotice, ScreenHead } from "../parts";

/**
 * F07 screen 2 — the morale index.
 *
 * A computed 0–100 index, labelled as one: the dial is never presented as a
 * survey result or an officer's opinion, and every component that builds it
 * expands to show its own contributor count. Each component and each pulse
 * facet is suppressed on its own rater count, so a unit can show three parts of
 * the index and withhold the fourth.
 */
export default function MoralePage() {
  const { t } = useT();
  const { unitId, loading: unitsLoading, error: unitsError, reload: reloadUnits } = useUnits();

  const morale = useApi<Morale | null>(
    () => (unitId ? getMorale(unitId) : Promise.resolve(null)),
    [unitId],
    { cacheKey: unitId ? `commander.morale.${unitId}` : undefined },
  );
  const pulse = useApi<PulseAggregate | null>(
    () => (unitId ? getPulseAggregate(unitId) : Promise.resolve(null)),
    [unitId],
    { cacheKey: unitId ? `commander.pulse.${unitId}` : undefined },
  );

  const reload = () => {
    reloadUnits();
    morale.reload();
    pulse.reload();
  };

  if (!unitId && !unitsLoading) {
    return (
      <div className="cmd-screen">
        <ScreenHead titleKey="morale.title" guideKey="morale.formula" />
        <DataNotice error={unitsError} onRetry={reload} />
        <EmptyState icon={IconGrid} titleKey="units.none" />
      </div>
    );
  }

  const m = morale.data;
  const p = pulse.data;

  return (
    <div className="cmd-screen">
      <ScreenHead
        titleKey="morale.title"
        guideKey="morale.formula"
        aside={
          <>
            {unitId ? <span className="cmd-unitid">{unitId}</span> : null}
            {m ? <Badge labelKey="morale.week" vars={{ week: m.week }} /> : null}
          </>
        }
      />
      <DataNotice error={morale.error ?? unitsError} onRetry={reload} />

      {!m ? (
        morale.loading ? (
          <div className="cmd-panel">
            <Skeleton lines={4} />
          </div>
        ) : null
      ) : (
        <>
          <div className="cmd-panel cmd-panel--dial">
            <Dial
              value={m.score}
              labelKey="morale.title"
              suppressed={m.suppressed}
              reasonKey={m.reason_key ?? undefined}
              vars={{ k: m.k }}
            />
          </div>

          <ul className="cmd-cols cmd-cols--three">
            {Object.entries(m.components).map(([name, c]) => (
              <li key={name}>
                <details className="cmd-details cmd-details--tile">
                  <summary className="cmd-details__summary cmd-details__summary--tile">
                    <StatTile
                      labelKey={c.label_key}
                      value={c.value}
                      suppressed={c.suppressed}
                      vars={{ k: m.k }}
                    />
                  </summary>
                  <div className="cmd-details__body">
                    {c.n !== null && c.n !== undefined ? (
                      <p className="cmd-note">{t("signals.rows", { n: c.n })}</p>
                    ) : null}
                    {c.facets && c.facets.length > 0 ? (
                      <ul className="cmd-facets">
                        {c.facets.map((f) => (
                          <li key={f} className="cmd-facets__item">
                            {t(`pulse.facet.${f}`)}
                          </li>
                        ))}
                      </ul>
                    ) : null}
                  </div>
                </details>
              </li>
            ))}
          </ul>
        </>
      )}

      <section className="cmd-section">
        <h2 className="cmd-h2">{t("pulse.title")}</h2>
        <p className="cmd-note">{t("pulse.anonymous", { k: p?.k ?? m?.k ?? 5 })}</p>
        <DataNotice error={pulse.error} onRetry={() => pulse.reload()} />
        {!p ? (
          pulse.loading ? (
            <div className="cmd-panel">
              <Skeleton lines={2} />
            </div>
          ) : null
        ) : (
          <>
            <p className="cmd-asof">{t("pulse.period", { period: p.period })}</p>
            <ul className="cmd-cols cmd-cols--four">
              {Object.entries(p.facets).map(([name, facet]) => (
                <li key={name}>
                  <StatTile
                    labelKey={`pulse.facet.${name}`}
                    value={facet.mean}
                    suppressed={facet.suppressed || facet.mean === null}
                    vars={{ k: p.k }}
                  />
                </li>
              ))}
            </ul>
          </>
        )}
      </section>
    </div>
  );
}
