"use client";

import { useEffect, useRef, useState } from "react";
import { useT } from "@saarthi/i18n";
import { Button, IconMic, IconMicOff, Skeleton, Toast, useApi } from "@saarthi/ui";
import { getOwnSitreps, submitOwnSitrep } from "@saarthi/api/commander";
import type { Sitrep } from "@saarthi/api/commander";
import { ScreenHead } from "../parts";

/**
 * Officer duty sitrep — talk the day in, get a work report.
 *
 * Follow-up questions look like log-completing details. Tone/mood is a
 * private heuristic on the same utterance and is never sent to the unit
 * overview (ADR-0003). This is a demo larp, labelled as such on screen.
 */

const SAMPLE =
  "Morning inspection of the lines at 0530. Parade and PT until 0700, all present. Two sections on the eastern fence from 0900 to 1400, no incident. Afternoon I sat with the JCOs on the leave backlog — six applications still pending. Evening briefing at 1800, night picquet rota posted. Long day. Voice is going. Will walk the perimeter once more at 2100.";

const QUESTION_KEYS: Record<string, string> = {
  hours: "sitrep.q.hours",
  sleep: "sitrep.q.sleep",
  incident: "sitrep.q.incident",
  leave: "sitrep.q.leave",
  tomorrow: "sitrep.q.tomorrow",
};

type Phase = "idle" | "recording" | "questions" | "saving" | "done";

function pickQuestionIds(text: string): string[] {
  const blob = text.toLowerCase();
  const out: string[] = [];
  const rules: [string, string[]][] = [
    ["hours", ["long", "hours", "duty", "picquet", "perimeter"]],
    ["sleep", ["tired", "voice", "night", "long", "exhausted"]],
    ["incident", ["incident", "firing", "casualty", "contact"]],
    ["leave", ["leave", "chhutti", "backlog"]],
  ];
  for (const [id, words] of rules) {
    if (out.length >= 2) break;
    if (words.some((w) => blob.includes(w))) out.push(id);
  }
  if (out.length < 2) out.push("tomorrow");
  return out.slice(0, 2);
}

function mean(values: number[]): number {
  if (!values.length) return 0;
  return values.reduce((a, b) => a + b, 0) / values.length;
}

function variance(values: number[]): number {
  if (values.length < 2) return 0;
  const m = mean(values);
  return values.reduce((a, v) => a + (v - m) * (v - m), 0) / (values.length - 1);
}

export default function SitrepPage() {
  const { t } = useT();
  const history = useApi(() => getOwnSitreps(14), [], { cacheKey: "commander.own.sitreps" });

  const [phase, setPhase] = useState<Phase>("idle");
  const [live, setLive] = useState("");
  const [finalText, setFinalText] = useState("");
  const [questionIds, setQuestionIds] = useState<string[]>([]);
  const [qIndex, setQIndex] = useState(0);
  const [answer, setAnswer] = useState("");
  const [answers, setAnswers] = useState<{ id: string; answer: string }[]>([]);
  const [report, setReport] = useState<Sitrep | null>(null);
  const [error, setError] = useState(false);
  const [micDenied, setMicDenied] = useState(false);

  const recRef = useRef<{ stop: () => void } | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const rmsRef = useRef<number[]>([]);
  const startedAt = useRef(0);

  useEffect(() => {
    return () => {
      recRef.current?.stop();
      streamRef.current?.getTracks().forEach((tr) => tr.stop());
    };
  }, []);

  const finishTranscript = (text: string, rms: number[]) => {
    const cleaned = text.replace(/\s+/g, " ").trim();
    if (cleaned.length < 8) {
      setError(true);
      setPhase("idle");
      return;
    }
    setFinalText(cleaned);
    setQuestionIds(pickQuestionIds(cleaned));
    setQIndex(0);
    setAnswer("");
    setAnswers([]);
    setPhase("questions");
    rmsRef.current = rms;
  };

  const startMic = async () => {
    setError(false);
    setLive("");
    setReport(null);
    rmsRef.current = [];
    startedAt.current = Date.now();

    const w = window as unknown as {
      SpeechRecognition?: new () => SpeechRec;
      webkitSpeechRecognition?: new () => SpeechRec;
    };
    const Ctor = w.SpeechRecognition || w.webkitSpeechRecognition;
    if (!Ctor) {
      setMicDenied(true);
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const ctx = new AudioContext();
      const src = ctx.createMediaStreamSource(stream);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 512;
      src.connect(analyser);
      const buf = new Float32Array(analyser.fftSize);
      let raf = 0;
      const tick = () => {
        analyser.getFloatTimeDomainData(buf);
        let acc = 0;
        for (let i = 0; i < buf.length; i += 1) {
          const sample = buf[i] ?? 0;
          acc += sample * sample;
        }
        rmsRef.current.push(Math.sqrt(acc / buf.length));
        raf = requestAnimationFrame(tick);
      };
      raf = requestAnimationFrame(tick);

      const rec = new Ctor();
      rec.continuous = true;
      rec.interimResults = true;
      rec.lang = "en-IN";
      let committed = "";
      rec.onresult = (ev: SpeechEvent) => {
        let interim = "";
        for (let i = ev.resultIndex; i < ev.results.length; i += 1) {
          const res = ev.results[i];
          if (!res) continue;
          const piece = res[0]?.transcript ?? "";
          if (res.isFinal) committed += `${piece} `;
          else interim += piece;
        }
        setLive(`${committed}${interim}`.trim());
      };
      rec.onerror = () => setMicDenied(true);
      rec.start();
      recRef.current = {
        stop: () => {
          cancelAnimationFrame(raf);
          rec.stop();
          stream.getTracks().forEach((tr) => tr.stop());
          ctx.close();
        },
      };
      setPhase("recording");
    } catch {
      setMicDenied(true);
    }
  };

  const stopMic = () => {
    recRef.current?.stop();
    recRef.current = null;
    const text = live;
    const rms = rmsRef.current.slice();
    finishTranscript(text, rms);
  };

  const useSample = () => {
    setLive(SAMPLE);
    setMicDenied(false);
    finishTranscript(SAMPLE, [0.03, 0.04, 0.02, 0.05, 0.06]);
  };

  const submitAnswers = async (all: { id: string; answer: string }[]) => {
    setPhase("saving");
    setError(false);
    const rms = rmsRef.current;
    try {
      const saved = await submitOwnSitrep({
        transcript: finalText,
        duration_s: Math.max(1, (Date.now() - startedAt.current) / 1000),
        rms_mean: mean(rms) || 0.03,
        rms_var: variance(rms) || 0.005,
        answers: all,
      });
      setReport(saved);
      setPhase("done");
      history.reload();
    } catch {
      setError(true);
      setPhase("questions");
    }
  };

  const nextQuestion = () => {
    const id = questionIds[qIndex];
    if (!id) return;
    const next = [...answers, { id, answer: answer.trim() || "—" }];
    setAnswers(next);
    setAnswer("");
    if (qIndex + 1 >= questionIds.length) {
      void submitAnswers(next);
    } else {
      setQIndex(qIndex + 1);
    }
  };

  const rows = history.data?.sitreps ?? [];

  return (
    <div className="cmd-sitrep">
      <ScreenHead titleKey="sitrep.title" guideKey="sitrep.guide" />

      {phase === "idle" || phase === "recording" ? (
        <section className="cmd-sitrep__capture">
          <p className="cmd-sitrep__live" aria-live="polite">
            {live || t(phase === "recording" ? "sitrep.listening" : "sitrep.prompt")}
          </p>
          <div className="cmd-sitrep__actions">
            {phase === "idle" ? (
              <Button onClick={() => void startMic()}>
                <IconMic /> {t("sitrep.mic")}
              </Button>
            ) : (
              <Button onClick={stopMic}>
                <IconMicOff /> {t("sitrep.stop")}
              </Button>
            )}
            <Button variant="secondary" onClick={useSample} disabled={phase === "recording"}>
              {t("sitrep.sample")}
            </Button>
          </div>
          {micDenied ? <p className="cmd-sitrep__hint">{t("sitrep.micDenied")}</p> : null}
        </section>
      ) : null}

      {phase === "questions" ? (
        <section className="cmd-sitrep__q">
          <p className="cmd-sitrep__q-kicker">{t("sitrep.q.kicker")}</p>
          <p className="cmd-sitrep__q-ask">
            {t(QUESTION_KEYS[questionIds[qIndex] ?? "tomorrow"] ?? "sitrep.q.tomorrow")}
          </p>
          <textarea
            className="sa-input cmd-sitrep__answer"
            rows={3}
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
          />
          <Button onClick={nextQuestion}>{t("common.next")}</Button>
        </section>
      ) : null}

      {phase === "saving" ? <Skeleton lines={4} /> : null}

      {phase === "done" && report ? (
        <div className="cmd-sitrep__reports">
          <article className="cmd-sitrep__card">
            <h2>{t("sitrep.work.title")}</h2>
            <p>{report.work_summary}</p>
            <ul>
              {report.work_bullets.map((b) => (
                <li key={b}>{b}</li>
              ))}
            </ul>
          </article>
          <article className="cmd-sitrep__card cmd-sitrep__card--private">
            <h2>{t("sitrep.well.title")}</h2>
            <p className="cmd-sitrep__private">{t("sitrep.well.private")}</p>
            <p>
              {t("sitrep.well.tone")}: {t(`sitrep.tone.${report.tone_label}`)}
            </p>
            <p>
              {t("sitrep.well.mood")}: {t(`sitrep.mood.${report.mood_label}`)}
            </p>
            <p>{report.wellness_summary}</p>
            <p className="cmd-sitrep__hint">{t("sitrep.well.heuristic")}</p>
          </article>
          <Button variant="secondary" onClick={() => { setPhase("idle"); setLive(""); setReport(null); }}>
            {t("sitrep.another")}
          </Button>
        </div>
      ) : null}

      {error ? <Toast messageKey="common.error" onDismiss={() => setError(false)} timeoutMs={4000} /> : null}

      <section className="cmd-sitrep__history">
        <h2>{t("sitrep.history")}</h2>
        {history.loading && !rows.length ? <Skeleton /> : null}
        {!history.loading && !rows.length ? <p>{t("common.empty")}</p> : null}
        <ol className="cmd-sitrep__list">
          {rows.map((row) => (
            <li key={row.id}>
              <strong>{row.duty_date}</strong>
              <span>{row.work_summary}</span>
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}

type SpeechRec = {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onresult: ((ev: SpeechEvent) => void) | null;
  onerror: (() => void) | null;
  start: () => void;
  stop: () => void;
};

type SpeechEvent = {
  resultIndex: number;
  results: { length: number; [i: number]: { isFinal: boolean; [j: number]: { transcript: string } } };
};
