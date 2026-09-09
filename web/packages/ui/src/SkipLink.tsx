"use client";

import { useT } from "@saarthi/i18n";

export type SkipLinkProps = {
  /** Defaults to the ConsoleShell's <main id="content">. */
  targetId?: string;
};

/** Keyboard users skip the sidebar. Visible only on focus, never `outline: none`. */
export function SkipLink({ targetId = "content" }: SkipLinkProps) {
  const { t } = useT();
  return (
    <a className="sa-skiplink" href={`#${targetId}`}>
      {t("a11y.skipToContent")}
    </a>
  );
}
