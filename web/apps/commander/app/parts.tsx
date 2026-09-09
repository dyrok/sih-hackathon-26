"use client";

import type { ReactNode } from "react";
import { useT } from "@saarthi/i18n";
import { Button, ErrorState, IconInfo, apiErrorStatus } from "@saarthi/ui";
import type { CareState } from "@saarthi/ui";

/**
 * The pieces every commander screen repeats: the rule-of-3 header, the data-age
 * line, the failure notices, and the rule-delta list shared by the simulator and
 * the forecast. Everything here is unit-shaped or has no subject at all.
 */

/** Title + one line of guidance. Never a third heading level (design.md §3). */
export function ScreenHead({
  titleKey,
  guideKey,
  guideVars,
  aside,
}: {
  titleKey: string;
  guideKey: string;
  guideVars?: Record<string, string | number>;
  aside?: ReactNode;
}) {
  const { t } = useT();
  return (
    <header className="cmd-head">
      <div className="cmd-head__text">
        <h1 className="cmd-head__title">{t(titleKey)}</h1>
        <p className="cmd-head__guide">{t(guideKey, guideVars)}</p>
      </div>
      {aside ? <div className="cmd-head__aside">{aside}</div> : null}
    </header>
  );
}

/**
 * "Data as of …". The screen states its age rather than pretending to be live
 * (F07 refresh note). The timestamp is printed exactly as the aggregation
 * service sent it — no client-side reinterpretation of when the number is from.
 */
export function AsOf({ when, stale }: { when: string | null | undefined; stale?: boolean }) {
  const { t } = useT();
  if (!when) return null;
  // "2026-09-01T06:00:00" → "2026-09-01 06:00". Pure string work on purpose:
  // re-reading the instant in the browser's timezone would change what the
  // aggregation service said the number's age is.
  const parts = when.split("T");
  const date = parts[0] ?? when;
  const time = parts[1];
  const shown = time ? `${date} ${time.slice(0, 5)}` : date;
  return (
    <p className={`cmd-asof${stale ? " cmd-asof--stale" : ""}`}>
      {t("aggregate.stale", { when: shown })}
    </p>
  );
}

/**
 * Failure states, in the three shapes that actually happen:
 * status 0 — the network is gone, so this is a quiet reconnect banner sitting
 * over whatever was last loaded, never a blank screen;
 * 403 — the server refused on privacy grounds, which is not something to retry;
 * anything else — a calm notice with the way out as the one action.
 */
export function DataNotice({ error, onRetry }: { error: Error | null; onRetry: () => void }) {
  const { t } = useT();
  if (!error) return null;
  const status = apiErrorStatus(error);

  if (status === 0) {
    return (
      <div className="cmd-banner" role="status">
        <IconInfo className="cmd-banner__icon" width={20} height={20} aria-hidden="true" />
        <p className="cmd-banner__text">{t("error.network")}</p>
        <Button variant="quiet" onClick={onRetry}>
          {t("common.retry")}
        </Button>
      </div>
    );
  }

  if (status === 403) {
    return <ErrorState titleKey="error.403" bodyKey="cmd.firewall" />;
  }

  return <ErrorState titleKey="common.error" bodyKey="sync.error.recovery" onRetry={onRetry} />;
}

/**
 * Presentation-only ladder mapping (design.md §2). The aggregation service owns
 * the number; this only picks which care state's icon and words carry it, and
 * the colour never travels alone — every cell also renders the chip's text.
 */
export function careStateFor(share: number): CareState {
  if (share < 0.1) return "green";
  if (share < 0.25) return "amber";
  if (share < 0.5) return "red";
  return "critical";
}

/** 0.223 → "22". Used wherever a share is written as a percentage. */
export function sharePct(share: number, digits = 0): string {
  return (share * 100).toFixed(digits);
}

export type RuleDelta = { rule_id: string; before: number; after: number; delta: number };

/**
 * Which rules changed and by how much. Counts of contributors matching each
 * rule — a rule id is a ruleset identifier, never a subject.
 */
export function RuleDeltaList({ rows, titleKey }: { rows: RuleDelta[]; titleKey: string }) {
  const { t } = useT();
  return (
    <section className="cmd-rules">
      <h2 className="cmd-h2">{t(titleKey)}</h2>
      {rows.length === 0 ? (
        <p className="cmd-note">{t("common.empty")}</p>
      ) : (
        <ul className="cmd-rules__list">
          {rows.map((r) => (
            <li key={r.rule_id} className="cmd-rules__row">
              <span className="cmd-rules__id">{r.rule_id}</span>
              <span className="cmd-rules__pair">{`${r.before} → ${r.after}`}</span>
              <span className="cmd-rules__change">{r.delta > 0 ? `+${r.delta}` : `${r.delta}`}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

/**
 * The assumption snapshot, in full. It renders beside the result, never behind
 * a hidden toggle that a reader could miss: the panel is collapsed but present,
 * labelled, and keyboard-reachable.
 */
export function AssumptionPanel({
  snapshot,
  defaultOpen,
}: {
  snapshot: Record<string, unknown>;
  defaultOpen?: boolean;
}) {
  const { t } = useT();
  const entries = Object.entries(snapshot);
  return (
    <details className="cmd-details" open={defaultOpen}>
      <summary className="cmd-details__summary">{t("sim.assumptions")}</summary>
      <dl className="cmd-assume">
        {entries.map(([key, value]) => (
          <div className="cmd-assume__row" key={key}>
            <dt className="cmd-assume__key">{key}</dt>
            <dd className="cmd-assume__val">
              {value !== null && typeof value === "object" ? (
                <pre className="cmd-assume__pre">{JSON.stringify(value, null, 2)}</pre>
              ) : (
                String(value)
              )}
            </dd>
          </div>
        ))}
      </dl>
    </details>
  );
}
