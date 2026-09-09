"use client";

import { useT } from "@saarthi/i18n";
import { EmptyState, ErrorState, IconFileText, Skeleton, useApi } from "@saarthi/ui";
import { getNotifications, getWhoViewed } from "@saarthi/api/jawan";
import { CACHE } from "../../../lib/cache";
import { formatDateTime } from "../../../lib/format";
import { SubScreen } from "../../../components/SubScreen";

/** Roles the audit log can name. An unknown one renders as itself, not blank. */
const ROLE_KEYS: Record<string, string> = {
  counsellor: "whoViewed.role.counsellor",
  welfare_officer: "whoViewed.role.welfare_officer",
  admin: "whoViewed.role.admin",
  auditor: "whoViewed.role.auditor",
  jawan: "whoViewed.role.jawan",
  commander: "whoViewed.role.commander",
};

/**
 * One readable line per audit action. The two that matter most get their own
 * sentence — an identity unlock and an emergency access are the events this
 * screen exists to make undeniable (design.md §5).
 */
const ACTION_KEYS: Record<string, string> = {
  "unmask.grant": "whoViewed.unmask.line",
  "identity.read": "whoViewed.unmask.line",
  "break_glass.open": "whoViewed.breakglass.line",
  "interventions.action": "timeline.action",
  "interventions.outcome": "timeline.outcome",
  "telemanas.referral": "timeline.telemanas",
};

export default function ReceiptsPage() {
  const { t, locale } = useT();
  const receipts = useApi(getWhoViewed, [], { cacheKey: CACHE.whoViewed });
  const notifications = useApi(getNotifications, [], { cacheKey: CACHE.notifications });

  const entries = receipts.data?.entries ?? [];
  const notices = notifications.data?.notifications ?? [];

  return (
    <SubScreen backHref="/me" titleKey="whoViewed.title" leadKey="receipt.header">
      {notices.length > 0 ? (
        <ul className="notice-list">
          {notices.map((notice) => (
            <li className="notice" key={notice.id}>
              <span className="notice__text">{t(notice.body_key)}</span>
              <time className="notice__at" dateTime={notice.created_at}>
                {formatDateTime(notice.created_at, locale)}
              </time>
            </li>
          ))}
        </ul>
      ) : null}

      {receipts.loading && receipts.data === null ? <Skeleton lines={4} height="56px" /> : null}

      {receipts.data === null && receipts.error !== null ? (
        <ErrorState titleKey="error.network" bodyKey="sync.error.recovery" onRetry={receipts.reload} />
      ) : null}

      {receipts.data !== null && entries.length === 0 ? (
        <EmptyState icon={IconFileText} titleKey="whoViewed.empty" />
      ) : null}

      {entries.length > 0 ? (
        <ol className="receipt">
          {entries.map((entry, i) => {
            const actionKey = ACTION_KEYS[entry.action];
            const why = entry.why ?? "";
            const roleKey = ROLE_KEYS[entry.role];
            // The unmask and break-glass sentences carry no reason of their
            // own, so those two keep the purpose string as a second line.
            const named = actionKey === "whoViewed.unmask.line" || actionKey === "whoViewed.breakglass.line";
            const line = actionKey
              ? t(actionKey, { detail: why })
              : why
                ? t("whoViewed.why", { why })
                : "";
            return (
              <li className="receipt__row" key={`${entry.when}-${i}`}>
                <span className="receipt__role">{roleKey ? t(roleKey) : entry.role}</span>
                <time className="receipt__at" dateTime={entry.when}>
                  {formatDateTime(entry.when, locale)}
                </time>
                {line ? <span className="receipt__line">{line}</span> : null}
                {named && why ? <span className="receipt__why">{t("whoViewed.why", { why })}</span> : null}
              </li>
            );
          })}
        </ol>
      ) : null}

      <p className="footnote">{t("whoViewed.footer")}</p>
    </SubScreen>
  );
}
