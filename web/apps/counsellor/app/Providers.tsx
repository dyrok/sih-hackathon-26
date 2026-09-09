"use client";

import type { ReactNode } from "react";
import { I18nProvider } from "@saarthi/i18n";

/** Client boundary for the app. */
export function Providers({ children }: { children: ReactNode }) {
  return <I18nProvider>{children}</I18nProvider>;
}
