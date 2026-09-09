/**
 * Shared transport. Role-specific calls live in ./jawan, ./counsellor and
 * ./commander and are reachable ONLY through those subpath exports — a console
 * that imports another role's module fails the path lint (scripts/path-lint.mjs),
 * which is how design-client-apps.md §6 "role routing" is enforced in code
 * rather than in review.
 */

/** Base URL for the FastAPI backend. Override via NEXT_PUBLIC_API_BASE. */
export const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000";

const TOKEN_KEY = "saarthi.token";
const SESSION_KEY = "saarthi.session";

export type Role =
  | "jawan"
  | "counsellor"
  | "welfare_officer"
  | "commander"
  | "admin"
  | "auditor"
  | "hr_ingest";

export type AuthSession = {
  token: string;
  role: Role | string;
  username: string;
  unitId?: string | null;
  pseudonymId?: string | null;
};

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function getSession(): AuthSession | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(SESSION_KEY);
    return raw ? (JSON.parse(raw) as AuthSession) : null;
  } catch {
    return null;
  }
}

export function saveSession(session: AuthSession): void {
  try {
    localStorage.setItem(TOKEN_KEY, session.token);
    localStorage.setItem(SESSION_KEY, JSON.stringify(session));
  } catch {
    /* private mode: the app still works for this session, just not across reloads */
  }
}

export function clearSession(): void {
  try {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(SESSION_KEY);
  } catch {
    /* nothing to clear */
  }
}

export class ApiError extends Error {
  status: number;
  /** True when the server refused on privacy grounds rather than a bad request. */
  get forbidden(): boolean {
    return this.status === 403;
  }
  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export type LoginResult = AuthSession;

/** Sign in. The token carries the role — the client never chooses its own. */
export async function login(username: string, password: string): Promise<LoginResult> {
  const body = (await apiFetch("/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
    auth: false,
  })) as Record<string, unknown>;
  const token = (body["access_token"] ?? body["token"]) as string | undefined;
  if (!token) throw new ApiError(500, "No token in login response");
  return {
    token,
    role: String(body["role"] ?? "jawan"),
    username: String(body["username"] ?? username),
    unitId: (body["unit_id"] as string | null) ?? null,
    pseudonymId: (body["pseudonym_id"] as string | null) ?? null,
  };
}

export type Me = {
  id: string;
  username: string;
  role: string;
  unit_id: string | null;
  pseudonym_id: string | null;
  display_name: string;
};

export function getMe(): Promise<Me> {
  return apiFetch("/auth/me") as Promise<Me>;
}

type FetchInit = RequestInit & { auth?: boolean };

/** Thin fetch wrapper: bearer token, JSON, ApiError on non-2xx. */
export async function apiFetch(path: string, init: FetchInit = {}): Promise<unknown> {
  const { auth = true, headers, ...rest } = init;
  const token = auth ? getToken() : null;
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...rest,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...headers,
      },
    });
  } catch (err) {
    // Distinguish "the network is gone" from "the server said no" — the UI
    // shows last-known data for one and an explanation for the other.
    throw new ApiError(0, err instanceof Error ? err.message : "network unreachable");
  }
  const text = await res.text();
  let body: unknown = null;
  if (text) {
    try {
      body = JSON.parse(text);
    } catch {
      body = { detail: text };
    }
  }
  if (!res.ok) {
    const detail = (body as { detail?: unknown } | null)?.detail;
    throw new ApiError(res.status, typeof detail === "string" ? detail : res.statusText);
  }
  return body;
}
