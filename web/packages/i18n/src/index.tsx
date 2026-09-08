"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import en from "./en.json";
import hi from "./hi.json";

export type Locale = "en" | "hi";

const dictionaries: Record<Locale, Record<string, string>> = { en, hi };
const STORAGE_KEY = "saarthi.locale";

type Vars = Record<string, string | number>;

type T = (key: string, vars?: Vars) => string;

type I18nContextValue = {
  locale: Locale;
  setLocale: (l: Locale) => void;
  t: T;
};

const I18nContext = createContext<I18nContextValue | null>(null);

function resolve(key: string, locale: Locale, vars?: Vars): string {
  const template = dictionaries[locale][key] ?? dictionaries.en[key] ?? key;
  if (!vars) return template;
  return template.replace(/\{(\w+)\}/g, (_, name: string) => String(vars[name] ?? `{${name}}`));
}

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("en");

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === "en" || stored === "hi") setLocaleState(stored);
  }, []);

  const setLocale = useCallback((l: Locale) => {
    setLocaleState(l);
    localStorage.setItem(STORAGE_KEY, l);
    document.documentElement.dataset.locale = l;
  }, []);

  useEffect(() => {
    document.documentElement.dataset.locale = locale;
  }, [locale]);

  const t = useCallback<T>((key, vars) => resolve(key, locale, vars), [locale]);

  const value = useMemo(() => ({ locale, setLocale, t }), [locale, setLocale, t]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useT(): I18nContextValue {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useT must be used inside <I18nProvider>");
  return ctx;
}

export { dictionaries };
