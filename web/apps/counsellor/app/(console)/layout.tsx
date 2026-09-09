"use client";

import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { usePathname, useRouter } from "next/navigation";
import { ConsoleShell, IconClipboard, IconPhoneCall, LanguageToggle, apiErrorStatus } from "@saarthi/ui";
import type { ConsoleNavItem } from "@saarthi/ui";
import { clearSession, getMe, getSession, getToken } from "@saarthi/api";

const NAV: ConsoleNavItem[] = [
  { href: "/", labelKey: "cons.nav.queue", icon: IconClipboard },
  { href: "/telemanas", labelKey: "cons.nav.telemanas", icon: IconPhoneCall },
];

const CONSOLE_ROLES = new Set(["counsellor", "welfare_officer"]);

/**
 * Console shell + the door. A token for another role never renders a frame of
 * this app: the session is cleared and the browser goes back to /login, because
 * "the UI is never trusted" cuts both ways (rbac-matrix.md).
 */
export default function ConsoleLayout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [ready, setReady] = useState(false);
  const [user, setUser] = useState<string | null>(null);

  useEffect(() => {
    const session = getSession();
    if (!getToken() || !session || !CONSOLE_ROLES.has(String(session.role))) {
      clearSession();
      router.replace("/login");
      return;
    }
    setUser(session.username);
    setReady(true);

    let live = true;
    getMe()
      .then((me) => {
        if (live) setUser(me.display_name || me.username);
      })
      .catch((err: unknown) => {
        // An expired token is a sign-out, not an error banner. Anything else
        // (a LAN blink) leaves the session name from localStorage in place.
        if (apiErrorStatus(err) === 401) {
          clearSession();
          router.replace("/login");
        }
      });
    return () => {
      live = false;
    };
  }, [router]);

  if (!ready) return null;

  const active = pathname.startsWith("/telemanas") ? "/telemanas" : "/";

  return (
    <ConsoleShell
      titleKey="cons.title"
      nav={NAV}
      active={active}
      user={user}
      onNavigate={(href) => router.push(href)}
      onSignOut={() => {
        clearSession();
        router.replace("/login");
      }}
    >
      <div className="cons-topbar">
        <LanguageToggle />
      </div>
      {children}
    </ConsoleShell>
  );
}
