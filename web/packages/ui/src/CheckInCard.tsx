"use client";

import { useT } from "@saarthi/i18n";
import { Button } from "./Button";

type Props = {
  onOpen: () => void;
  checkedInToday: boolean;
};

/**
 * The calm check-in card (ADR-0004): sits on the roster home screen.
 * No badge, no streak counter, no guilt mechanics. Saffron is reserved for
 * this one CTA on the screen.
 */
export function CheckInCard({ onOpen, checkedInToday }: Props) {
  const { t } = useT();
  return (
    <section className="sa-checkincard">
      <p className="sa-checkincard__title">
        {checkedInToday ? t("home.checkin.empty") : t("home.checkin.title")}
      </p>
      <p className="sa-checkincard__sub">{t("screen.disclaimer")}</p>
      <Button onClick={onOpen} className="sa-checkincard__cta">
        {t("home.checkin.open")}
      </Button>
    </section>
  );
}
