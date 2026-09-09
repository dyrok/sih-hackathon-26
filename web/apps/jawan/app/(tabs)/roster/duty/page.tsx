"use client";

import { useT } from "@saarthi/i18n";
import { Badge, EmptyState, ErrorState, IconCalendar, Skeleton, useApi } from "@saarthi/ui";
import { getRoster } from "@saarthi/api/jawan";
import { CACHE } from "../../../lib/cache";
import { formatWeekday } from "../../../lib/format";
import { SubScreen } from "../../../components/SubScreen";

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

const WINDOW_DAYS = 14;

export default function DutyPage() {
  const { t, locale } = useT();
  const { data, error, loading, reload } = useApi(() => getRoster(WINDOW_DAYS), [], {
    cacheKey: CACHE.roster,
  });

  const today = data?.as_of ?? "";
  const all = data?.days ?? [];
  const upcoming = all.filter((d) => d.date >= today);
  // A roster that has run out still has to show something truthful rather than
  // an empty screen, so fall back to the tail of what the server returned.
  const days = (upcoming.length > 0 ? upcoming : all.slice(-WINDOW_DAYS)).slice(0, WINDOW_DAYS);

  return (
    <SubScreen backHref="/roster" titleKey="roster.title" leadKey="roster.section.upcoming">
      {loading && data === null ? <Skeleton lines={6} height="52px" /> : null}

      {data === null && error !== null ? (
        <ErrorState titleKey="error.network" bodyKey="sync.error.recovery" onRetry={reload} />
      ) : null}

      {data !== null && days.length === 0 ? (
        <EmptyState icon={IconCalendar} titleKey="common.empty" bodyKey="roster.nextDuty.none" />
      ) : null}

      {days.length > 0 ? (
        <ul className="duty-list">
          {days.map((day) => (
            <li className={`duty-row${day.date === today ? " duty-row--today" : ""}`} key={day.date}>
              <span className="duty-row__date">{formatWeekday(day.date, locale)}</span>
              <span className="duty-row__meta">
                {day.date === today ? <Badge labelKey="roster.today" tone="attention" /> : null}
                {day.rest_day ? (
                  <Badge labelKey="roster.restDay" />
                ) : (
                  <span className="duty-row__shift">{shiftLabel(day.shift_code, t)}</span>
                )}
              </span>
            </li>
          ))}
        </ul>
      ) : null}
    </SubScreen>
  );
}
