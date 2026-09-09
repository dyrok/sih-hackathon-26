"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { useApi } from "@saarthi/ui";
import { getSession } from "@saarthi/api";
import { getUnits } from "@saarthi/api/commander";
import type { UnitCell, UnitsOverview } from "@saarthi/api/commander";

/**
 * One fetch of the unit overview for the whole console.
 *
 * The heatmap reads the same object the unit picker reads, so the landing grid
 * and the four unit-scoped screens can never disagree about which units exist.
 * Everything in here is unit-shaped: the only identifier the console holds is a
 * unit id, which is the F07 firewall stated in the shape of the client state.
 */

const SELECTED_KEY = "saarthi.commander.unit";

export type UnitsContextValue = {
  overview: UnitsOverview | null;
  units: UnitCell[];
  loading: boolean;
  /** True while `overview` is the last-known cached copy rather than a fresh read. */
  stale: boolean;
  error: Error | null;
  reload: () => void;
  /** The unit the four unit-scoped screens are reading. Null until units load. */
  unitId: string | null;
  setUnitId: (id: string) => void;
};

const UnitsContext = createContext<UnitsContextValue | null>(null);

export function UnitsProvider({ children }: { children: ReactNode }) {
  const { data, error, loading, stale, reload } = useApi<UnitsOverview>(getUnits, [], {
    cacheKey: "commander.units",
  });
  const [chosen, setChosen] = useState<string | null>(null);

  // Restore the last chosen unit before the first render that has data, so a
  // reload does not silently move the operator to a different unit.
  useEffect(() => {
    try {
      const stored = localStorage.getItem(SELECTED_KEY);
      if (stored) setChosen(stored);
    } catch {
      /* private mode: the picker just starts at the first unit */
    }
  }, []);

  const units = useMemo(() => data?.units ?? [], [data]);

  const setUnitId = useMemo(
    () => (id: string) => {
      setChosen(id);
      try {
        localStorage.setItem(SELECTED_KEY, id);
      } catch {
        /* the choice still holds for this session */
      }
    },
    [],
  );

  const value = useMemo<UnitsContextValue>(() => {
    const session = getSession();
    const own = session?.unitId ?? null;
    const known = units.map((u) => u.unit_id);
    const first = known[0] ?? null;
    const resolved =
      chosen && known.includes(chosen) ? chosen : own && known.includes(own) ? own : first;
    return {
      overview: data,
      units,
      loading,
      stale,
      error,
      reload,
      unitId: resolved,
      setUnitId,
    };
  }, [data, units, loading, stale, error, reload, chosen, setUnitId]);

  return <UnitsContext.Provider value={value}>{children}</UnitsContext.Provider>;
}

export function useUnits(): UnitsContextValue {
  const ctx = useContext(UnitsContext);
  if (!ctx) throw new Error("useUnits must be used inside <UnitsProvider>");
  return ctx;
}
