"use client";

import { useT } from "@saarthi/i18n";

/** Rail marker kinds. Nothing here is an alarm level — these are record types. */
export type TimelineKind = "info" | "action" | "outcome" | "access" | "care";

export type TimelineEvent = {
  at: string | number | Date;
  key: string;
  vars?: Record<string, string | number>;
  kind: TimelineKind;
};

export type TimelineProps = {
  events: TimelineEvent[];
  emptyKey?: string;
};

function formatAt(at: TimelineEvent["at"], locale: string): { text: string; iso: string } {
  const d = at instanceof Date ? at : new Date(at);
  if (Number.isNaN(d.getTime())) return { text: String(at), iso: "" };
  const fmt = new Intl.DateTimeFormat(locale === "hi" ? "hi-IN" : "en-IN", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
  return { text: fmt.format(d), iso: d.toISOString() };
}

/**
 * The receipt, not the warning (design.md §5). An ordered list on a rail, calm
 * and factual, with tabular-nums timestamps so a column of times lines up and
 * reads like a ledger rather than an incident report.
 */
export function Timeline({ events, emptyKey = "common.empty" }: TimelineProps) {
  const { t, locale } = useT();

  if (events.length === 0) {
    return <p className="sa-timeline__empty">{t(emptyKey)}</p>;
  }

  return (
    <ol className="sa-timeline">
      {events.map((e, i) => {
        const { text, iso } = formatAt(e.at, locale);
        return (
          <li key={`${iso}-${e.key}-${i}`} className={`sa-timeline__item sa-timeline__item--${e.kind}`}>
            <span className="sa-timeline__dot" aria-hidden="true" />
            <time className="sa-timeline__at" dateTime={iso || undefined}>
              {text}
            </time>
            <span className="sa-timeline__text">{t(e.key, e.vars)}</span>
          </li>
        );
      })}
    </ol>
  );
}
