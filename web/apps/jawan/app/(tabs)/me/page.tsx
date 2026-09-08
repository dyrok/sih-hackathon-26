"use client";

import { useT } from "@saarthi/i18n";
import { IconGlobe, IconShield, IconUser } from "@saarthi/ui";

const ITEMS = [
  { key: "me.consent", icon: IconShield },
  { key: "me.receipts", icon: IconUser },
  { key: "me.settings", icon: IconGlobe },
] as const;

export default function MePage() {
  const { t } = useT();
  return (
    <>
      <h1 className="section-title" style={{ marginTop: 0 }}>
        {t("nav.me")}
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
