"use client";

import { useEffect, useReducer, useRef } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useT } from "@saarthi/i18n";
import { Badge, CareStateChip, EmptyState, IconClipboard, Skeleton, useApi } from "@saarthi/ui";
import { getCase, getQueue } from "@saarthi/api/counsellor";
import type { CaseDetail } from "@saarthi/api/counsellor";
import { LoadError, ReconnectBanner } from "./LoadError";
import { SlaClock } from "./SlaClock";
import { formatDate } from "./format";
import { useNow } from "./useNow";

type RowDetail = {
  openedAt: string;
  unitId: string | null;
  topFactors: CaseDetail["top_factors"];
};

/**
 * The queue row carries the *reasons*, never a bare number (design.md §4), and
 * the reasons live on the case detail. So the rail loads detail per row, three
 * at a time, and each row fills in as its evidence arrives.
 *
 * Every one of those reads is audit-logged and receipted to the subject — that
 * is deliberate (F06: "including browsing reads"), and it is why the fetch is
 * bounded to the rows the engine actually raised rather than anything wider.
 */
function useRowDetails(caseIds: string[]): Map<string, RowDetail | "error"> {
  const cacheRef = useRef(new Map<string, RowDetail | "error">());
  const [, bump] = useReducer((n: number) => n + 1, 0);
  const key = caseIds.join(",");

  useEffect(() => {
    const ids = key ? key.split(",") : [];
    const missing = ids.filter((id) => !cacheRef.current.has(id));
    if (missing.length === 0) return;

    let cancelled = false;
    let cursor = 0;

    const lane = async (): Promise<void> => {
      for (;;) {
        if (cancelled) return;
        const id = missing[cursor];
        cursor += 1;
        if (id === undefined) return;
        try {
          const detail = await getCase(id);
          cacheRef.current.set(id, {
            openedAt: detail.opened_at,
            unitId: detail.unit_id,
            topFactors: detail.top_factors,
          });
        } catch {
          // A row that will not load still shows its tier and its clock; it is
          // never dropped from the queue.
          cacheRef.current.set(id, "error");
        }
        if (!cancelled) bump();
      }
    };

    void Promise.all(Array.from({ length: Math.min(3, missing.length) }, () => lane()));
    return () => {
      cancelled = true;
    };
  }, [key]);

  return cacheRef.current;
}

const CAP_REASON_KEYS: Record<string, string> = {
  weekly_cap: "cons.queue.capReason.weekly_cap",
  capacity_0: "cons.queue.capReason.capacity_0",
};

/** Master pane of the master–detail console: the ranked queue, always visible. */
export function QueueRail() {
  const { t, locale } = useT();
  const pathname = usePathname();
  const now = useNow();
  const { data, error, loading, reload } = useApi(() => getQueue(), [], { cacheKey: "cons.queue" });

  const rows = data?.queue ?? [];
  const details = useRowDetails(rows.map((r) => r.case_id));

  const deferred = rows.filter((r) => r.deferred_until !== null);
  const capReached = rows.some((r) => r.cap_reason === "weekly_cap");

  return (
    <section className="cons-rail" aria-labelledby="cons-queue-heading">
      <div className="cons-rail__head">
        <h2 className="cons-rail__title" id="cons-queue-heading">
          {t("cons.queue.title")}
        </h2>
        <p className="cons-rail__guide">{t("cons.queue.subtitle")}</p>
        {rows.length > 0 ? (
          <p className="cons-rail__meta">
            {t("cons.queue.count", { n: rows.length })}
            {deferred.length > 0 ? ` · ${t("cons.queue.deferredCount", { n: deferred.length })}` : ""}
          </p>
        ) : null}
      </div>

      {capReached ? <p className="cons-callout">{t("cons.queue.capReached")}</p> : null}

      {error && rows.length > 0 ? <ReconnectBanner error={error} /> : null}

      {loading && rows.length === 0 ? (
        <Skeleton lines={5} height="72px" />
      ) : error && rows.length === 0 ? (
        <LoadError error={error} onRetry={reload} />
      ) : rows.length === 0 ? (
        <EmptyState icon={IconClipboard} titleKey="queue.empty.audit" />
      ) : (
        <ul className="cons-rail__list">
          {rows.map((row) => {
            const href = `/case/${row.case_id}`;
            const active = pathname === href || pathname.startsWith(`${href}/`);
            const detail = details.get(row.case_id);
            const loaded = detail && detail !== "error" ? detail : null;
            return (
              <li key={row.case_id}>
                <Link
                  className="cons-row"
                  href={href}
                  aria-current={active ? "page" : undefined}
                  prefetch={false}
                >
                  <span className="cons-row__head">
                    <span className="cons-row__id">{row.pseudonym_id ?? row.case_id}</span>
                    <CareStateChip state={row.tier} />
                    {row.group_case ? <Badge labelKey="cons.queue.group" /> : null}
                  </span>

                  <span className="cons-row__meta">
                    {loaded?.unitId ? <span>{loaded.unitId}</span> : null}
                    <SlaClock openedAt={loaded?.openedAt ?? null} slaHours={row.sla_hours} now={now} />
                  </span>

                  {loaded && loaded.topFactors.length > 0 ? (
                    <span className="cons-row__factors">
                      {loaded.topFactors.map((f) => (
                        <span className="cons-row__factor" key={`${row.case_id}-${f.rule_id}`}>
                          {`${t(f.key)}${f.value ? ` · ${f.value}` : ""}`}
                        </span>
                      ))}
                    </span>
                  ) : detail === "error" ? (
                    <span className="cons-row__deferred">{t("cons.queue.factorsUnavailable")}</span>
                  ) : (
                    <span className="cons-row__factors" aria-hidden="true">
                      <span className="cons-row__factor cons-row__factor--ghost" />
                    </span>
                  )}

                  {row.deferred_until ? (
                    <span className="cons-row__deferred">
                      {t("cons.queue.deferred", {
                        when: formatDate(row.deferred_until, locale),
                        reason: t(
                          (row.cap_reason && CAP_REASON_KEYS[row.cap_reason]) ??
                            "cons.queue.capReason.other",
                        ),
                      })}
                    </span>
                  ) : null}
                </Link>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
