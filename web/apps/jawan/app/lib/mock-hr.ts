/**
 * OFFLINE / DEGRADED FALLBACK ONLY.
 *
 * The roster home reads the real HR proxies — `getRoster()`, `getLeave()`,
 * `getPayslip()` from `@saarthi/api/jawan` — and caches each response in
 * IndexedDB so an offline open still shows the person's own duty, leave and
 * pay-slip month. These constants stand in for exactly one case: a first run
 * that has never reached the server and therefore has nothing cached. The
 * screen says so with `roster.demoNote` whenever they are on screen.
 *
 * Nothing here is welfare data, and nothing here is ever written back.
 */

export type MockHr = {
  nextDutyDate: string;
  nextDutyShift: string;
  leaveBalance: number;
  leaveEntitlement: number;
  payslipMonth: string;
};

export const mockHr: MockHr = {
  nextDutyDate: "2026-09-09",
  nextDutyShift: "day",
  leaveBalance: 12,
  leaveEntitlement: 30,
  payslipMonth: "2026-08",
};
