"use client";

import type { ComponentType, ReactNode, SVGProps } from "react";
import { useT } from "@saarthi/i18n";
import { SkipLink } from "./SkipLink";
import { IconLogout } from "./Icons";

export type ConsoleNavItem = {
  href: string;
  labelKey: string;
  icon: ComponentType<SVGProps<SVGSVGElement>>;
};

export type ConsoleShellProps = {
  titleKey: string;
  nav: ConsoleNavItem[];
  /** The active `href`. */
  active: string;
  /** Display name of the signed-in operator; already a value, not a key. */
  user?: string | null;
  onSignOut: () => void;
  children: ReactNode;
  /**
   * Optional client-side router hook. The links stay real <a href> elements —
   * middle-click, ctrl-click and "open in new tab" keep working — and this only
   * intercepts a plain left click so the console does not do a full reload.
   */
  onNavigate?: (href: string) => void;
};

/**
 * Sidebar layout for the two consoles. Real <a> elements, `aria-current="page"`
 * on the active route, a skip link before the nav, and one <main id="content">.
 * Under 900px the sidebar becomes a top bar whose nav scrolls horizontally —
 * no hamburger, because a hidden nav is a nav an operator cannot scan.
 */
export function ConsoleShell({
  titleKey,
  nav,
  active,
  user,
  onSignOut,
  children,
  onNavigate,
}: ConsoleShellProps) {
  const { t } = useT();
  return (
    <div className="sa-console">
      <SkipLink />
      <header className="sa-console__side">
        <p className="sa-console__brand">{t(titleKey)}</p>
        <nav className="sa-console__nav" aria-label={t("a11y.mainNav")}>
          <ul className="sa-console__navlist">
            {nav.map(({ href, labelKey, icon: Icon }) => (
              <li key={href}>
                <a
                  className={`sa-console__navlink${href === active ? " sa-console__navlink--active" : ""}`}
                  href={href}
                  aria-current={href === active ? "page" : undefined}
                  onClick={
                    onNavigate
                      ? (e) => {
                          if (e.defaultPrevented || e.button !== 0) return;
                          if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
                          e.preventDefault();
                          onNavigate(href);
                        }
                      : undefined
                  }
                >
                  <Icon width={20} height={20} />
                  <span className="sa-console__navlabel">{t(labelKey)}</span>
                </a>
              </li>
            ))}
          </ul>
        </nav>
        <div className="sa-console__foot">
          {user ? <span className="sa-console__user">{user}</span> : null}
          <button type="button" className="sa-console__signout" onClick={onSignOut}>
            <IconLogout width={18} height={18} />
            <span>{t("nav.signOut")}</span>
          </button>
        </div>
      </header>
      <main className="sa-console__main" id="content">
        {children}
      </main>
    </div>
  );
}
