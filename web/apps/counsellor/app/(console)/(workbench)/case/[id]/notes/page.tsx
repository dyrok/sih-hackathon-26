"use client";

import { useEffect, useState } from "react";
import type { FormEvent, KeyboardEvent } from "react";
import { useT } from "@saarthi/i18n";
import {
  Button,
  Field,
  Segmented,
  Skeleton,
  Slider,
  TextArea,
  TextInput,
  Toast,
  useApi,
} from "@saarthi/ui";
import { addNote, getNotes } from "@saarthi/api/counsellor";
import type { NoteDraft } from "@saarthi/api/counsellor";
import { useCase } from "../../../../../components/CaseContext";
import { LoadError } from "../../../../../components/LoadError";
import { formatDateTime, toLocalInputValue } from "../../../../../components/format";
import { useRole } from "../../../../../components/session";

const MODALITIES = [
  { value: "in_person", labelKey: "cons.notes.modality.in_person" },
  { value: "tele", labelKey: "cons.notes.modality.tele" },
  { value: "telemanas", labelKey: "cons.notes.modality.telemanas" },
];

type Draft = {
  sessionAt: string;
  modality: NoteDraft["modality"];
  themes: string[];
  reestimate: number;
  freeText: string;
};

const EMPTY: Draft = { sessionAt: "", modality: "in_person", themes: [], reestimate: 50, freeText: "" };

function draftKey(caseId: string): string {
  return `saarthi.cons.note.${caseId}`;
}

/** A date and a default modality are not an unsent note; themes and words are. */
function hasContent(draft: Draft): boolean {
  return draft.freeText.trim().length > 0 || draft.themes.length > 0;
}

/**
 * F06 screen 4. The draft is written to this machine on every keystroke and
 * restored on the way back in: an on-prem LAN drops, and a counsellor should
 * never pay for that with a note they have to remember and retype.
 */
export default function CaseNotesPage() {
  const { t, locale } = useT();
  const { caseId } = useCase();
  const role = useRole();

  const [draft, setDraft] = useState<Draft>(EMPTY);
  const [themeInput, setThemeInput] = useState("");
  const [hydrated, setHydrated] = useState(false);
  const [restored, setRestored] = useState(false);
  const [busy, setBusy] = useState(false);
  const [toastKey, setToastKey] = useState<string | null>(null);
  const [version, setVersion] = useState(0);

  const notes = useApi(() => getNotes(caseId), [caseId, version]);

  // Restore first, then start saving — otherwise the empty default would
  // overwrite the draft it is supposed to recover.
  useEffect(() => {
    let next: Draft = { ...EMPTY, sessionAt: toLocalInputValue(new Date()) };
    let wasRestored = false;
    try {
      const raw = localStorage.getItem(draftKey(caseId));
      if (raw) {
        const saved = JSON.parse(raw) as Partial<Draft>;
        next = { ...next, ...saved, themes: saved.themes ?? [] };
        wasRestored = hasContent(next);
      }
    } catch {
      /* private mode or corrupt draft: start from a clean form */
    }
    setDraft(next);
    setRestored(wasRestored);
    setHydrated(true);
  }, [caseId]);

  useEffect(() => {
    if (!hydrated) return;
    try {
      if (hasContent(draft)) localStorage.setItem(draftKey(caseId), JSON.stringify(draft));
      else localStorage.removeItem(draftKey(caseId));
    } catch {
      /* the note still submits; only the local copy is unavailable */
    }
  }, [draft, caseId, hydrated]);

  const addTheme = () => {
    const value = themeInput.trim();
    if (!value || draft.themes.includes(value)) {
      setThemeInput("");
      return;
    }
    setDraft((d) => ({ ...d, themes: [...d.themes, value] }));
    setThemeInput("");
  };

  const onThemeKey = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      addTheme();
    }
  };

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (busy) return;
    setBusy(true);
    setToastKey(null);
    try {
      await addNote(caseId, {
        session_at: draft.sessionAt ? new Date(draft.sessionAt).toISOString() : undefined,
        modality: draft.modality,
        themes: draft.themes,
        risk_reestimate: draft.reestimate,
        free_text: draft.freeText.trim() ? draft.freeText.trim() : null,
      });
      try {
        localStorage.removeItem(draftKey(caseId));
      } catch {
        /* nothing to clear */
      }
      setDraft({ ...EMPTY, sessionAt: toLocalInputValue(new Date()) });
      setRestored(false);
      setToastKey("cons.notes.saved");
      setVersion((v) => v + 1);
    } catch {
      setToastKey("cons.notes.saveError");
    } finally {
      setBusy(false);
    }
  };

  const canWrite = role === "counsellor";

  return (
    <>
      <section className="cons-card" aria-labelledby="cons-noteform-heading">
        <h2 className="cons-card__title" id="cons-noteform-heading">
          {t("cons.notes.add")}
        </h2>
        <p className="cons-card__note">{t("note.confidential")}</p>

        {!canWrite ? (
          <p className="cons-card__note">{t("cons.notes.readOnly")}</p>
        ) : (
          <form className="cons-stack" onSubmit={submit}>
            {restored ? (
              <p className="cons-callout" role="status">
                {t("cons.notes.draftRestored")}
              </p>
            ) : null}

            <Field labelKey="cons.notes.sessionAt" htmlFor="cons-note-at">
              <TextInput
                id="cons-note-at"
                type="datetime-local"
                value={draft.sessionAt}
                disabled={busy}
                onChange={(e) => setDraft((d) => ({ ...d, sessionAt: e.target.value }))}
              />
            </Field>

            <div className="cons-stack cons-stack--tight">
              <span className="sa-field__label">{t("cons.notes.modality")}</span>
              <Segmented
                name="cons-note-modality"
                options={MODALITIES}
                value={draft.modality}
                ariaLabelKey="cons.notes.modality"
                disabled={busy}
                onChange={(v) =>
                  setDraft((d) => ({ ...d, modality: v as NoteDraft["modality"] }))
                }
              />
            </div>

            <div className="cons-stack cons-stack--tight">
              <Field labelKey="cons.notes.themes" htmlFor="cons-note-theme">
                <div className="cons-inline cons-inline--tight cons-themeadd">
                  <TextInput
                    id="cons-note-theme"
                    value={themeInput}
                    placeholder={t("cons.notes.themePlaceholder")}
                    disabled={busy}
                    onKeyDown={onThemeKey}
                    onChange={(e) => setThemeInput(e.target.value)}
                  />
                  <Button variant="secondary" onClick={addTheme} disabled={busy || !themeInput.trim()}>
                    {t("cons.notes.themeAdd")}
                  </Button>
                </div>
              </Field>
              {draft.themes.length > 0 ? (
                <ul className="cons-themes">
                  {draft.themes.map((theme) => (
                    <li className="cons-theme" key={theme}>
                      <span>{theme}</span>
                      <button
                        type="button"
                        className="cons-theme__remove"
                        aria-label={t("cons.notes.themeRemove", { theme })}
                        onClick={() =>
                          setDraft((d) => ({ ...d, themes: d.themes.filter((x) => x !== theme) }))
                        }
                      >
                        <span aria-hidden="true">{"×"}</span>
                      </button>
                    </li>
                  ))}
                </ul>
              ) : null}
            </div>

            <Slider
              labelKey="cons.notes.reestimate"
              id="cons-note-risk"
              value={draft.reestimate}
              min={0}
              max={100}
              step={1}
              disabled={busy}
              onChange={(v) => setDraft((d) => ({ ...d, reestimate: v }))}
            />

            <Field labelKey="cons.notes.freeText" htmlFor="cons-note-text" hintKey="cons.notes.freeTextHint">
              <TextArea
                id="cons-note-text"
                rows={5}
                value={draft.freeText}
                disabled={busy}
                onChange={(e) => setDraft((d) => ({ ...d, freeText: e.target.value }))}
              />
            </Field>

            <div className="cons-inline">
              <Button type="submit" loading={busy}>
                {t("common.save")}
              </Button>
              {hydrated && hasContent(draft) ? (
                <span className="cons-card__note">{t("cons.notes.draftSaved")}</span>
              ) : null}
            </div>
          </form>
        )}

        {toastKey ? <Toast messageKey={toastKey} onDismiss={() => setToastKey(null)} timeoutMs={6000} /> : null}
      </section>

      <section className="cons-card" aria-labelledby="cons-notelist-heading">
        <h2 className="cons-card__title" id="cons-notelist-heading">
          {t("cons.notes.title")}
        </h2>
        <p className="cons-card__note">{t("note.confidential")}</p>

        {notes.loading && !notes.data ? (
          <Skeleton lines={3} height="20px" />
        ) : !notes.data ? (
          <LoadError error={notes.error} onRetry={notes.reload} />
        ) : notes.data.notes.length === 0 ? (
          <p className="cons-card__note">{t("cons.notes.empty")}</p>
        ) : (
          <ul className="cons-notelist">
            {notes.data.notes.map((note) => (
              <li className="cons-note" key={note.note_id}>
                <div className="cons-note__head">
                  <span>{formatDateTime(note.session_at, locale)}</span>
                  <span>{t(`cons.notes.modality.${note.modality}`)}</span>
                  {note.risk_reestimate !== null ? (
                    <span>{t("cons.notes.reestimateValue", { n: note.risk_reestimate })}</span>
                  ) : null}
                </div>
                {note.themes.length > 0 ? (
                  <ul className="cons-themes">
                    {note.themes.map((theme) => (
                      <li className="cons-theme" key={`${note.note_id}-${theme}`}>
                        <span>{theme}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="cons-note__withheld">{t("cons.notes.themesNone")}</p>
                )}
                {note.free_text ? (
                  <p className="cons-note__text">{note.free_text}</p>
                ) : note.free_text_withheld || !note.own ? (
                  <p className="cons-note__withheld">{t("cons.notes.withheld")}</p>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </section>
    </>
  );
}
