"use client";

import { useT } from "@saarthi/i18n";
import { IconClock, IconHeart, IconUser } from "@saarthi/ui";

const ITEMS = [
  { key: "welfare.trend", icon: IconClock },
  { key: "welfare.pulse", icon: IconHeart },
  { key: "welfare.buddy", icon: IconUser },
] as const;

export default function WelfarePage() {
  const { t } = useT();
  return (
    <>
      <h1 className="section-title" style={{ marginTop: 0 }}>
        {t("nav.welfare")}
      </h1>
      {ITEMS.map(({ key, icon: Icon }) => (
        <div className="list-row" key={key}>
          <span className="list-row__label">
            <span className="list-row__icon">
              <Icon width={22} height={22} />
            </span>
            {t(key)}
          </span>
          <span className="sa-syncpill">{t("coming.soon")}</span>
        </div>
      ))}
    </>
  );
}
