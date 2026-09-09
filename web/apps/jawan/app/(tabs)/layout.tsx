"use client";

import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useT } from "@saarthi/i18n";
import { BottomTabs, IconClipboard, IconHeart, IconUser, SkipLink, SyncPill } from "@saarthi/ui";
import type { TabItem } from "@saarthi/ui";
import { getToken } from "@saarthi/api";
import { ensureSyncEngine, stopSyncEngine } from "../lib/sync";

const TABS: TabItem[] = [
  { id: "roster", labelKey: "nav.roster", icon: IconClipboard },
  { id: "welfare", labelKey: "nav.welfare", icon: IconHeart },
  { id: "me", labelKey: "nav.me", icon: IconUser },
];

export default function TabsLayout({ children }: { children: ReactNode }) {
  const { t } = useT();
  const pathname = usePathname();
  const router = useRouter();
  const [authed, setAuthed] = useState<boolean | null>(null);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    setAuthed(true);
  }, [router]);

  useEffect(() => {
    if (!getToken()) return;
    // One engine for the whole session. It drains opportunistically; nothing on
    // screen ever waits for it (ADR-0005).
    ensureSyncEngine();
    return () => stopSyncEngine();
  }, []);

  if (authed === null) return null;

  const active = pathname.startsWith("/welfare")
    ? "welfare"
    : pathname.startsWith("/me")
      ? "me"
      : "roster";

  return (
    <div className="app-shell">
      <SkipLink targetId="content" />
      <header className="app-topbar">
        <span className="app-brand">{t("login.title")}</span>
        <SyncPill />
      </header>
      <main className="app-main" id="content" tabIndex={-1}>
        {children}
      </main>
      <BottomTabs tabs={TABS} active={active} onSelect={(id) => router.push(`/${id}`)} />
    </div>
  );
}
