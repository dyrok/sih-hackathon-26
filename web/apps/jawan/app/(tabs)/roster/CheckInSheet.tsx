"use client";

import { useEffect, useRef, useState } from "react";
import { useT } from "@saarthi/i18n";
import { Button } from "@saarthi/ui";
import { enqueue, getClientUuid, notifyQueueChanged } from "@saarthi/sync";
import type { QueueItem } from "@saarthi/sync";

const EMOJI = ["😞", "😕", "😐", "🙂", "😄"] as const;

type Props = {
  onClose: () => void;
  onSaved: () => void;
};

/**
 * 10-second check-in sheet (F02): ≤3 taps — emoji → slider → save.
 * Writes to the local queue instantly; the network is never required (ADR-0005).
 * Native <dialog> + showModal() gives focus trap, inert background, Escape,
 * and focus restore on close for free.
 */
export function CheckInSheet({ onClose, onSaved }: Props) {
  const { t } = useT();
  const dialogRef = useRef<HTMLDialogElement>(null);
  const emojiGroupRef = useRef<HTMLDivElement>(null);
  const [mood, setMood] = useState<number | null>(null);
  const [slider, setSlider] = useState(5);
  const [note, setNote] = useState("");
  const [moodError, setMoodError] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const d = dialogRef.current;
    if (d && !d.open) d.showModal();
  }, []);

  const close = () => {
    const d = dialogRef.current;
    if (d && d.open) d.close();
    onClose();
  };

  const localDate = new Date().toLocaleDateString("en-CA"); // YYYY-MM-DD local

  const save = async () => {
    if (saving) return;
    if (mood === null) {
      setMoodError(true);
      emojiGroupRef.current?.querySelector("button")?.focus();
      return;
    }
    setMoodError(false);
    setSaving(true);
    try {
      const client_uuid = await getClientUuid();
      const item: QueueItem = {
        table: "checkin",
        client_uuid,
        captured_at: new Date().toISOString(),
        payload: {
          local_date: localDate,
          mood_emoji: mood,
          stress_slider: slider,
          ...(note.trim() ? { free_text: note.trim() } : {}),
        },
      };
      await enqueue(item);
      notifyQueueChanged();
      onSaved();
    } finally {
      setSaving(false);
    }
  };

  return (
    <dialog
      ref={dialogRef}
      className="sheet"
      aria-labelledby="checkin-sheet-title"
      onCancel={(e) => {
        e.preventDefault();
        close();
      }}
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) close();
      }}
    >
      <h2 className="sheet__title" id="checkin-sheet-title">
        {t("checkin.title")}
      </h2>
      <p className="sheet__sub">{t("screen.disclaimer")}</p>

      <div className="emoji-row" role="group" aria-label={t("checkin.title")} ref={emojiGroupRef}>
        {EMOJI.map((face, i) => {
          const value = i + 1;
          const selected = mood === value;
          return (
            <button
              key={value}
              type="button"
              aria-pressed={selected}
              className={`emoji-btn${selected ? " emoji-btn--selected" : ""}`}
              onClick={() => {
                setMood(value);
                setMoodError(false);
              }}
            >
              <span aria-hidden="true">{face}</span>
              <span className="emoji-btn__label">{t(`checkin.emoji.${value}`)}</span>
            </button>
          );
        })}
      </div>
      {moodError && (
        <p className="sheet__error" role="alert">
          {t("checkin.error.mood")}
        </p>
      )}

      <label className="slider-label" htmlFor="stress-slider">
        {t("checkin.slider.label")}
      </label>
      <div className="slider-row">
        <input
          id="stress-slider"
          className="slider-input"
          type="range"
          min={0}
          max={10}
          value={slider}
          onChange={(e) => setSlider(Number(e.target.value))}
        />
        <span className="slider-value" aria-hidden="true">
          {slider}
        </span>
      </div>

      <label className="field-label" htmlFor="checkin-note">
        {t("checkin.optional.label")}
      </label>
      <input
        id="checkin-note"
        className="field-input"
        value={note}
        placeholder={t("checkin.optional.placeholder")}
        onChange={(e) => setNote(e.target.value)}
      />

      <div className="sheet-actions">
        <Button variant="quiet" onClick={close}>
          {t("common.cancel")}
        </Button>
        <Button onClick={save} loading={saving}>
          {t("checkin.submit")}
        </Button>
      </div>
    </dialog>
  );
}
