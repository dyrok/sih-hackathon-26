"use client";

import { useT } from "@saarthi/i18n";
import { Badge, ErrorState, Skeleton, useApi } from "@saarthi/ui";
import { getSignalsSummary } from "@saarthi/api/jawan";
import { CACHE } from "../../../lib/cache";
import { formatDay } from "../../../lib/format";
import { SubScreen } from "../../../components/SubScreen";

export default function SignalsPage() {
  const { t, locale } = useT();
  const { data, error, loading, reload } = useApi(getSignalsSummary, [], { cacheKey: CACHE.signals });

  return (
    <SubScreen backHref="/me" titleKey="signals.title" leadKey="expiry.explain">
      {loading && data === null ? <Skeleton lines={5} height="56px" /> : null}

      {data === null && error !== null ? (
        <ErrorState titleKey="error.network" bodyKey="sync.error.recovery" onRetry={reload} />
      ) : null}

      <ul className="signal-list">
        {(data?.scopes ?? []).map((scope) => (
          <li className="signal-row" key={scope.bundle_id}>
            <span className="signal-row__head">
              <span className="signal-row__label">{t(scope.label_key)}</span>
              {scope.granted ? null : <Badge labelKey="consent.off" />}
            </span>
            <span className="signal-row__rows">
              {scope.rows_held > 0 ? t("signals.rows", { n: scope.rows_held }) : t("signals.none")}
            </span>
            {scope.oldest_expiry ? (
              <span className="signal-row__expiry">
                {t("signals.expires", { when: formatDay(scope.oldest_expiry, locale) })}
              </span>
            ) : null}
          </li>
        ))}
      </ul>

      {/* The single most load-bearing sentence on this screen (F03, ADR-0002). */}
      <p className="signal-noaudio">{t("signals.noAudio")}</p>
      {data ? <p className="footnote">{t(data.explain_key)}</p> : null}
    </SubScreen>
  );
}
