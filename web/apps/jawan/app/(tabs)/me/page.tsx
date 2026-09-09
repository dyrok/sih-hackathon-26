"use client";

import Link from "next/link";
import { useT } from "@saarthi/i18n";
import { IconClock, IconFileText, IconShield, IconSliders } from "@saarthi/ui";

const ROWS = [
  { href: "/me/consent", labelKey: "me.consent", detailKey: "consent.subtitle", icon: IconShield },
  { href: "/me/receipts", labelKey: "me.receipts", detailKey: "whoViewed.footer", icon: IconFileText },
  { href: "/me/signals", labelKey: "me.signals", detailKey: "signals.noAudio", icon: IconClock },
  { href: "/me/settings", labelKey: "me.settings", detailKey: "settings.helpline", icon: IconSliders },
];

export default function MePage() {
  const { t } = useT();
  return (
    <>
      <h1 className="section-title section-title--first">{t("me.title")}</h1>
      <p className="screen-lead">{t("receipt.header")}</p>

      <ul className="hub-list">
        {ROWS.map(({ href, labelKey, detailKey, icon: Icon }) => (
          <li key={href}>
            <Link className="hub-row" href={href}>
              <span className="hub-row__icon">
                <Icon width={22} height={22} />
              </span>
              <span className="hub-row__text">
                <span className="hub-row__label">{t(labelKey)}</span>
                <span className="hub-row__detail">{t(detailKey)}</span>
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </>
  );
}
