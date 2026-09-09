"use client";

import { useEffect, useState } from "react";
import { getSession } from "@saarthi/api";

/**
 * The signed-in role, read after mount so the server render and the first
 * client render agree. `null` means "not known yet" — screens that gate a
 * write on it render the read-only path until it resolves, never the other way
 * round.
 */
export function useRole(): string | null {
  const [role, setRole] = useState<string | null>(null);
  useEffect(() => {
    const session = getSession();
    setRole(session ? String(session.role) : null);
  }, []);
  return role;
}
