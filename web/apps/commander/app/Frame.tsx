"use client";

import { useEffect, useId, useState } from "react";
import type { ReactNode } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useT } from "@saarthi/i18n";
import {
  ConsoleShell,
  IconChart,
  IconGrid,
  IconHeart,
  IconShield,
  IconSliders,
  IconTrendUp,
  IconCalendar,
  IconMic,
  LanguageToggle,
} from "@saarthi/ui";
import type { ConsoleNavItem } from "@saarthi/ui";
import { clearSession, getSession, getToken } from "@saarthi/api";
import { UnitsProvider, useUnits } from "./units";

const NAV: ConsoleNavItem[] = [
  { href: "/", labelKey: "cmd.nav.heatmap", icon: IconGrid },
  { href: "/morale", labelKey: "cmd.nav.morale", icon: IconChart },
  { href: "/indicators", labelKey: "cmd.nav.indicators", icon: IconTrendUp },
  { href: "/simulator", labelKey: "cmd.nav.simulator", icon: IconSliders },
  { href: "/forecast", labelKey: "cmd.nav.forecast", icon: IconCalendar },
  { href: "/checkin", labelKey: "cmd.nav.checkin", icon: IconHeart },
  { href: "/sitrep", labelKey: "cmd.nav.sitrep", icon: IconMic },
];

/** The screens that read one unit at a time and therefore share the picker. */
const UNIT_SCOPED = ["/morale", "/indicators", "/simulator", "/forecast"];

/**
 * The picker is chrome only when there is a choice to make: a commander whose
 * token is scoped to one unit gets it preselected and never sees a control that
 * suggests other units exist for them.
 */
function UnitPicker() {
  const { t } = useT();
  const { units, unitId, setUnitId } = useUnits();
  const id = useId();
  if (units.length < 2 || !unitId) return null;
  return (
    <div className="cmd-picker">
      <label className="cmd-picker__label" htmlFor={id}>
        {t("sim.units")}
      </label>
      <select
        id={id}
        className="sa-select cmd-picker__select"
        value={unitId}
        onChange={(e) => setUnitId(e.target.value)}
      >
        {units.map((u) => (
          <option key={u.unit_id} value={u.unit_id}>
            {u.unit_id}
          </option>
        ))}
      </select>
    </div>
  );
}

function Console({ children }: { children: ReactNode }) {
  const { t } = useT();
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<string | null>(null);

  // localStorage is read after mount so the server-rendered markup and the
  // first client render agree.
  useEffect(() => {
    setUser(getSession()?.username ?? null);
  }, []);

  const active = NAV.some((n) => n.href === pathname) ? pathname : "/";

  return (
    <ConsoleShell
      titleKey="cmd.title"
      nav={NAV}
      active={active}
      user={user}
      onNavigate={(href) => router.push(href)}
      onSignOut={() => {
        clearSession();
        router.replace("/login");
      }}
    >
      <div className="cmd-topline">
        {UNIT_SCOPED.includes(pathname) ? <UnitPicker /> : null}
        <LanguageToggle />
      </div>
      {children}
      {/* The promise, once, calmly — not a banner, not a badge (ADR-0003). */}
      <footer className="cmd-firewall">
        <IconShield className="cmd-firewall__icon" width={20} height={20} aria-hidden="true" />
        <p className="cmd-firewall__text">{t("cmd.firewall")}</p>
      </footer>
    </ConsoleShell>
  );
}

export function Frame({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const isLogin = pathname === "/login";
  const [authed, setAuthed] = useState(false);

  useEffect(() => {
    if (isLogin) return;
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    setAuthed(true);
  }, [isLogin, router]);

  if (isLogin) return <>{children}</>;
  if (!authed) return null;

  return (
    <UnitsProvider>
      <Console>{children}</Console>
    </UnitsProvider>
  );
}
