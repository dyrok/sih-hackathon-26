"use client";

import { useState } from "react";
import type { FormEvent } from "react";
import { useRouter } from "next/navigation";
import { useT } from "@saarthi/i18n";
import { Button, LanguageToggle } from "@saarthi/ui";
import { clearSession, login, saveSession } from "@saarthi/api";

/**
 * Commander sign-in. The token carries the role, so this screen only checks
 * that the role it was handed belongs on this console — a counsellor or a jawan
 * signing in here is turned away rather than shown an emptied-out dashboard.
 */
export default function LoginPage() {
  const { t } = useT();
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<"credentials" | "role" | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      const session = await login(username, password);
      if (session.role !== "commander") {
        clearSession();
        setError("role");
        setBusy(false);
        return;
      }
      saveSession(session);
      router.replace("/");
    } catch {
      setError("credentials");
      setBusy(false);
    }
  };

  return (
    <div className="cmd-login">
      <div className="cmd-login__lang">
        <LanguageToggle />
      </div>
      <h1 className="cmd-login__title">{t("login.title")}</h1>
      <p className="cmd-login__sub">{t("cmd.title")}</p>
      <form className="cmd-login__form" onSubmit={submit}>
        <div>
          <label className="cmd-login__label" htmlFor="username">
            {t("login.username")}
          </label>
          <input
            id="username"
            className="sa-input"
            autoComplete="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
        </div>
        <div>
          <label className="cmd-login__label" htmlFor="password">
            {t("login.password")}
          </label>
          <input
            id="password"
            className="sa-input"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        {error === "role" ? (
          <p className="cmd-login__error" role="alert">
            {t("login.wrongRole")}
          </p>
        ) : null}
        {error === "credentials" ? (
          <p className="cmd-login__error" role="alert">
            {t("login.error")}
          </p>
        ) : null}
        <Button type="submit" loading={busy}>
          {busy ? t("login.signingIn") : t("login.submit")}
        </Button>
      </form>
    </div>
  );
}
