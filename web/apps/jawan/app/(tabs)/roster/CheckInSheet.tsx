"use client";

import { useState } from "react";
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
 */
export function CheckInSheet({ onClose, onSaved }: Props) {
  const { t } = useT();
  const [mood, setMood] = useState<number | null>(null);
  const [slider, setSlider] = useState(5);
  const [note, setNote] = useState("");
  const [saving, setSaving] = useState(false);

  const localDate = new Date().toLocaleDateString("en-CA"); // YYYY-MM-DD local

  const save = async () => {
    if (mood === null || saving) return;
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
    <div className="sheet-backdrop" role="presentation" onMouseDown={onClose}>
      <div
        className="sheet"
        role="dialog"
        aria-modal="true"
        aria-label={t("checkin.title")}
        onMouseDown={(e) => e.stopPropagation()}
      >
        <h2 className="sheet__title">{t("checkin.title")}</h2>
        <p className="sheet__sub">{t("screen.disclaimer")}</p>

        <div className="emoji-row" role="radiogroup" aria-label={t("checkin.title")}>
          {EMOJI.map((face, i) => {
            const value = i + 1;
            const selected = mood === value;
            return (
              <button
                key={value}
                type="button"
                role="radio"
                aria-checked={selected}
                className={`emoji-btn${selected ? " emoji-btn--selected" : ""}`}
                onClick={() => setMood(value)}
              >
                <span aria-hidden="true">{face}</span>
                <span className="emoji-btn__label">{t(`checkin.emoji.${value}`)}</span>
              </button>
            );
          })}
        </div>

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
          <Button variant="quiet" onClick={onClose}>
            {t("common.cancel")}
          </Button>
          <Button onClick={save} disabled={mood === null} loading={saving}>
            {t("checkin.submit")}
          </Button>
        </div>
      </div>
    </div>
  );
}
