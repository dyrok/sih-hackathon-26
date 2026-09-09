"use client";

import type { ReactNode } from "react";
import Link from "next/link";
import { useParams, usePathname } from "next/navigation";
import { useT } from "@saarthi/i18n";
import { Badge, CareStateChip, Skeleton, useApi } from "@saarthi/ui";
import { getCase } from "@saarthi/api/counsellor";
import { CaseProvider } from "../../../../components/CaseContext";
import { LoadError, ReconnectBanner } from "../../../../components/LoadError";
import { SlaClock } from "../../../../components/SlaClock";
import { UnmaskPanel } from "../../../../components/UnmaskPanel";
import { formatDateTime } from "../../../../components/format";
import { useNow } from "../../../../components/useNow";

const STATUS_KEYS: Record<string, string> = {
  open: "cons.status.open",
  deferred: "cons.status.deferred",
  closed: "cons.status.closed",
};

function useCaseId(): string {
  const params = useParams();
  const raw = params?.["id"];
  return Array.isArray(raw) ? (raw[0] ?? "") : (raw ?? "");
}

/**
 * The case header is shared by evidence, notes and outcome, so the person's
 * pseudonym, care state and SLA clock never leave the screen while a counsellor
 * works — and neither does the fact that the name is still sealed.
 */
export default function CaseLayout({ children }: { children: ReactNode }) {
  const { t, locale } = useT();
  const pathname = usePathname();
  const caseId = useCaseId();
  const now = useNow();
  const { data, error, loading, reload } = useApi(() => getCase(caseId), [caseId]);

  const base = `/case/${caseId}`;
  const tabs = [
    { href: base, labelKey: "cons.case.tab.evidence" },
    { href: `${base}/notes`, labelKey: "cons.case.tab.notes" },
    { href: `${base}/outcomes`, labelKey: "cons.case.tab.outcomes" },
  ];

  if (loading && !data) {
    return <Skeleton lines={6} height="24px" />;
  }
  if (!data) {
    return <LoadError error={error} onRetry={reload} />;
  }

  const statusKey = STATUS_KEYS[data.status];

  return (
    <>
      {error ? <ReconnectBanner error={error} /> : null}

      <div className="cons-head">
        <Link className="cons-back" href="/">
          {t("cons.case.backToQueue")}
        </Link>
        <h1 className="cons-title">{t("cons.case.title", { id: caseId })}</h1>
        <p className="cons-guide">
          {data.unit_id
            ? t("cons.case.pseudonym", { id: data.pseudonym_id ?? caseId, unit: data.unit_id })
            : (data.pseudonym_id ?? caseId)}
        </p>
        <div className="cons-head__row">
          <CareStateChip state={data.tier} />
          {statusKey ? <Badge labelKey={statusKey} /> : null}
          {data.group_case ? <Badge labelKey="cons.queue.group" /> : null}
          <SlaClock openedAt={data.opened_at} slaHours={data.sla_hours} now={now} />
        </div>
        <p className="cons-meta">
          {t("cons.case.openedAt", { when: formatDateTime(data.opened_at, locale) })}
        </p>
      </div>

      <nav aria-label={t("cons.case.title", { id: caseId })}>
        <ul className="cons-subnav">
          {tabs.map((tab) => (
            <li key={tab.href}>
              <Link
                className="cons-subnav__link"
                href={tab.href}
                aria-current={pathname === tab.href ? "page" : undefined}
              >
                {t(tab.labelKey)}
              </Link>
            </li>
          ))}
        </ul>
      </nav>

      <UnmaskPanel caseId={caseId} pseudonymId={data.pseudonym_id} onChanged={reload} />

      <CaseProvider value={{ caseId, detail: data, error, loading, reload }}>{children}</CaseProvider>
    </>
  );
}
