"use client";

import { useState } from "react";
import type { FormEvent } from "react";
import { useRouter } from "next/navigation";
import { useT } from "@saarthi/i18n";
import { Button, Field, LanguageToggle, TextInput } from "@saarthi/ui";
import { clearSession, login, saveSession } from "@saarthi/api";

/** Only these two roles have a console here. Everything else is sent away with
 *  its session cleared — a token that opened the wrong door is not left lying
 *  in localStorage. */
const CONSOLE_ROLES = new Set(["counsellor", "welfare_officer"]);

export default function LoginPage() {
  const { t } = useT();
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [errorKey, setErrorKey] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (busy) return;
    setBusy(true);
    setErrorKey(null);
    try {
      const session = await login(username.trim(), password);
      if (!CONSOLE_ROLES.has(String(session.role))) {
        clearSession();
        setErrorKey("login.wrongRole");
        setBusy(false);
        return;
      }
      saveSession(session);
      router.replace("/");
    } catch {
      setErrorKey("login.error");
      setBusy(false);
    }
  };

  const canSubmit = username.trim().length > 0 && password.length > 0;

  return (
    <main className="cons-login" id="content">
      <h1 className="cons-login__title">{t("cons.title")}</h1>
      <p className="cons-login__sub">{t("cons.login.roleNote")}</p>
      <form className="cons-login__form" onSubmit={submit}>
        <Field labelKey="login.username" htmlFor="cons-username" required>
          <TextInput
            id="cons-username"
            autoComplete="username"
            value={username}
            disabled={busy}
            onChange={(e) => setUsername(e.target.value)}
          />
        </Field>
        <Field
          labelKey="login.password"
          htmlFor="cons-password"
          required
          errorKey={errorKey ?? undefined}
        >
          <TextInput
            id="cons-password"
            type="password"
            autoComplete="current-password"
            value={password}
            disabled={busy}
            onChange={(e) => setPassword(e.target.value)}
          />
        </Field>
        <Button type="submit" loading={busy} disabled={!canSubmit}>
          {busy ? t("login.signingIn") : t("login.submit")}
        </Button>
      </form>
      <p className="cons-login__foot">{t("cons.login.demoHint")}</p>
      <LanguageToggle />
    </main>
  );
}
