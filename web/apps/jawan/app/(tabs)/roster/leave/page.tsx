"use client";

import { useT } from "@saarthi/i18n";
import { Badge, EmptyState, ErrorState, IconClipboard, Skeleton, StatTile, useApi } from "@saarthi/ui";
import { getLeave } from "@saarthi/api/jawan";
import type { LeaveApplication } from "@saarthi/api/jawan";
import { CACHE } from "../../../lib/cache";
import { formatDay } from "../../../lib/format";
import { SubScreen } from "../../../components/SubScreen";

const STATUS_KEYS: Record<LeaveApplication["status"], string> = {
  applied: "leave.status.applied",
  sanctioned: "leave.status.sanctioned",
  cancelled: "leave.status.cancelled",
};

export default function LeavePage() {
  const { t, locale } = useT();
  const { data, error, loading, reload } = useApi(getLeave, [], { cacheKey: CACHE.leave });

  const applications = data?.applications ?? [];

  return (
    <SubScreen backHref="/roster" titleKey="leave.title">
      {loading && data === null ? <Skeleton lines={4} height="52px" /> : null}

      {data === null && error !== null ? (
        <ErrorState titleKey="error.network" bodyKey="sync.error.recovery" onRetry={reload} />
      ) : null}

      {data ? (
        <StatTile
          labelKey="leave.title"
          value={t("leave.balance", { n: data.balance_days, total: data.entitlement_days })}
        />
      ) : null}

      {data !== null && applications.length === 0 ? (
        <EmptyState icon={IconClipboard} titleKey="leave.empty" />
      ) : null}

      {applications.length > 0 ? (
        <ul className="leave-list">
          {applications.map((row, i) => (
            <li className="leave-row" key={`${row.applied_at}-${i}`}>
              <span className="leave-row__head">
                <span className="leave-row__dates">
                  {row.from && row.to
                    ? `${formatDay(row.from, locale)} — ${formatDay(row.to, locale)}`
                    : formatDay(row.applied_at, locale)}
                </span>
                <Badge labelKey={STATUS_KEYS[row.status]} />
              </span>
              {row.home_leave ? <span className="leave-row__type">{t("leave.homeLeave")}</span> : null}
            </li>
          ))}
        </ul>
      ) : null}
    </SubScreen>
  );
}
