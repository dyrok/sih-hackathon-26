"use client";

import { useT } from "@saarthi/i18n";

/** Shared by every seeded demo account (`backend/app/seed.py`). */
export const DEMO_PASSWORD = "saarthi";

export type DemoAccount = {
  username: string;
  role: "jawan" | "counsellor" | "welfare_officer" | "commander";
  labelKey: string;
};

/** The six accounts a jury walkthrough actually uses. */
export const DEMO_ACCOUNTS: readonly DemoAccount[] = [
  { username: "jawan.demo", role: "jawan", labelKey: "login.demo.jawan3bn" },
  { username: "jawan.tiny", role: "jawan", labelKey: "login.demo.jawanTiny" },
  { username: "counsellor.a", role: "counsellor", labelKey: "login.demo.counsellor" },
  { username: "welfare.a", role: "welfare_officer", labelKey: "login.demo.welfare" },
  { username: "commander.3bn", role: "commander", labelKey: "login.demo.cmd3bn" },
  { username: "commander.tiny", role: "commander", labelKey: "login.demo.cmdTiny" },
];

export type DemoQuickLoginProps = {
  selectedUsername: string;
  onPick: (username: string, password: string) => void;
  disabled?: boolean;
};

/**
 * Demo-only account strip. A tap fills username + password (same secret for
 * every seeded user) so a walkthrough can sign out and switch role without
 * typing. The parent decides whether to auto-submit.
 */
export function DemoQuickLogin({ selectedUsername, onPick, disabled }: DemoQuickLoginProps) {
  const { t } = useT();
  const labels: Record<string, string> = {
    "jawan.demo": t("login.demo.jawan3bn"),
    "jawan.tiny": t("login.demo.jawanTiny"),
    "counsellor.a": t("login.demo.counsellor"),
    "welfare.a": t("login.demo.welfare"),
    "commander.3bn": t("login.demo.cmd3bn"),
    "commander.tiny": t("login.demo.cmdTiny"),
  };
  return (
    <div className="sa-quicklogin">
      <p className="sa-quicklogin__heading" id="sa-quicklogin-label">
        {t("login.demo.heading")}
      </p>
      <p className="sa-quicklogin__hint">{t("login.demo.hint")}</p>
      <div className="sa-quicklogin__tabs" role="group" aria-labelledby="sa-quicklogin-label">
        {DEMO_ACCOUNTS.map((account) => {
          const selected = account.username === selectedUsername;
          return (
            <button
              key={account.username}
              type="button"
              className={`sa-quicklogin__tab${selected ? " sa-quicklogin__tab--selected" : ""}`}
              disabled={disabled}
              aria-pressed={selected}
              onClick={() => onPick(account.username, DEMO_PASSWORD)}
            >
              <span className="sa-quicklogin__name">{labels[account.username]}</span>
              <span className="sa-quicklogin__user">{account.username}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
