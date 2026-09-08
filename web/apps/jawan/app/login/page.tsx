"use client";

import { useState } from "react";
import type { FormEvent } from "react";
import { useRouter } from "next/navigation";
import { useT } from "@saarthi/i18n";
import { Button } from "@saarthi/ui";
import { login, saveSession } from "@saarthi/api";
import { getClientUuid } from "@saarthi/sync";

export default function LoginPage() {
  const { t } = useT();
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(false);
  const [busy, setBusy] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (busy) return;
    setBusy(true);
    setError(false);
    try {
      const session = await login(username, password);
      saveSession(session);
      await getClientUuid();
      router.replace("/roster");
    } catch {
      setError(true);
      setBusy(false);
    }
  };

  return (
    <div className="login-wrap">
      <h1 className="login-title">{t("login.title")}</h1>
      <p className="login-sub">{t("login.subtitle")}</p>
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
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        {error && <p className="login-error">{t("login.error")}</p>}
        <Button type="submit" loading={busy}>
          {busy ? t("login.signingIn") : t("login.submit")}
        </Button>
      </form>
    </div>
  );
}
