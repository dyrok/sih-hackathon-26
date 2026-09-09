"use client";

import { useState } from "react";
import Link from "next/link";
import { useT } from "@saarthi/i18n";
import {
  CheckInCard,
  IconCalendar,
  IconClipboard,
  IconFileText,
  IconHeart,
  IconUser,
  Skeleton,
  UndoBar,
  useApi,
} from "@saarthi/ui";
import { getLeave, getMyCheckIns, getPayslip, getRoster } from "@saarthi/api/jawan";
import { notifyQueueChanged, removeFromQueue } from "@saarthi/sync";
import { CACHE } from "../../lib/cache";
import { formatMonth, formatWeekday } from "../../lib/format";
import { mockHr } from "../../lib/mock-hr";
import { CheckInSheet } from "./CheckInSheet";

const SHIFT_KEYS: Record<string, string> = {
  day: "roster.shift.day",
  evening: "roster.shift.evening",
  night: "roster.shift.night",
};

/** An unrecognised shift code is shown as the roster wrote it, never renamed. */
function shiftLabel(code: string, t: (key: string) => string): string {
  const key = SHIFT_KEYS[code];
  return key ? t(key) : code;
}

/** Undo window for a saved check-in, in ms. */
const UNDO_MS = 8000;

export default function RosterPage() {
  const { t, locale } = useT();
  const [sheetOpen, setSheetOpen] = useState(false);
  const [undoId, setUndoId] = useState<number | null>(null);
  const [savedLocally, setSavedLocally] = useState(false);

  const roster = useApi(() => getRoster(14), [], { cacheKey: CACHE.roster });
  const leave = useApi(getLeave, [], { cacheKey: CACHE.leave });
  const payslip = useApi(getPayslip, [], { cacheKey: CACHE.payslip });
  const checkins = useApi(() => getMyCheckIns(1), [], { cacheKey: CACHE.checkinsToday });

  const loading = roster.loading && roster.data === null;
  // The mock adapter is the last resort: a first run that has never reached the
  // server and so has nothing cached either.
  const degraded = roster.data === null && roster.error !== null;

  const nextDuty = roster.data?.next_duty ?? null;
  const dutyLine = nextDuty
    ? t("roster.nextDuty", {
        when: `${formatWeekday(nextDuty.date, locale)} · ${shiftLabel(nextDuty.shift_code, t)}`,
      })
    : degraded
      ? t("roster.nextDuty", {
          when: `${formatWeekday(mockHr.nextDutyDate, locale)} · ${shiftLabel(mockHr.nextDutyShift, t)}`,
        })
      : t("roster.nextDuty.none");

  const leaveLine = t("roster.leaveBalance", {
    n: leave.data?.balance_days ?? (degraded ? mockHr.leaveBalance : 0),
  });

  const payslipLine = payslip.data
    ? payslip.data.available
      ? t("roster.payslip", { month: formatMonth(payslip.data.month, locale) })
      : t("roster.payslip.unavailable")
    : t("roster.payslip", { month: formatMonth(mockHr.payslipMonth, locale) });

  const checkedInToday = savedLocally || (checkins.data?.checked_in_today ?? false);
  // First run is "the server has never seen one and this device has not just
  // made one" — otherwise the teaching copy reappears every morning.
  const hasEverCheckedIn = savedLocally || (checkins.data?.checkins.length ?? 0) > 0;

  const undo = async () => {
    if (undoId !== null) await removeFromQueue(undoId);
    notifyQueueChanged();
    setSavedLocally(false);
    setUndoId(null);
  };

  return (
    <>
      <h1 className="section-title section-title--first">{t("nav.roster")}</h1>

      <CheckInCard
        onOpen={() => setSheetOpen(true)}
        checkedInToday={checkedInToday}
        hasEverCheckedIn={hasEverCheckedIn}
      />

      <h2 className="section-title">{t("home.section.services")}</h2>
      {loading ? (
        <Skeleton lines={4} height="72px" />
      ) : (
        <div className="card-grid">
          <Link className="service-card service-card--link" href="/roster/duty">
            <span className="service-card__icon">
              <IconCalendar width={22} height={22} />
            </span>
            <span className="service-card__label">{t("home.card.roster")}</span>
            <span className="service-card__detail">{dutyLine}</span>
          </Link>

          <Link className="service-card service-card--link" href="/roster/leave">
            <span className="service-card__icon">
              <IconClipboard width={22} height={22} />
            </span>
            <span className="service-card__label">{t("home.card.leave")}</span>
            <span className="service-card__detail">{leaveLine}</span>
          </Link>

          <article className="service-card">
            <span className="service-card__icon">
              <IconFileText width={22} height={22} />
            </span>
            <p className="service-card__label">{t("home.card.payslip")}</p>
            <p className="service-card__detail">{payslipLine}</p>
          </article>

          <article className="service-card">
            <span className="service-card__icon">
              <IconHeart width={22} height={22} />
            </span>
            <p className="service-card__label">{t("home.card.canteen")}</p>
            <p className="service-card__detail">{t("coming.soon")}</p>
          </article>

          <article className="service-card">
            <span className="service-card__icon">
              <IconClipboard width={22} height={22} />
            </span>
            <p className="service-card__label">{t("home.card.grievance")}</p>
            <p className="service-card__detail">{t("coming.soon")}</p>
          </article>

          <article className="service-card">
            <span className="service-card__icon">
              <IconUser width={22} height={22} />
            </span>
            <p className="service-card__label">{t("home.card.welfare")}</p>
            <p className="service-card__detail">{t("coming.soon")}</p>
          </article>
        </div>
      )}

      {degraded ? <p className="demo-note">{t("roster.demoNote")}</p> : null}
      {roster.data !== null && roster.error !== null ? (
        <p className="demo-note">{t("error.network")}</p>
      ) : null}

      {sheetOpen ? (
        <CheckInSheet
          onClose={() => setSheetOpen(false)}
          onSaved={(queueId) => {
            setSavedLocally(true);
            setUndoId(queueId);
            setSheetOpen(false);
          }}
        />
      ) : null}

      {undoId !== null ? (
        <UndoBar
          messageKey="checkin.thanks"
          actionKey="checkin.undo"
          timeoutMs={UNDO_MS}
          onAction={() => void undo()}
          onDismiss={() => setUndoId(null)}
        />
      ) : null}
    </>
  );
}
