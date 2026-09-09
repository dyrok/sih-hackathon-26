"use client";

import type { ComponentType, SVGProps } from "react";
import { useT } from "@saarthi/i18n";

export type TabItem = {
  id: string;
  labelKey: string;
  icon: ComponentType<SVGProps<SVGSVGElement>>;
};

type Props = {
  tabs: TabItem[];
  active: string;
  onSelect: (id: string) => void;
};

/** Mobile-first 3-tab bottom bar (Roster / Welfare / Me). */
export function BottomTabs({ tabs, active, onSelect }: Props) {
  return (
    <nav className="sa-tabs" aria-label="Primary">
      {tabs.map(({ id, labelKey, icon: Icon }) => (
        <TabButton key={id} id={id} labelKey={labelKey} icon={Icon} active={active === id} onSelect={onSelect} />
      ))}
    </nav>
  );
}

function TabButton({
  id,
  labelKey,
  icon: Icon,
  active,
  onSelect,
}: {
  id: string;
  labelKey: string;
  icon: ComponentType<SVGProps<SVGSVGElement>>;
  active: boolean;
  onSelect: (id: string) => void;
}) {
  const { t } = useT();
  return (
    <button
      type="button"
      className={`sa-tab${active ? " sa-tab--active" : ""}`}
      aria-current={active ? "page" : undefined}
      onClick={() => onSelect(id)}
    >
      <Icon width={22} height={22} />
      <span className="sa-tab__label">{t(labelKey)}</span>
    </button>
  );
}
