"use client";

import Link from "next/link";
import { useT } from "@saarthi/i18n";
import { IconChart, IconFileText, IconHeart, IconUsers, useApi } from "@saarthi/ui";
import { getMyInstruments } from "@saarthi/api/jawan";
import { CACHE } from "../../lib/cache";

export default function WelfarePage() {
  const { t } = useT();
  const { data } = useApi(getMyInstruments, [], { cacheKey: CACHE.instruments });

  const doneThisMonth = (data?.done_this_month.length ?? 0) > 0;

  const rows = [
    { href: "/welfare/trend", labelKey: "welfare.trend", detailKey: "trend.ownonly", icon: IconChart },
    {
      href: "/welfare/instrument",
      labelKey: "welfare.instruments",
      detailKey: doneThisMonth ? "instrument.done" : "instrument.subtitle",
      icon: IconFileText,
    },
    { href: "/welfare/pulse", labelKey: "welfare.pulse", detailKey: "pulse.intro", icon: IconUsers },
    { href: "/welfare/buddy", labelKey: "welfare.buddy", detailKey: "buddy.private", icon: IconHeart },
  ];

  return (
    <>
      <h1 className="section-title section-title--first">{t("welfare.title")}</h1>
      <p className="screen-lead">{t("trend.ownonly")}</p>

      <ul className="hub-list">
        {rows.map(({ href, labelKey, detailKey, icon: Icon }) => (
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
