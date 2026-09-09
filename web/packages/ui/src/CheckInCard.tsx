"use client";

import { useT } from "@saarthi/i18n";
import { Button } from "./Button";

type Props = {
  onOpen: () => void;
  /** True once today's check-in has been captured (queued counts). */
  checkedInToday: boolean;
  /** False only until the very first check-in this device has ever seen. */
  hasEverCheckedIn?: boolean;
};

/**
 * The calm check-in card (ADR-0004): sits on the roster home screen.
 * No badge, no streak counter, no guilt mechanics.
 *
 * Three states, not two — the middle one is the whole point of the copy:
 *   first run  → "First check-in — takes 10 seconds."   (teach)
 *   any day    → "How was today? (10 seconds)"          (ask)
 *   done today → "Checked in today. Thank you."         (close the loop)
 * Saffron is the CTA only while there is something to ask for; once today is
 * done the button steps back to quiet, so the screen keeps its single accent
 * and stops nagging someone who already answered.
 */
export function CheckInCard({ onOpen, checkedInToday, hasEverCheckedIn = true }: Props) {
  const { t } = useT();
  const titleKey = checkedInToday
    ? "home.checkin.doneToday"
    : hasEverCheckedIn
      ? "home.checkin.title"
      : "home.checkin.empty";
  return (
    <section className="sa-checkincard">
      <p className="sa-checkincard__title">{t(titleKey)}</p>
      <p className="sa-checkincard__sub">
        {t(checkedInToday ? "checkin.thanks" : "screen.disclaimer")}
      </p>
      <Button
        onClick={onOpen}
        variant={checkedInToday ? "quiet" : "primary"}
        className={checkedInToday ? "sa-checkincard__action" : "sa-checkincard__cta"}
      >
        {t("home.checkin.open")}
      </Button>
    </section>
  );
}
