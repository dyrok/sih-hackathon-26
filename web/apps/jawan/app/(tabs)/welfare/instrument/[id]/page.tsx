"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useT } from "@saarthi/i18n";
import { Button, ErrorState } from "@saarthi/ui";
import { AGREE5, BY_ID, needsSafetyProtocol, scoreInstrument } from "@saarthi/instruments";
import type { Item, Scale } from "@saarthi/instruments";
import { STORES, enqueue, get, newItemUuid, notifyQueueChanged, put } from "@saarthi/sync";
import { SubScreen } from "../../../../components/SubScreen";
import { localDate } from "../../../../lib/format";
import { drainNow } from "../../../../lib/sync";

type Draft = {
  instrument: string;
  answers: Record<string, number>;
  index: number;
  elapsedMs: number;
};

type Phase = "answering" | "saved" | "safety";

const DRAFT_PREFIX = "saarthi.instrument.draft.";

export default function InstrumentRunPage() {
  const { t, locale } = useT();
  const params = useParams<{ id: string }>();
  const rawId = params?.id;
  const id = typeof rawId === "string" ? decodeURIComponent(rawId) : "";
  const instrument = BY_ID[id];

  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [index, setIndex] = useState(0);
  const [phase, setPhase] = useState<Phase>("answering");
  const [missing, setMissing] = useState(false);
  const [restored, setRestored] = useState(false);
  const [contactSent, setContactSent] = useState(false);

  const elapsedRef = useRef(0);
  const tickRef = useRef(Date.now());
  const savedRef = useRef(false);

  const draftKey = `${DRAFT_PREFIX}${id}`;

  // Restore an interrupted run. F02 requires that an offline reload mid-flow
  // never loses answers, so the draft is written on every answer, not on exit.
  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const draft = await get<Draft>(STORES.meta, draftKey);
        if (!cancelled && draft && draft.instrument === id) {
          setAnswers(draft.answers);
          setIndex(draft.index);
          elapsedRef.current = draft.elapsedMs;
        }
      } catch {
        // No IndexedDB: the run still works, it just cannot survive a reload.
      }
      if (!cancelled) {
        tickRef.current = Date.now();
        setRestored(true);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [draftKey, id]);

  const persist = useCallback(
    (next: Draft) => {
      void put(STORES.meta, next, draftKey).catch(() => undefined);
    },
    [draftKey],
  );

  if (!instrument) {
    return (
      <SubScreen backHref="/welfare/instrument" titleKey="instrument.title">
        <ErrorState titleKey="error.404" bodyKey="instrument.subtitle" />
      </SubScreen>
    );
  }

  if (instrument.licence === "licence_pending" || instrument.items.length === 0) {
    return (
      <SubScreen backHref="/welfare/instrument" titleKey={instrument.nameKey}>
        <p className="screen-lead">{t("instrument.licencePending")}</p>
        <p className="footnote">{t("instrument.source", { source: instrument.source })}</p>
      </SubScreen>
    );
  }

  const questions: { item: Item; scale: Scale; validity: boolean }[] = [
    ...instrument.items.map((item) => ({ item, scale: instrument.scale, validity: false })),
    // The two social-desirability probes ride at the end on their own scale and
    // never enter the instrument total (clinical-instruments.md §4).
    ...instrument.validityItems.map((item) => ({ item, scale: AGREE5, validity: true })),
  ];
  const total = questions.length;
  const current = questions[Math.min(index, total - 1)];

  const answerCurrent = (value: number) => {
    if (!current) return;
    const now = Date.now();
    elapsedRef.current += now - tickRef.current;
    tickRef.current = now;
    const next = { ...answers, [current.item.id]: value };
    setAnswers(next);
    setMissing(false);
    persist({ instrument: id, answers: next, index, elapsedMs: elapsedRef.current });
  };

  const finish = async () => {
    if (savedRef.current) return;
    savedRef.current = true;
    const scored = scoreInstrument(id, answers, elapsedRef.current);
    await enqueue({
      table: "instrument",
      client_uuid: newItemUuid(),
      captured_at: new Date().toISOString(),
      payload: {
        instrument: scored.instrument,
        score: scored.score,
        ...(scored.item_9 !== undefined ? { item_9: scored.item_9 } : {}),
        validity_fail: scored.flags.validity_fail,
        straight_lining: scored.flags.straight_lining,
        too_fast: scored.flags.too_fast,
        all_max: scored.flags.all_max,
        recorded_at: localDate(),
      },
    });
    notifyQueueChanged();
    void put(STORES.meta, undefined, draftKey).catch(() => undefined);
    setPhase(needsSafetyProtocol(scored) ? "safety" : "saved");
  };

  const next = () => {
    if (!current) return;
    if (answers[current.item.id] === undefined) {
      setMissing(true);
      return;
    }
    const now = Date.now();
    elapsedRef.current += now - tickRef.current;
    tickRef.current = now;
    if (index + 1 >= total) {
      void finish();
      return;
    }
    const nextIndex = index + 1;
    setIndex(nextIndex);
    persist({ instrument: id, answers, index: nextIndex, elapsedMs: elapsedRef.current });
  };

  const back = () => {
    const prev = Math.max(0, index - 1);
    setIndex(prev);
    setMissing(false);
    persist({ instrument: id, answers, index: prev, elapsedMs: elapsedRef.current });
  };

  // The safety protocol is not a screen the person can tab past: it replaces
  // the flow entirely and offers a human on the other end, now.
  if (phase === "safety") {
    return (
      <section className="safety" aria-live="assertive">
        <h1 className="safety__title">{t("instrument.safety.title")}</h1>
        <p className="safety__body">{t("instrument.safety.body")}</p>
        <a className="safety__call" href="tel:14416">
          {t("instrument.safety.call")}
        </a>
        <Button
          variant="secondary"
          disabled={contactSent}
          onClick={() => {
            setContactSent(true);
            // The queued row already carries the item that routes the human
            // protocol server-side; this asks the outbox to send it now instead
            // of waiting for the next opportunistic drain.
            void drainNow().catch(() => undefined);
          }}
        >
          {t("instrument.safety.counsellor")}
        </Button>
        {contactSent ? (
          <p className="safety__saved" role="status">
            {t("instrument.saved")}
          </p>
        ) : null}
        <p className="safety__helpline">{t("settings.helpline")}</p>
      </section>
    );
  }

  if (phase === "saved") {
    return (
      <SubScreen backHref="/welfare/instrument" titleKey={instrument.nameKey}>
        <p className="screen-lead">{t("instrument.saved")}</p>
        {/* No band, no score, ever — the person's own trend is the feedback. */}
        <p className="footnote">{t("instrument.noBand")}</p>
        <Link className="hub-row" href="/welfare/trend">
          <span className="hub-row__text">
            <span className="hub-row__label">{t("trend.title")}</span>
            <span className="hub-row__detail">{t("trend.ownonly")}</span>
          </span>
        </Link>
      </SubScreen>
    );
  }

  if (!restored || !current) return null;

  const answered = answers[current.item.id];
  const stem = locale === "hi" ? current.item.hi : current.item.en;

  return (
    <div className="instrument-run">
      <Link className="subscreen__back" href="/welfare/instrument">
        {t("instrument.exit")}
      </Link>

      <p className="instrument-run__progress">{t("instrument.progress", { n: index + 1, total })}</p>
      <ol className="progress-dots" aria-hidden="true">
        {questions.map((q, i) => (
          <li
            key={q.item.id}
            className={`progress-dot${i === index ? " progress-dot--current" : ""}${
              answers[q.item.id] !== undefined ? " progress-dot--done" : ""
            }`}
          />
        ))}
      </ol>

      <p className="instrument-run__window">
        {current.validity ? t("instrument.validity.note") : t(instrument.windowKey)}
      </p>
      <h1 className="instrument-run__stem">{stem}</h1>

      <div className="option-list" role="radiogroup" aria-label={stem}>
        {current.scale.options.map((option) => {
          const selected = answered === option.value;
          return (
            <label className={`option${selected ? " option--selected" : ""}`} key={option.value}>
              <input
                className="option__input"
                type="radio"
                name={`q-${current.item.id}`}
                value={option.value}
                checked={selected}
                onChange={() => answerCurrent(option.value)}
              />
              <span className="option__label">{t(option.labelKey)}</span>
            </label>
          );
        })}
      </div>

      {missing ? (
        <p className="sheet__error" role="alert">
          {t("instrument.answerRequired")}
        </p>
      ) : null}

      <div className="instrument-run__actions">
        <Button variant="quiet" onClick={back} disabled={index === 0}>
          {t("common.back")}
        </Button>
        <Button onClick={next}>{index + 1 >= total ? t("instrument.submit") : t("common.next")}</Button>
      </div>

      <p className="footnote">{t("screen.disclaimer")}</p>
      <p className="footnote">{t("instrument.exitConfirm")}</p>
    </div>
  );
}
