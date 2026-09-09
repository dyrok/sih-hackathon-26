"use client";

import { useRouter } from "next/navigation";
import { useT } from "@saarthi/i18n";
import { CareStateChip, EmptyState, IconGrid, Skeleton, SuppressedCell } from "@saarthi/ui";
import { useUnits } from "./units";
import { AsOf, DataNotice, ScreenHead, careStateFor, sharePct } from "./parts";

const CARE_STATES = ["green", "amber", "red", "critical"] as const;
const SKELETON_CELLS = [0, 1, 2, 3, 4, 5];

/**
 * F07 screen 1 — the unit heatmap, and the console's landing screen.
 *
 * Each cell is a unit. A cell can be read at a glance (the care state's icon and
 * words), read exactly (the percentage in its label), or read as suppressed —
 * and a suppressed cell carries no number, no bar and no shading that would let
 * a reader guess one back. Drill-down ends at the unit's morale and indicators;
 * there is nothing below that to navigate to.
 */
export default function HeatmapPage() {
  const { t } = useT();
  const router = useRouter();
  const { overview, units, loading, stale, error, reload, setUnitId } = useUnits();

  const openUnit = (unitId: string) => {
    setUnitId(unitId);
    router.push("/morale");
  };

  return (
    <div className="cmd-screen">
      <ScreenHead titleKey="heat.title" guideKey="heat.legend" />
      <DataNotice error={error} onRetry={reload} />
      <AsOf when={overview?.as_of} stale={stale} />

      {!overview && loading ? (
        <ul className="cmd-grid" aria-busy="true">
          {SKELETON_CELLS.map((i) => (
            <li key={i} className="cmd-cell cmd-cell--loading">
              <Skeleton lines={2} />
            </li>
          ))}
        </ul>
      ) : overview && units.length === 0 ? (
        <EmptyState icon={IconGrid} titleKey="units.none" />
      ) : (
        <ul className="cmd-grid">
          {units.map((u) => {
            if (u.suppressed || u.elevated_share === null) {
              return (
                <li key={u.unit_id}>
                  {/* No number, no bar, no tint — suppression is not a value. */}
                  <div className="cmd-cell cmd-cell--suppressed">
                    <p className="cmd-cell__unit">{u.unit_id}</p>
                    <p className="cmd-cell__quiet">
                      <SuppressedCell
                        reasonKey={u.reason_key ?? undefined}
                        vars={{ k: u.k }}
                      />
                    </p>
                  </div>
                </li>
              );
            }
            const state = careStateFor(u.elevated_share);
            const pct = sharePct(u.elevated_share);
            return (
              <li key={u.unit_id}>
                <a
                  className={`cmd-cell cmd-cell--link cmd-cell--${state}`}
                  href="/morale"
                  onClick={(e) => {
                    if (e.defaultPrevented || e.button !== 0) return;
                    if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
                    e.preventDefault();
                    openUnit(u.unit_id);
                  }}
                >
                  <span className="cmd-cell__label">
                    {t(u.label_key, { unit: u.unit_id, pct })}
                  </span>
                  <span className="cmd-cell__bar" aria-hidden="true">
                    <span className="cmd-cell__barfill" style={{ width: `${pct}%` }} />
                  </span>
                  <CareStateChip state={state} />
                </a>
              </li>
            );
          })}
        </ul>
      )}

      <ul className="cmd-legend" aria-label={t("heat.legend")}>
        {CARE_STATES.map((s) => (
          <li key={s}>
            <CareStateChip state={s} />
          </li>
        ))}
      </ul>
    </div>
  );
}
