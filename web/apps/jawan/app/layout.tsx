import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import "@fontsource/noto-sans/400.css";
import "@fontsource/noto-sans/600.css";
import "@fontsource/noto-sans/700.css";
import "@fontsource/noto-sans-devanagari/400.css";
import "@fontsource/noto-sans-devanagari/600.css";
import "@fontsource/noto-sans-devanagari/700.css";
import "@saarthi/tokens/tokens.css";
import "@saarthi/ui/ui.css";
import "./globals.css";
import { I18nProvider } from "@saarthi/i18n";
import { tokens } from "@saarthi/tokens";
import { SwRegister } from "./sw-register";

export const metadata: Metadata = {
  title: "SAARTHI",
  description: "Fitness for duty · Parivaar welfare",
  manifest: "/manifest.webmanifest",
};

export const viewport: Viewport = {
  themeColor: tokens.color.brand.olive.fallback,
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <I18nProvider>{children}</I18nProvider>
        <SwRegister />
      </body>
    </html>
  );
}
