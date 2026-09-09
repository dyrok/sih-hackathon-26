"use client";

import { useT } from "@saarthi/i18n";
import { Segmented } from "./Segmented";

const OPTIONS = [
  { value: "en", labelKey: "settings.language.en" },
  { value: "hi", labelKey: "settings.language.hi" },
];

/**
 * en/hi switch. A real 2-option radio group, not a styled checkbox — the
 * language control is the first thing a Hindi-first user looks for, so it has
 * to be readable and reachable by keyboard on every surface.
 */
export function LanguageToggle() {
  const { locale, setLocale } = useT();
  return (
    <Segmented
      name="saarthi-locale"
      options={OPTIONS}
      value={locale}
      ariaLabelKey="settings.language"
      onChange={(v) => setLocale(v === "hi" ? "hi" : "en")}
    />
  );
}
