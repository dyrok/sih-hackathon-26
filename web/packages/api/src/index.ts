/**
 * Shared surface only. Role clients are deliberately NOT re-exported here:
 * importing `@saarthi/api` must never hand a console another role's calls.
 */
export {
  API_BASE,
  ApiError,
  apiFetch,
  clearSession,
  getMe,
  getSession,
  getToken,
  login,
  saveSession,
} from "./http";
export type { AuthSession, LoginResult, Me, Role } from "./http";
