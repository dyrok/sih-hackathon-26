/**
 * Date/number formatting for the jawan app.
 *
 * Every helper takes the locale explicitly rather than reading a global, so a
 * language switch re-renders the numbers with the text (design.md §3).
 */

type Locale = "en" | "hi";

const intlLocale = (locale: Locale) => (locale === "hi" ? "hi-IN" : "en-IN");

/** Local calendar day as YYYY-MM-DD — the check-in's "today", not UTC's. */
export function localDate(d: Date = new Date()): string {
  return d.toLocaleDateString("en-CA");
}

function parse(iso: string): Date | null {
  // "2026-09-09" is parsed as UTC midnight by Date; adding the time part keeps
  // a day-granular string on the day the user means in their own timezone.
  const value = /^\d{4}-\d{2}-\d{2}$/.test(iso) ? `${iso}T00:00:00` : iso;
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? null : d;
}

/** "09 Sep" — a roster row, a trend tick. */
export function formatDay(iso: string, locale: Locale): string {
  const d = parse(iso);
  if (!d) return iso;
  return new Intl.DateTimeFormat(intlLocale(locale), { day: "2-digit", month: "short" }).format(d);
}

/** "Tue 09 Sep" — the next-duty line. */
export function formatWeekday(iso: string, locale: Locale): string {
  const d = parse(iso);
  if (!d) return iso;
  return new Intl.DateTimeFormat(intlLocale(locale), {
    weekday: "short",
    day: "2-digit",
    month: "short",
  }).format(d);
}

/** "09 Sep, 14:32" — receipt timestamps, tabular-nums in CSS. */
export function formatDateTime(iso: string, locale: Locale): string {
  const d = parse(iso);
  if (!d) return iso;
  return new Intl.DateTimeFormat(intlLocale(locale), {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(d);
}

/** "Aug 2026" from a "YYYY-MM" pay-slip month. */
export function formatMonth(value: string, locale: Locale): string {
  const d = parse(/^\d{4}-\d{2}$/.test(value) ? `${value}-01` : value);
  if (!d) return value;
  return new Intl.DateTimeFormat(intlLocale(locale), { month: "short", year: "numeric" }).format(d);
}

export function isToday(iso: string): boolean {
  return iso.slice(0, 10) === localDate();
}
