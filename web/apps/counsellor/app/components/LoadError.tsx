"use client";

import { ErrorState, apiErrorStatus } from "@saarthi/ui";

export type LoadErrorProps = {
  error: unknown;
  onRetry?: () => void;
};

/**
 * One place decides what a failure means, so every screen says the same thing.
 *
 * status 0 — the LAN blinked. The console keeps whatever it already had on
 * screen and explains; it does not blank the page (design-client-apps.md §4).
 * status 403 — the server refused on privacy grounds. That is an answer, not a
 * fault, so there is no retry button to press.
 */
export function LoadError({ error, onRetry }: LoadErrorProps) {
  const status = apiErrorStatus(error);

  if (status === 0) {
    return <ErrorState titleKey="error.network" bodyKey="cons.error.retryWhenBack" onRetry={onRetry} />;
  }
  if (status === 403) {
    return <ErrorState titleKey="error.403" bodyKey="cons.error.forbidden" />;
  }
  if (status === 404) {
    return <ErrorState titleKey="error.404" bodyKey="cons.case.notFound" />;
  }
  return <ErrorState titleKey="common.error" bodyKey="cons.error.generic" onRetry={onRetry} />;
}

/** The banner variant: shown above data that is still on screen from before. */
export function ReconnectBanner({ error }: { error: unknown }) {
  if (apiErrorStatus(error) !== 0) return null;
  return (
    <div className="cons-banner">
      <ErrorState titleKey="error.network" bodyKey="cons.error.retryWhenBack" />
    </div>
  );
}
