"use client";

import { useT } from "@saarthi/i18n";
import { Badge } from "@saarthi/ui";
import { hoursBetween } from "./format";

export type SlaClockProps = {
  /** ISO timestamp the case was opened at, or null while the detail loads. */
  openedAt: string | null;
  slaHours: number | null;
  now: number | null;
};

/**
 * The SLA clock counts **up** (F06 screen 1). It states elapsed hours against
 * the target and, past it, adds a factual overdue marker — no red, no siren, no
 * shaming. A counsellor already knows a case is late; the interface's job is to
 * be accurate about how late, not to editorialise.
 */
export function SlaClock({ openedAt, slaHours, now }: SlaClockProps) {
  const { t } = useT();
  if (!openedAt || now === null) return null;

  const elapsed = hoursBetween(openedAt, now);
  const overdue = slaHours !== null && elapsed > slaHours;

  return (
    <span className="cons-inline cons-inline--tight">
      <span className={`cons-sla${overdue ? " cons-sla--over" : ""}`}>
        {slaHours === null
          ? t("cons.queue.openHours", { n: elapsed })
          : t("cons.queue.sla", { n: elapsed, target: slaHours })}
      </span>
      {overdue && slaHours !== null ? (
        <Badge labelKey="cons.queue.overdue" vars={{ n: slaHours }} tone="attention" />
      ) : null}
    </span>
  );
}
