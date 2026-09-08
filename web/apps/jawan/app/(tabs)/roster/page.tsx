"use client";

import { useState } from "react";
import { useT } from "@saarthi/i18n";
import { CheckInCard, IconClipboard, IconClock, IconHeart, IconUser } from "@saarthi/ui";
import { mockHr } from "../../lib/mock-hr";
import { CheckInSheet } from "./CheckInSheet";

type ServiceCard = {
  key: string;
  icon: typeof IconClipboard;
  detail?: string;
  detailVars?: Record<string, string | number>;
};

const SERVICES: ServiceCard[] = [
  { key: "home.card.roster", icon: IconClipboard, detail: "roster.nextDuty", detailVars: { when: mockHr.nextDuty } },
  { key: "home.card.leave", icon: IconUser, detail: "roster.leaveBalance", detailVars: { n: mockHr.leaveBalance } },
  { key: "home.card.payslip", icon: IconClock, detail: "roster.payslip", detailVars: { month: mockHr.payslipMonth } },
  { key: "home.card.canteen", icon: IconHeart },
  { key: "home.card.grievance", icon: IconClipboard },
  { key: "home.card.welfare", icon: IconHeart },
];

export default function RosterPage() {
  const { t } = useT();
  const [sheetOpen, setSheetOpen] = useState(false);
  const [checkedToday, setCheckedToday] = useState(false);

  return (
    <>
      <h1 className="section-title" style={{ marginTop: 0 }}>
        {t("nav.roster")}
      </h1>
      <CheckInCard onOpen={() => setSheetOpen(true)} checkedInToday={checkedToday} />

      <h2 className="section-title">{t("home.section.services")}</h2>
      <div className="card-grid">
        {SERVICES.map(({ key, icon: Icon, detail, detailVars }) => (
          <article className="service-card" key={key}>
            <span className="service-card__icon">
              <Icon width={22} height={22} />
            </span>
            <p className="service-card__label">{t(key)}</p>
            {detail && detailVars && <p className="service-card__detail">{t(detail, detailVars)}</p>}
          </article>
        ))}
      </div>
      <p className="demo-note">{t("roster.demoNote")}</p>

      {sheetOpen && (
        <CheckInSheet
          onClose={() => setSheetOpen(false)}
          onSaved={() => {
            setCheckedToday(true);
            setSheetOpen(false);
          }}
        />
      )}
    </>
  );
}
