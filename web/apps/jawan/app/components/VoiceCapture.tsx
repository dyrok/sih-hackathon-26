"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useT } from "@saarthi/i18n";
import { Button, IconMic, IconMicOff } from "@saarthi/ui";
import { enqueue, newItemUuid, notifyQueueChanged } from "@saarthi/sync";
import { localDate } from "../lib/format";

/**
 * VOICE CAPTURE — APP-006 / F03 screen 1.
 *
 * The architectural claim this component has to make true: **only numbers leave
 * the device.** So there is no MediaRecorder, no Blob, no object URL, no File
 * and no audio buffer that outlives a single analyser frame anywhere in this
 * file. What is kept between frames is a per-frame envelope (timestamp, RMS,
 * dB, an f0 estimate) — a ~30 Hz numeric stream from which no speech, and no
 * speaker, can be reconstructed. That envelope is reduced to one feature vector
 * on stop and then dropped with the component.
 *
 * The extractors below are deliberate APPROXIMATIONS of the F03 feature table,
 * computed with what a browser can do cheaply on a 2 GB phone:
 *   - f0        : decimated time-domain autocorrelation, 70-350 Hz search
 *   - jitter    : mean absolute period difference between adjacent voiced frames
 *   - shimmer   : mean absolute dB difference between adjacent voiced frames
 *   - loudness  : variance of frame dB over voiced frames
 *   - pauses    : unvoiced runs of 250 ms or more, interior to the utterance
 *   - rate      : syllable-nucleus peaks in the dB envelope per second
 * They are not a validated prosody model (ADR-0002 weights voice low for
 * exactly this reason). Swapping in a real extractor changes this file only —
 * the wire contract is `model_version` + `schema_version`.
 */

type Prosody = {
  f0_mean: number;
  f0_sd: number;
  speech_rate: number;
  pause_count: number;
  pause_total: number;
  voiced_ratio: number;
  loudness_var: number;
  jitter: number;
  shimmer: number;
  duration_s: number;
  model_version: string;
  schema_version: string;
};

type Phase = "idle" | "unsupported" | "denied" | "recording" | "ready" | "tooShort" | "saved";

/** Server contract: 5 s minimum, 30 s maximum (self_service._apply_voice). */
const MIN_SECONDS = 5;
const MAX_SECONDS = 30;
/** Below this frame RMS there is no voice worth measuring. */
const VOICED_RMS = 0.012;
/** An unvoiced run at or above this is a pause, not a gap between syllables. */
const PAUSE_MS = 250;

type Frames = { t: number[]; db: number[]; f0: number[] };

function mean(values: number[]): number {
  if (values.length === 0) return 0;
  let sum = 0;
  for (const v of values) sum += v;
  return sum / values.length;
}

function variance(values: number[]): number {
  if (values.length < 2) return 0;
  const m = mean(values);
  let acc = 0;
  for (const v of values) acc += (v - m) * (v - m);
  return acc / (values.length - 1);
}

/** Average every 4 samples — cheap anti-alias before autocorrelation. */
function decimate(buf: Float32Array, factor: number): Float32Array {
  const out = new Float32Array(Math.floor(buf.length / factor));
  for (let i = 0; i < out.length; i += 1) {
    let acc = 0;
    for (let k = 0; k < factor; k += 1) acc += buf[i * factor + k] ?? 0;
    out[i] = acc / factor;
  }
  return out;
}

/** Normalised autocorrelation pitch estimate. Returns 0 when unvoiced. */
function estimateF0(buf: Float32Array, sampleRate: number): number {
  const factor = 4;
  const x = decimate(buf, factor);
  const rate = sampleRate / factor;
  const minLag = Math.max(2, Math.floor(rate / 350));
  const maxLag = Math.min(x.length - 1, Math.floor(rate / 70));
  if (maxLag <= minLag) return 0;

  let energy = 0;
  for (let i = 0; i < x.length; i += 1) energy += (x[i] ?? 0) * (x[i] ?? 0);
  if (energy <= 0) return 0;

  let bestLag = 0;
  let bestCorr = 0;
  for (let lag = minLag; lag <= maxLag; lag += 1) {
    let corr = 0;
    for (let i = 0; i + lag < x.length; i += 1) corr += (x[i] ?? 0) * (x[i + lag] ?? 0);
    if (corr > bestCorr) {
      bestCorr = corr;
      bestLag = lag;
    }
  }
  // A weak best peak means noise, not a period.
  if (bestLag === 0 || bestCorr / energy < 0.3) return 0;
  return rate / bestLag;
}

/** Syllable nuclei: peaks in the smoothed dB envelope, 120 ms apart minimum. */
function countNuclei(frames: Frames): number {
  const n = frames.db.length;
  if (n < 3) return 0;
  const smooth: number[] = [];
  for (let i = 0; i < n; i += 1) {
    const a = frames.db[Math.max(0, i - 1)] ?? 0;
    const b = frames.db[i] ?? 0;
    const c = frames.db[Math.min(n - 1, i + 1)] ?? 0;
    smooth.push((a + b + c) / 3);
  }
  const peak = Math.max(...smooth);
  const floorDb = mean(smooth);
  const threshold = Math.max(floorDb + 2, peak - 12);
  let count = 0;
  let lastAt = -Infinity;
  for (let i = 1; i < n - 1; i += 1) {
    const value = smooth[i] ?? 0;
    const at = frames.t[i] ?? 0;
    if (value < threshold) continue;
    if (value < (smooth[i - 1] ?? 0) || value < (smooth[i + 1] ?? 0)) continue;
    if (at - lastAt < 120) continue;
    count += 1;
    lastAt = at;
  }
  return count;
}

function reduceToVector(frames: Frames): Prosody {
  const total = frames.t.length;
  const first = frames.t[0] ?? 0;
  const last = frames.t[total - 1] ?? first;
  const duration = Math.max(0, (last - first) / 1000);

  const voicedF0: number[] = [];
  const voicedDb: number[] = [];
  const periodDiffs: number[] = [];
  const dbDiffs: number[] = [];
  let voicedFrames = 0;
  let previousPeriod: number | null = null;
  let previousDb: number | null = null;

  let pauseCount = 0;
  let pauseTotal = 0;
  let runStart: number | null = null;
  let heardVoice = false;

  for (let i = 0; i < total; i += 1) {
    const f0 = frames.f0[i] ?? 0;
    const db = frames.db[i] ?? 0;
    const at = frames.t[i] ?? 0;
    const voiced = f0 > 0;

    if (voiced) {
      voicedFrames += 1;
      voicedF0.push(f0);
      voicedDb.push(db);
      const period = 1 / f0;
      if (previousPeriod !== null) periodDiffs.push(Math.abs(period - previousPeriod));
      if (previousDb !== null) dbDiffs.push(Math.abs(db - previousDb));
      previousPeriod = period;
      previousDb = db;

      // An interior silence that has just ended is a pause.
      if (runStart !== null && heardVoice) {
        const length = at - runStart;
        if (length >= PAUSE_MS) {
          pauseCount += 1;
          pauseTotal += length / 1000;
        }
      }
      runStart = null;
      heardVoice = true;
    } else {
      previousPeriod = null;
      previousDb = null;
      if (runStart === null) runStart = at;
    }
  }

  const meanPeriod = voicedF0.length > 0 ? mean(voicedF0.map((f) => 1 / f)) : 0;

  return {
    f0_mean: Number(mean(voicedF0).toFixed(2)),
    f0_sd: Number(Math.sqrt(variance(voicedF0)).toFixed(2)),
    speech_rate: duration > 0 ? Number((countNuclei(frames) / duration).toFixed(2)) : 0,
    pause_count: pauseCount,
    pause_total: Number(pauseTotal.toFixed(2)),
    voiced_ratio: total > 0 ? Number((voicedFrames / total).toFixed(3)) : 0,
    loudness_var: Number(variance(voicedDb).toFixed(2)),
    jitter: meanPeriod > 0 ? Number(((mean(periodDiffs) / meanPeriod) * 100).toFixed(2)) : 0,
    shimmer: Number(mean(dbDiffs).toFixed(2)),
    duration_s: Number(duration.toFixed(1)),
    model_version: "web-prosody-v1",
    schema_version: "v1",
  };
}

type Props = {
  /** The `voice` consent bundle. Nothing here runs without it. */
  granted: boolean;
};

export function VoiceCapture({ granted }: Props) {
  const { t } = useT();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const contextRef = useRef<AudioContext | null>(null);
  const rafRef = useRef<number | null>(null);
  const framesRef = useRef<Frames>({ t: [], db: [], f0: [] });

  const [phase, setPhase] = useState<Phase>("idle");
  const [seconds, setSeconds] = useState(0);
  const [vector, setVector] = useState<Prosody | null>(null);

  const releaseHardware = useCallback(() => {
    if (rafRef.current !== null) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }
    // Releasing the tracks is what turns the OS recording indicator off. It is
    // done on stop, on discard, on error and on unmount — never conditionally.
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    void contextRef.current?.close().catch(() => undefined);
    contextRef.current = null;
  }, []);

  useEffect(() => releaseHardware, [releaseHardware]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const media = navigator.mediaDevices;
    const hasAudioContext = "AudioContext" in window;
    if (!media || typeof media.getUserMedia !== "function" || !hasAudioContext) {
      setPhase("unsupported");
    }
  }, []);

  const stop = useCallback(() => {
    const frames = framesRef.current;
    releaseHardware();
    const result = reduceToVector(frames);
    // The envelope has done its job; drop it before anything else can read it.
    framesRef.current = { t: [], db: [], f0: [] };
    if (result.duration_s < MIN_SECONDS) {
      setVector(null);
      setPhase("tooShort");
      return;
    }
    setVector(result);
    setPhase("ready");
  }, [releaseHardware]);

  const start = useCallback(async () => {
    setVector(null);
    setSeconds(0);
    framesRef.current = { t: [], db: [], f0: [] };
    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      setPhase("denied");
      return;
    }
    streamRef.current = stream;

    const context = new AudioContext();
    contextRef.current = context;
    const source = context.createMediaStreamSource(stream);
    const analyser = context.createAnalyser();
    analyser.fftSize = 2048;
    analyser.smoothingTimeConstant = 0;
    source.connect(analyser);
    // Deliberately NOT connected to context.destination: no playback path.

    const samples = new Float32Array(analyser.fftSize);
    const wave = new Uint8Array(analyser.fftSize);
    const started = performance.now();
    setPhase("recording");

    const olive =
      getComputedStyle(document.documentElement).getPropertyValue("--sa-color-brand-olive").trim() ||
      "currentColor";

    const tick = () => {
      const now = performance.now();
      const elapsed = (now - started) / 1000;

      analyser.getFloatTimeDomainData(samples);
      let sumSquares = 0;
      for (let i = 0; i < samples.length; i += 1) {
        const value = samples[i] ?? 0;
        sumSquares += value * value;
      }
      const rms = Math.sqrt(sumSquares / samples.length);
      const db = 20 * Math.log10(Math.max(rms, 1e-8));
      const f0 = rms > VOICED_RMS ? estimateF0(samples, context.sampleRate) : 0;

      const frames = framesRef.current;
      frames.t.push(now);
      frames.db.push(db);
      frames.f0.push(f0);

      // Live waveform. The sample window is drawn and then overwritten on the
      // next frame; nothing is retained.
      const canvas = canvasRef.current;
      if (canvas) {
        analyser.getByteTimeDomainData(wave);
        const ctx2d = canvas.getContext("2d");
        if (ctx2d) {
          const dpr = window.devicePixelRatio || 1;
          const width = canvas.clientWidth * dpr;
          const height = canvas.clientHeight * dpr;
          if (canvas.width !== width || canvas.height !== height) {
            canvas.width = width;
            canvas.height = height;
          }
          ctx2d.clearRect(0, 0, canvas.width, canvas.height);
          ctx2d.lineWidth = 2 * dpr;
          ctx2d.strokeStyle = olive;
          ctx2d.beginPath();
          const step = canvas.width / wave.length;
          for (let i = 0; i < wave.length; i += 1) {
            const v = ((wave[i] ?? 128) - 128) / 128;
            const y = canvas.height / 2 + v * (canvas.height / 2) * 0.9;
            if (i === 0) ctx2d.moveTo(0, y);
            else ctx2d.lineTo(i * step, y);
          }
          ctx2d.stroke();
        }
      }

      setSeconds(Math.floor(elapsed));
      if (elapsed >= MAX_SECONDS) {
        stop();
        return;
      }
      rafRef.current = requestAnimationFrame(tick);
    };

    rafRef.current = requestAnimationFrame(tick);
  }, [stop]);

  const discard = useCallback(() => {
    setVector(null);
    setSeconds(0);
    setPhase("idle");
  }, []);

  const keep = useCallback(async () => {
    if (!vector) return;
    await enqueue({
      table: "voice",
      client_uuid: newItemUuid(),
      captured_at: new Date().toISOString(),
      payload: { ...vector, recorded_at: localDate() },
    });
    notifyQueueChanged();
    setVector(null);
    setPhase("saved");
  }, [vector]);

  if (!granted) {
    return (
      <div className="voice voice--gated">
        <p className="voice__note">{t("consent.needed")}</p>
        <Link className="voice__link" href="/me/consent">
          {t("consent.turnOn")}
        </Link>
      </div>
    );
  }

  if (phase === "unsupported") {
    return (
      <p className="voice__note" role="status">
        <IconMicOff width={18} height={18} />
        {t("voice.unsupported")}
      </p>
    );
  }

  return (
    <div className="voice">
      {phase === "idle" || phase === "denied" || phase === "tooShort" || phase === "saved" ? (
        <Button variant="secondary" onClick={() => void start()}>
          <IconMic width={18} height={18} />
          {phase === "idle" || phase === "saved" ? t("voice.start") : t("voice.rerecord")}
        </Button>
      ) : null}

      {phase === "denied" ? (
        <p className="voice__note" role="alert">
          {t("voice.denied")}
        </p>
      ) : null}
      {phase === "tooShort" ? (
        <p className="voice__note" role="alert">
          {t("voice.tooShort")}
        </p>
      ) : null}
      {phase === "saved" ? (
        <p className="voice__note" role="status">
          {t("voice.saved")}
        </p>
      ) : null}

      {phase === "recording" ? (
        <div className="voice__live">
          <p className="voice__privacy">{t("voice.privacy.line")}</p>
          <p className="voice__explain">{t("voice.explain")}</p>
          <canvas className="voice__canvas" ref={canvasRef} aria-hidden="true" />
          <p className="voice__status" role="status">
            {t("voice.analysing")}
            <span className="voice__seconds">{seconds}</span>
          </p>
          <Button variant="secondary" onClick={stop}>
            {t("voice.stop")}
          </Button>
        </div>
      ) : null}

      {phase === "ready" && vector ? (
        <div className="voice__review">
          <p className="voice__privacy">{t("voice.privacy.line")}</p>
          <p className="voice__explain">{t("voice.explain")}</p>
          <div className="voice__actions">
            <Button variant="secondary" onClick={() => void keep()}>
              {t("voice.keep")}
            </Button>
            <Button variant="quiet" onClick={discard}>
              {t("voice.discard")}
            </Button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
