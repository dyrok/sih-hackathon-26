"use client";

import { createContext, useContext } from "react";
import type { ReactNode } from "react";
import type { CaseDetail } from "@saarthi/api/counsellor";

export type CaseContextValue = {
  caseId: string;
  detail: CaseDetail | null;
  error: unknown;
  loading: boolean;
  reload: () => void;
};

const CaseContext = createContext<CaseContextValue | null>(null);

/** The case layout loads the case once; evidence, notes and outcome read it
 *  from here instead of each re-fetching (and re-auditing) the same record. */
export function CaseProvider({ value, children }: { value: CaseContextValue; children: ReactNode }) {
  return <CaseContext.Provider value={value}>{children}</CaseContext.Provider>;
}

export function useCase(): CaseContextValue {
  const ctx = useContext(CaseContext);
  if (!ctx) throw new Error("useCase must be used inside a case route");
  return ctx;
}
