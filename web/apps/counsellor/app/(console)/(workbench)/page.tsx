"use client";

import { useT } from "@saarthi/i18n";

/** The detail pane before a case is picked. It teaches rather than decorates. */
export default function QueueLandingPage() {
  const { t } = useT();
  return (
    <div className="cons-head">
      <h1 className="cons-title">{t("cons.case.selectTitle")}</h1>
      <p className="cons-guide">{t("cons.case.selectBody")}</p>
    </div>
  );
}
