"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useT } from "@saarthi/i18n";
import { Button, ErrorState, Skeleton, Toast, apiErrorStatus, useApi } from "@saarthi/ui";
import { getConsent, getMyPulse, submitPulse } from "@saarthi/api/jawan";
import type { PulseFacet } from "@saarthi/api/jawan";
import { enqueue, newItemUuid, notifyQueueChanged } from "@saarthi/sync";
import { CACHE } from "../../../lib/cache";
import { localDate } from "../../../lib/format";
import { SubScreen } from "../../../components/SubScreen";

const FACET_KEYS: Record<PulseFacet, string> = {
  leadership: "pulse.facet.leadership",
  fairness: "pulse.facet.fairness",
  family_support: "pulse.facet.family_support",
  facilities: "pulse.facet.facilities",
};

const RATINGS = [1, 2, 3, 4, 5] as const;

/**
 * k is a server-side setting (config.k_anonymity) and the jawan API never
 * returns it — the aggregate endpoint that enforces it belongs to the
 * commander surface. 5 is the value the whole product is specified around
 * (FR-19, ADR-0003); it is stated here so the sentence on screen is concrete.
 */
const K_ANONYMITY = 5;

export default function PulsePage() {
  const { t } = useT();
  const consent = useApi(getConsent, [], { cacheKey: CACHE.consent });
  const pulse = useApi(getMyPulse, [], { cacheKey: CACHE.pulse });

  const [ratings, setRatings] = useState<Partial<Record<PulseFacet, number>>>({});
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [refused, setRefused] = useState(false);

  useEffect(() => {
    if (pulse.data) setRatings(pulse.data.mine);
  }, [pulse.data]);

  const granted = consent.data?.bundles.find((b) => b.bundle_id === "unit_pulse")?.granted ?? null;
  const facets = pulse.data?.facets ?? (Object.keys(FACET_KEYS) as PulseFacet[]);
  const period = pulse.data?.period ?? "";

  const chosen = facets
    .map((facet) => ({ facet, rating: ratings[facet] }))
    .filter((r): r is { facet: PulseFacet; rating: number } => r.rating !== undefined);

  const submit = async () => {
    if (saving || chosen.length === 0) return;
    setSaving(true);
    setRefused(false);
    try {
      await submitPulse(chosen);
      setSaved(true);
    } catch (err) {
      if (apiErrorStatus(err) === 403) {
        // The server refused on consent grounds. Explain, never retry.
        setRefused(true);
      } else {
        // Offline or server down: one queued row per facet, matching the
        // shape /app/sync expects.
        for (const item of chosen) {
          await enqueue({
            table: "pulse",
            client_uuid: newItemUuid(),
            captured_at: new Date().toISOString(),
            payload: {
              facet: item.facet,
              rating: item.rating,
              ...(period ? { period } : {}),
              recorded_at: localDate(),
            },
          });
        }
        notifyQueueChanged();
        setSaved(true);
      }
    } finally {
      setSaving(false);
    }
  };

  if (granted === false || refused) {
    return (
      <SubScreen backHref="/welfare" titleKey="pulse.title" leadKey="pulse.intro">
        <p className="screen-lead">{t("pulse.needConsent")}</p>
        <Link className="hub-row" href="/me/consent">
          <span className="hub-row__text">
            <span className="hub-row__label">{t("me.consent")}</span>
            <span className="hub-row__detail">{t("consent.turnOn")}</span>
          </span>
        </Link>
      </SubScreen>
    );
  }

  return (
    <SubScreen backHref="/welfare" titleKey="pulse.title" leadKey="pulse.intro">
      {pulse.loading && pulse.data === null ? <Skeleton lines={4} height="56px" /> : null}

      {pulse.data === null && pulse.error !== null ? (
        <ErrorState titleKey="error.network" bodyKey="sync.error.recovery" onRetry={pulse.reload} />
      ) : null}

      {period ? <p className="pulse-period">{t("pulse.period", { period })}</p> : null}

      {facets.map((facet) => (
        <fieldset className="pulse-facet" key={facet}>
          <legend className="pulse-facet__legend">{t(FACET_KEYS[facet])}</legend>
          <div className="pulse-scale">
            {RATINGS.map((value) => {
              const selected = ratings[facet] === value;
              return (
                <label className={`pulse-dot${selected ? " pulse-dot--selected" : ""}`} key={value}>
                  <input
                    className="pulse-dot__input"
                    type="radio"
                    name={`pulse-${facet}`}
                    value={value}
                    checked={selected}
                    aria-label={`${t(FACET_KEYS[facet])} ${value}`}
                    onChange={() => {
                      setRatings((prev) => ({ ...prev, [facet]: value }));
                      setSaved(false);
                    }}
                  />
                  <span className="pulse-dot__value" aria-hidden="true">
                    {value}
                  </span>
                </label>
              );
            })}
          </div>
          <p className="pulse-anchors">
            <span>{t("pulse.scale.1")}</span>
            <span>{t("pulse.scale.5")}</span>
          </p>
        </fieldset>
      ))}

      <Button onClick={() => void submit()} loading={saving} disabled={chosen.length === 0}>
        {t("pulse.submit")}
      </Button>

      <p className="footnote">{t("pulse.anonymous", { k: K_ANONYMITY })}</p>

      {saved ? (
        <Toast messageKey="pulse.done" vars={{ period }} timeoutMs={6000} onDismiss={() => setSaved(false)} />
      ) : null}
    </SubScreen>
  );
}
