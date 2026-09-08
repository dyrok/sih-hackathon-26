/**
 * MOCK HR data for the demo persona (Constable 34, 3rd Bn).
 * APP-002 adapter: kv's backend does not expose HRMS proxy endpoints yet.
 * These values stand in behind the same shape the real adapter will use —
 * swap the implementation, not the screen.
 */

export type MockHr = {
  nextDuty: string;
  leaveBalance: number;
  payslipMonth: string;
};

export const mockHr: MockHr = {
  nextDuty: "Tue 09 Sep · 06:00 gate duty",
  leaveBalance: 12,
  payslipMonth: "Aug 2026",
};
