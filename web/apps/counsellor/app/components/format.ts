"use client";

/** Timestamp formatting shared by the console. Numerals are rendered with
 *  tabular-nums in CSS so a column of times lines up like a ledger. */

function toDate(value: string | number | Date): Date | null {
  const d = value instanceof Date ? value : new Date(value);
  return Number.isNaN(d.getTime()) ? null : d;
}

function intlLocale(locale: string): string {
  return locale === "hi" ? "hi-IN" : "en-IN";
}

export function formatDateTime(value: string | number | Date, locale: string): string {
  const d = toDate(value);
  if (!d) return String(value);
  return new Intl.DateTimeFormat(intlLocale(locale), {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(d);
}

export function formatDate(value: string | number | Date, locale: string): string {
  const d = toDate(value);
  if (!d) return String(value);
  return new Intl.DateTimeFormat(intlLocale(locale), {
    day: "2-digit",
    month: "short",
  }).format(d);
}

/** Whole hours between two instants, floored at zero. */
export function hoursBetween(from: string | number | Date, to: number): number {
  const d = toDate(from);
  if (!d) return 0;
  return Math.max(0, Math.floor((to - d.getTime()) / 3_600_000));
}

/** `datetime-local` wants `YYYY-MM-DDTHH:mm` in local time, not an ISO instant. */
export function toLocalInputValue(d: Date): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(
    d.getMinutes(),
  )}`;
}
