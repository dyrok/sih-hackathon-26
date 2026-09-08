"use client";

import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useT } from "@saarthi/i18n";
import { BottomTabs, IconClipboard, IconHeart, IconUser, SyncPill } from "@saarthi/ui";
import type { TabItem } from "@saarthi/ui";
import { API_BASE, getToken } from "@saarthi/api";
import { startSyncEngine } from "@saarthi/sync";

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
  const engineRef = useRef<ReturnType<typeof startSyncEngine> | null>(null);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    setAuthed(true);
  }, [router]);

  useEffect(() => {
    if (!getToken()) return;
    engineRef.current = startSyncEngine({
      apiBase: API_BASE,
      getToken,
      endpoints: {
        checkin: "/app/checkins",
        instrument: "/app/instruments",
        consent: "/app/consent",
        pulse: "/app/pulse/ratings",
      },
    });
    return () => engineRef.current?.stop();
  }, []);

  if (authed === null) return null;

  const active = pathname.startsWith("/welfare") ? "welfare" : pathname.startsWith("/me") ? "me" : "roster";

  return (
    <div className="app-shell">
      <header className="app-topbar">
        <span className="app-brand">{t("login.title")}</span>
        <SyncPill />
      </header>
      <main className="app-main">{children}</main>
      <BottomTabs tabs={TABS} active={active} onSelect={(id) => router.push(`/${id}`)} />
    </div>
  );
}
