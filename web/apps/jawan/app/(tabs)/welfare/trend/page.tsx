"use client";

import { useT } from "@saarthi/i18n";
import { EmptyState, ErrorState, IconChart, Skeleton, useApi } from "@saarthi/ui";
import { getMyCheckIns, getMyTrend } from "@saarthi/api/jawan";
import { CACHE } from "../../../lib/cache";
import { formatDay, localDate } from "../../../lib/format";
import { SubScreen } from "../../../components/SubScreen";
import { TrendLine } from "../../../components/TrendLine";
import type { TrendPointView } from "../../../components/TrendLine";

const WINDOW_DAYS = 90;

export default function TrendPage() {
  const { t, locale } = useT();
  const checkins = useApi(() => getMyCheckIns(WINDOW_DAYS), [], { cacheKey: CACHE.checkins });
  const trend = useApi(getMyTrend, [], { cacheKey: CACHE.trend });

  const rows = checkins.data?.checkins ?? [];
  const points: TrendPointView[] = rows
    .filter((row): row is typeof row & { mood_score: number } => row.mood_score !== null)
    .map((row) => ({ date: row.date.slice(0, 10), value: row.mood_score }));

  const today = checkins.data?.as_of?.slice(0, 10) ?? localDate();

  // The engine's own trend is used for MARKERS only — a tick on the days when
  // outreach was due. No score and no tier is rendered: the person's line is
  // their check-ins, not a risk number about them.
  const markers = (trend.data?.trend ?? [])
    .filter((p) => p.tier === "red" || p.tier === "critical")
    .map((p) => p.as_of.slice(0, 10));

  const readings = points.map((p) => `${formatDay(p.date, locale)} ${p.value}`).join(", ");
  const summary = markers.length > 0
    ? `${t("trend.axis.days")}: ${readings}. ${t("trend.marker.action")}: ${markers.length}`
    : `${t("trend.axis.days")}: ${readings}`;

  return (
    <SubScreen backHref="/welfare" titleKey="trend.title" leadKey="trend.ownonly">
      {checkins.loading && checkins.data === null ? <Skeleton lines={5} height="24px" /> : null}

      {checkins.data === null && checkins.error !== null ? (
        <ErrorState titleKey="error.network" bodyKey="sync.error.recovery" onRetry={checkins.reload} />
      ) : null}

      {checkins.data !== null && points.length === 0 ? (
        <EmptyState icon={IconChart} titleKey="trend.empty" bodyKey="home.checkin.empty" />
      ) : null}

      {points.length > 0 ? (
        <>
          <TrendLine
            points={points}
            today={today}
            days={WINDOW_DAYS}
            markers={markers}
            summary={summary}
          />
          <p className="trend-axis">
            <span>{t("trend.axis.days")}</span>
            <span>{t("trend.today")}</span>
          </p>
        </>
      ) : null}

      <p className="footnote">{t("expiry.explain")}</p>
    </SubScreen>
  );
}
