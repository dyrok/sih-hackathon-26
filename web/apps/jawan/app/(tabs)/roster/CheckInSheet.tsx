"use client";

import { useRef, useState } from "react";
import { useT } from "@saarthi/i18n";
import { Button, Checkbox, Field, Sheet, Slider, TextArea, TextInput, useApi } from "@saarthi/ui";
import { enqueue, newItemUuid, notifyQueueChanged } from "@saarthi/sync";
import { getConsent, grantConsent, toCheckInWire } from "@saarthi/api/jawan";
import type { ConsentWire } from "@saarthi/api/jawan";
import { CACHE } from "../../lib/cache";
import { localDate } from "../../lib/format";
import { VoiceCapture } from "../../components/VoiceCapture";

const EMOJI = ["\u{1F61E}", "\u{1F615}", "\u{1F610}", "\u{1F642}", "\u{1F604}"] as const;
/** Offline memory of a grant that is still sitting in the outbox. */
const CONSENTED_KEY = "saarthi.consented.checkin";

type Props = {
  onClose: () => void;
  /** The queue row id, so the caller can offer an undo instead of a confirm. */
  onSaved: (queueId: number) => void;
};

function localFlag(key: string): boolean {
  try {
    return localStorage.getItem(key) === "1";
  } catch {
    return false;
  }
}

/**
 * The 10-second check-in (F02 screen 2): emoji → save is two taps; everything
 * else on the sheet is optional. It writes to the local outbox and returns —
 * the network is never on the path (ADR-0005), and the confirmation is an undo
 * bar on the home screen rather than a modal asking "are you sure" (design.md
 * §6: undo beats confirm).
 */
export function CheckInSheet({ onClose, onSaved }: Props) {
  const { t, locale } = useT();
  const emojiGroupRef = useRef<HTMLDivElement>(null);
  const [mood, setMood] = useState<number | null>(null);
  const [slider, setSlider] = useState(5);
  const [sleep, setSleep] = useState("");
  const [note, setNote] = useState("");
  const [agreed, setAgreed] = useState(() => localFlag(CONSENTED_KEY));
  const [error, setError] = useState<"mood" | "consent" | null>(null);
  const [saving, setSaving] = useState(false);

  // Cached so the sheet knows the consent state on a cold offline open.
  const { data: consent } = useApi(getConsent, [], { cacheKey: CACHE.consent });
  const bundle = (id: string) => consent?.bundles.find((b) => b.bundle_id === id);
  const checkinGranted = bundle("checkin")?.granted ?? localFlag(CONSENTED_KEY);
  const voiceGranted = bundle("voice")?.granted ?? false;

  const sleepHours = (() => {
    const value = Number.parseFloat(sleep);
    return Number.isFinite(value) && value >= 0 && value <= 16 ? value : undefined;
  })();

  const save = async () => {
    if (saving) return;
    if (mood === null) {
      setError("mood");
      emojiGroupRef.current?.querySelector("button")?.focus();
      return;
    }
    if (!checkinGranted && !agreed) {
      setError("consent");
      return;
    }
    setError(null);
    setSaving(true);
    try {
      if (!checkinGranted) {
        const wire: ConsentWire = {
          bundle_id: "checkin",
          purpose_string: t("consent.purpose.checkin"),
          data_categories: ["mood", "stress_slider", "free_text", "sleep_hours"],
          language: locale,
        };
        try {
          await grantConsent(wire);
        } catch {
          // Offline: the grant queues ahead of the check-in, so the server sees
          // consent before the row it gates (FIFO drain).
          await enqueue({
            table: "consent",
            client_uuid: newItemUuid(),
            captured_at: new Date().toISOString(),
            payload: { ...wire },
          });
        }
        try {
          localStorage.setItem(CONSENTED_KEY, "1");
        } catch {
          /* private mode: the server copy is still authoritative */
        }
      }

      const payload = toCheckInWire(mood, slider, localDate(), {
        ...(sleepHours !== undefined ? { sleep_hours: sleepHours } : {}),
        ...(note.trim() ? { free_text: note.trim() } : {}),
      });

      // A fresh uuid PER ITEM. Reusing the device uuid would make the server
      // treat a second check-in as a retry of the first.
      const queueId = await enqueue({
        table: "checkin",
        client_uuid: newItemUuid(),
        captured_at: new Date().toISOString(),
        payload: { ...payload },
      });
      notifyQueueChanged();
      onSaved(queueId);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Sheet
      titleKey="checkin.title"
      subtitleKey="screen.disclaimer"
      onClose={onClose}
      footer={
        <>
          <Button variant="quiet" onClick={onClose}>
            {t("common.cancel")}
          </Button>
          <Button onClick={() => void save()} loading={saving}>
            {t("checkin.submit")}
          </Button>
        </>
      }
    >
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
      {error === "mood" ? (
        <p className="sheet__error" role="alert">
          {t("checkin.error.mood")}
        </p>
      ) : null}

      <Slider labelKey="checkin.slider.label" value={slider} onChange={setSlider} min={0} max={10} />

      <Field labelKey="checkin.sleep.label" htmlFor="checkin-sleep">
        <TextInput
          id="checkin-sleep"
          type="number"
          inputMode="decimal"
          min={0}
          max={16}
          step={0.5}
          value={sleep}
          onChange={(e) => setSleep(e.target.value)}
        />
      </Field>

      <Field labelKey="checkin.optional.label" htmlFor="checkin-note">
        <TextArea
          id="checkin-note"
          rows={3}
          value={note}
          placeholder={t("checkin.optional.placeholder")}
          onChange={(e) => setNote(e.target.value)}
        />
      </Field>
      <VoiceCapture granted={voiceGranted} />

      {!checkinGranted ? (
        <Checkbox
          labelKey="consent.checkin.agree"
          checked={agreed}
          errorKey={error === "consent" ? "consent.checkin.error" : undefined}
          onChange={(next) => {
            setAgreed(next);
            setError((e) => (e === "consent" ? null : e));
          }}
        />
      ) : null}
    </Sheet>
  );
}
