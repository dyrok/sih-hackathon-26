"use client";

import { useT } from "@saarthi/i18n";
import { EmptyState, IconGrid, Meter, Skeleton, StatTile, SuppressedCell, useApi } from "@saarthi/ui";
import { getIndicators } from "@saarthi/api/commander";
import type { IndicatorCell, Indicators } from "@saarthi/api/commander";
import { useUnits } from "../units";
import { AsOf, DataNotice, ScreenHead } from "../parts";

/**
 * F07 screen 3 — leading and lagging, always side by side.
 *
 * The teaching point of the screen is the pairing: the left column is what a
 * commander can still act on, the right column has already happened. So the two
 * columns render together in every state, and on a narrow screen they stack
 * while keeping their own headings — a single visible column would quietly
 * delete the lesson.
 */

/** Shares arrive as 0–1 from the aggregation service; they read as percentages. */
function isShare(key: string): boolean {
  return key.endsWith("_rate") || key.endsWith("_ratio");
}

function cellValue(cell: IndicatorCell): string | null {
  const v = cell.value;
  if (v === null || typeof v === "object") return null;
  return isShare(cell.key) ? `${(v * 100).toFixed(1)}%` : `${v}`;
}

function IndicatorTile({ cell, k }: { cell: IndicatorCell; k: number }) {
  const { t } = useT();
  const reasonKey = cell.reason_key ?? undefined;
  const counts =
    cell.value !== null && typeof cell.value === "object"
      ? Object.entries(cell.value as Record<string, number | null>)
      : null;

  // Buckets the service returned as null are folded away: a bucket below k is
  // withheld rather than shown as a small count.
  const buckets = cell.buckets ? Object.entries(cell.buckets) : [];
  const shown = buckets.filter((b): b is [string, number] => b[1] !== null);
  const folded = buckets.length - shown.length;
  const total = shown.reduce((sum, b) => sum + b[1], 0);
  const scale = cell.n ?? (total > 0 ? total : 1);

  return (
    <div className="cmd-indicator">
      <StatTile
        labelKey={cell.key}
        value={cellValue(cell)}
        suppressed={cell.suppressed || (cellValue(cell) === null && counts === null)}
        reasonKey={reasonKey}
        vars={{ k }}
      />

      {counts && !cell.suppressed ? (
        <ul className="cmd-counts">
          {counts.map(([name, n]) => (
            <li key={name} className="cmd-counts__row">
              <span className="cmd-counts__label">{t(`cons.outcome.${name}`)}</span>
              <span className="cmd-counts__value">
                {n === null ? <SuppressedCell reasonKey={reasonKey} vars={{ k }} /> : n}
              </span>
            </li>
          ))}
        </ul>
      ) : null}

      {shown.length > 0 ? (
        <div className="cmd-buckets">
          {shown.map(([name, n]) => (
            <Meter key={name} labelKey={name} value={n} min={0} max={scale} valueText={n} />
          ))}
          {folded > 0 ? (
            <p className="cmd-note">
              <SuppressedCell reasonKey={reasonKey} vars={{ k }} />
            </p>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

function Column({
  titleKey,
  cells,
  k,
}: {
  titleKey: string;
  cells: IndicatorCell[];
  k: number;
}) {
  const { t } = useT();
  return (
    <section className="cmd-col">
      <h2 className="cmd-h2">{t(titleKey)}</h2>
      <ul className="cmd-col__list">
        {cells.map((cell) => (
          <li key={cell.key}>
            <IndicatorTile cell={cell} k={k} />
          </li>
        ))}
      </ul>
    </section>
  );
}

export default function IndicatorsPage() {
  const { unitId, loading: unitsLoading, error: unitsError, reload: reloadUnits } = useUnits();

  const ind = useApi<Indicators | null>(
    () => (unitId ? getIndicators(unitId) : Promise.resolve(null)),
    [unitId],
    { cacheKey: unitId ? `commander.indicators.${unitId}` : undefined },
  );

  const reload = () => {
    reloadUnits();
    ind.reload();
  };

  if (!unitId && !unitsLoading) {
    return (
      <div className="cmd-screen">
        <ScreenHead titleKey="ind.title" guideKey="ind.teaching" />
        <DataNotice error={unitsError} onRetry={reload} />
        <EmptyState icon={IconGrid} titleKey="units.none" />
      </div>
    );
  }

  const d = ind.data;

  return (
    <div className="cmd-screen">
      <ScreenHead
        titleKey="ind.title"
        guideKey={d?.teaching_key ?? "ind.teaching"}
        aside={unitId ? <span className="cmd-unitid">{unitId}</span> : null}
      />
      <DataNotice error={ind.error ?? unitsError} onRetry={reload} />
      <AsOf when={d?.as_of} stale={ind.stale} />

      {!d ? (
        ind.loading ? (
          <div className="cmd-cols cmd-cols--two">
            <div className="cmd-panel">
              <Skeleton lines={4} />
            </div>
            <div className="cmd-panel">
              <Skeleton lines={4} />
            </div>
          </div>
        ) : null
      ) : (
        <div className="cmd-cols cmd-cols--two">
          <Column titleKey="ind.leading" cells={d.leading} k={d.k} />
          <Column titleKey="ind.lagging" cells={d.lagging} k={d.k} />
        </div>
      )}
    </div>
  );
}
