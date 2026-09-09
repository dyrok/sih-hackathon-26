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
import { tokens } from "@saarthi/tokens";
import { Providers } from "./Providers";

export const metadata: Metadata = {
  title: "SAARTHI counsellor console",
  description: "Pseudonymised clinical workbench — cases, evidence, notes, outcomes.",
};

export const viewport: Viewport = {
  themeColor: tokens.color.brand.olive.fallback,
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
