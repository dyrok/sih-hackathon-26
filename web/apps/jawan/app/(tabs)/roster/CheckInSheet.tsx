"use client";

import { useEffect, useRef, useState } from "react";
import { useT } from "@saarthi/i18n";
import { Button } from "@saarthi/ui";
import { enqueue, getClientUuid, notifyQueueChanged } from "@saarthi/sync";
import type { QueueItem } from "@saarthi/sync";
import { grantConsent, toCheckInWire } from "@saarthi/api";

const EMOJI = ["😞", "😕", "😐", "🙂", "😄"] as const;
const CONSENTED_KEY = "saarthi.consented.checkin";

type Props = {
  onClose: () => void;
  onSaved: () => void;
};

/**
 * 10-second check-in sheet (F02): ≤3 taps — emoji → slider → save.
 * Writes to the local queue instantly; the network is never required (ADR-0005).
 * First save grants the checkin consent bundle explicitly (checkbox) — consent
 * is never granted silently.
 * Native <dialog> + showModal() gives focus trap, inert background, Escape,
 * and focus restore on close for free.
 */
export function CheckInSheet({ onClose, onSaved }: Props) {
  const { t, locale } = useT();
  const dialogRef = useRef<HTMLDialogElement>(null);
  const emojiGroupRef = useRef<HTMLDivElement>(null);
  const [mood, setMood] = useState<number | null>(null);
  const [slider, setSlider] = useState(5);
  const [note, setNote] = useState("");
  const [agreed, setAgreed] = useState(() => localStorage.getItem(CONSENTED_KEY) === "1");
  const [error, setError] = useState<string | null>(null);
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
      setError("mood");
      emojiGroupRef.current?.querySelector("button")?.focus();
      return;
    }
    if (!agreed) {
      setError("consent");
      return;
    }
    setError(null);
    setSaving(true);
    try {
      const client_uuid = await getClientUuid();
      const wire = toCheckInWire(mood, slider, localDate);

      // Consent first (kv's API is consent-gated). Online: grant now.
      // Offline: queue the grant so it syncs before the check-in (FIFO).
      if (!localStorage.getItem(CONSENTED_KEY)) {
        const consentWire = {
          bundle_id: "checkin" as const,
          purpose_string: t("consent.scope.checkin"),
          data_categories: ["checkin", "sleep", "instruments"],
          language: locale,
        };
        try {
          await grantConsent(consentWire);
        } catch {
          await enqueue({ table: "consent", client_uuid, captured_at: new Date().toISOString(), payload: consentWire });
        }
        localStorage.setItem(CONSENTED_KEY, "1");
      }

      const item: QueueItem = {
        table: "checkin",
        client_uuid,
        captured_at: new Date().toISOString(),
        payload: {
          ...wire,
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
                setError((e) => (e === "mood" ? null : e));
              }}
            >
              <span aria-hidden="true">{face}</span>
              <span className="emoji-btn__label">{t(`checkin.emoji.${value}`)}</span>
            </button>
          );
        })}
      </div>
      {error === "mood" && (
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

      <label className="consent-check">
        <input
          type="checkbox"
          checked={agreed}
          onChange={(e) => {
            setAgreed(e.target.checked);
            setError((err) => (err === "consent" ? null : err));
          }}
        />
        <span>{t("consent.checkin.agree")}</span>
      </label>
      {error === "consent" && (
        <p className="sheet__error" role="alert">
          {t("consent.checkin.error")}
        </p>
      )}

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
