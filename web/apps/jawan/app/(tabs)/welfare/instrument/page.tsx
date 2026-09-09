"use client";

import Link from "next/link";
import { useT } from "@saarthi/i18n";
import { Badge, useApi } from "@saarthi/ui";
import { BANK } from "@saarthi/instruments";
import { getMyInstruments } from "@saarthi/api/jawan";
import { CACHE } from "../../../lib/cache";
import { SubScreen } from "../../../components/SubScreen";

export default function InstrumentPickerPage() {
  const { t, locale } = useT();
  const { data } = useApi(getMyInstruments, [], { cacheKey: CACHE.instruments });
  const done = new Set(data?.done_this_month ?? []);

  return (
    <SubScreen backHref="/welfare" titleKey="instrument.title" leadKey="instrument.subtitle">
      <ul className="instrument-list">
        {BANK.map((instrument) => {
          const licencePending = instrument.licence === "licence_pending" || instrument.items.length === 0;
          const doneThisMonth = done.has(instrument.id);
          const disabled = licencePending || doneThisMonth;

          const body = (
            <>
              <span className="instrument-card__head">
                <span className="instrument-card__name">{t(instrument.nameKey)}</span>
                {doneThisMonth ? <Badge labelKey="instrument.done" /> : null}
              </span>
              {licencePending ? (
                <span className="instrument-card__note">{t("instrument.licencePending")}</span>
              ) : (
                <span className="instrument-card__meta">
                  {t("instrument.itemCount", { n: instrument.items.length })}
                </span>
              )}
              {instrument.adaptation === "review_pending" && locale === "hi" ? (
                <span className="instrument-card__note">{t("instrument.translationPending")}</span>
              ) : null}
              <span className="instrument-card__source">
                {t("instrument.source", { source: instrument.source })}
              </span>
            </>
          );

          return (
            <li key={instrument.id}>
              {disabled ? (
                <div className="instrument-card instrument-card--disabled" aria-disabled="true">
                  {body}
                </div>
              ) : (
                <Link
                  className="instrument-card instrument-card--link"
                  href={`/welfare/instrument/${instrument.id}`}
                >
                  {body}
                  <span className="instrument-card__cta">{t("instrument.start")}</span>
                </Link>
              )}
            </li>
          );
        })}
      </ul>
      <p className="footnote">{t("screen.disclaimer")}</p>
    </SubScreen>
  );
}
