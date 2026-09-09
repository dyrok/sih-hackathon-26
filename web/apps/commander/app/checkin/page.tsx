"use client";

import { useState } from "react";
import { useT } from "@saarthi/i18n";
import {
  Button,
  CheckInCard,
  Sheet,
  Skeleton,
  Slider,
  Sparkline,
  Toast,
  useApi,
} from "@saarthi/ui";
import { getOwnCheckIns, submitOwnCheckIn } from "@saarthi/api/commander";
import type { OwnCheckIn } from "@saarthi/api/commander";
import { DataNotice, ScreenHead } from "../parts";

/**
 * The closed set the rules engine reads, and the same 1–5 emoji ladder the
 * jawan app uses. `mood_score` runs 0–10 with HIGHER meaning lighter, so the
 * "how heavy did today feel" slider is inverted on the way out — identical
 * convention to F02, so one person's check-in means the same thing whatever
 * rank they hold.
 */
const MOODS = [
  { value: 1, face: "😞", label: "rough" },
  { value: 2, face: "😕", label: "low" },
  { value: 3, face: "😐", label: "ok" },
  { value: 4, face: "🙂", label: "good" },
  { value: 5, face: "😄", label: "fine" },
] as const;

/**
 * F07 screen 6 — the commander's own check-in.
 *
 * Officer-first rollout (ADR-0004): command takes the check-in before asking
 * anyone else to. This is the one screen in the console with a person on it,
 * and that person is the signed-in operator themselves — their own data, under
 * their own token, on a route that accepts no subject selector at all.
 */
export default function CheckInPage() {
  const { t } = useT();
  const history = useApi<OwnCheckIn>(() => getOwnCheckIns(30), [], {
    cacheKey: "commander.own.checkins",
  });

  const [open, setOpen] = useState(false);
  const [mood, setMood] = useState<number | null>(null);
  const [heavy, setHeavy] = useState(5);
  const [error, setError] = useState<"mood" | "save" | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const close = () => {
    setOpen(false);
    setError(null);
  };

  const save = async () => {
    if (saving) return;
    if (mood === null) {
      setError("mood");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const picked = MOODS.find((m) => m.value === mood);
      await submitOwnCheckIn({
        mood_label: picked ? picked.label : "ok",
        mood_score: 10 - heavy,
        recorded_at: new Date().toLocaleDateString("en-CA"),
      });
      setOpen(false);
      setMood(null);
      setHeavy(5);
      setSaved(true);
      history.reload();
    } catch {
      setError("save");
    } finally {
      setSaving(false);
    }
  };

  const rows = (history.data?.checkins ?? []).filter(
    (c): c is { date: string; mood_score: number } => c.mood_score !== null,
  );

  return (
    <div className="cmd-screen">
      <ScreenHead titleKey="cmd.checkin.title" guideKey="cmd.checkin.intro" />
      <DataNotice error={history.error} onRetry={() => history.reload()} />

      <div className="cmd-checkin">
        <CheckInCard
          onOpen={() => setOpen(true)}
          checkedInToday={history.data?.checked_in_today ?? false}
          hasEverCheckedIn={(history.data?.checkins.length ?? 0) > 0}
        />
      </div>

      <section className="cmd-panel">
        <h2 className="cmd-h2">{t("trend.title")}</h2>
        <p className="cmd-note">{t("trend.ownonly")}</p>
        {!history.data ? (
          history.loading ? (
            <Skeleton lines={2} />
          ) : null
        ) : rows.length === 0 ? (
          <p className="cmd-note">{t("trend.empty")}</p>
        ) : (
          <>
            <div className="cmd-chart">
              <Sparkline
                points={rows.map((c) => c.mood_score)}
                min={0}
                max={10}
                ariaLabelKey="trend.title"
                width={480}
                height={100}
              />
            </div>
            <div className="cmd-chart__axis">
              <span>{rows[0]?.date}</span>
              <span>{rows[rows.length - 1]?.date}</span>
            </div>
          </>
        )}
      </section>

      {saved ? (
        <Toast messageKey="cmd.checkin.saved" onDismiss={() => setSaved(false)} timeoutMs={6000} />
      ) : null}

      {open ? (
        <Sheet
          titleKey="checkin.title"
          subtitleKey="screen.disclaimer"
          onClose={close}
          footer={
            <>
              <Button variant="quiet" onClick={close}>
                {t("common.cancel")}
              </Button>
              <Button onClick={save} loading={saving}>
                {t("checkin.submit")}
              </Button>
            </>
          }
        >
          <div className="cmd-emoji" role="group" aria-label={t("checkin.title")}>
            {MOODS.map((m) => (
              <button
                key={m.value}
                type="button"
                aria-pressed={mood === m.value}
                className={`cmd-emoji__btn${mood === m.value ? " cmd-emoji__btn--on" : ""}`}
                onClick={() => {
                  setMood(m.value);
                  setError((e) => (e === "mood" ? null : e));
                }}
              >
                <span className="cmd-emoji__face" aria-hidden="true">
                  {m.face}
                </span>
                <span className="cmd-emoji__label">{t(`checkin.emoji.${m.value}`)}</span>
              </button>
            ))}
          </div>
          {error === "mood" ? (
            <p className="cmd-outofrange" role="alert">
              {t("checkin.error.mood")}
            </p>
          ) : null}

          <Slider
            labelKey="checkin.slider.label"
            value={heavy}
            min={0}
            max={10}
            step={1}
            disabled={saving}
            onChange={setHeavy}
          />

          {error === "save" ? (
            <p className="cmd-outofrange" role="alert">
              {t("common.error")}
            </p>
          ) : null}
        </Sheet>
      ) : null}
    </div>
  );
}
