"use client";

import { useState } from "react";
import type { FormEvent } from "react";
import { useRouter } from "next/navigation";
import { useT } from "@saarthi/i18n";
import { Button, DemoQuickLogin } from "@saarthi/ui";
import { clearSession, login, saveSession } from "@saarthi/api";
import { getClientUuid } from "@saarthi/sync";

export default function LoginPage() {
  const { t } = useT();
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<"credentials" | "role" | null>(null);
  const [busy, setBusy] = useState(false);

  const signIn = async (user: string, pass: string) => {
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      const session = await login(user.trim(), pass);
      if (session.role !== "jawan") {
        clearSession();
        setError("role");
        setBusy(false);
        return;
      }
      saveSession(session);
      await getClientUuid();
      router.replace("/roster");
    } catch {
      setError("credentials");
      setBusy(false);
    }
  };

  const submit = (e: FormEvent) => {
    e.preventDefault();
    void signIn(username, password);
  };

  return (
    <div className="login-wrap">
      <h1 className="login-title">{t("login.title")}</h1>
      <p className="login-sub">{t("login.subtitle")}</p>
      <DemoQuickLogin
        selectedUsername={username}
        disabled={busy}
        onPick={(user, pass) => {
          setUsername(user);
          setPassword(pass);
          void signIn(user, pass);
        }}
      />
      <form className="login-form" onSubmit={submit}>
        <div>
          <label className="field-label" htmlFor="username">
            {t("login.username")}
          </label>
          <input
            id="username"
            className="field-input"
            autoComplete="username"
            value={username}
            disabled={busy}
            onChange={(e) => setUsername(e.target.value)}
          />
        </div>
        <div>
          <label className="field-label" htmlFor="password">
            {t("login.password")}
          </label>
          <input
            id="password"
            className="field-input"
            type="password"
            autoComplete="current-password"
            value={password}
            disabled={busy}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        {error === "role" ? (
          <p className="login-error" role="alert">
            {t("login.wrongRole")}
          </p>
        ) : null}
        {error === "credentials" ? (
          <p className="login-error" role="alert">
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
