"use client";

import type { ReactNode } from "react";
import Link from "next/link";
import { useT } from "@saarthi/i18n";
import { IconArrowLeft } from "@saarthi/ui";

type Props = {
  /** Route this screen was pushed from — a real link, so back works offline. */
  backHref: string;
  titleKey: string;
  /** The one line of guidance under the title. There is never a third level. */
  leadKey?: string;
  leadVars?: Record<string, string | number>;
  children: ReactNode;
};

/**
 * Frame for every pushed sub-route: back affordance, screen title, one line of
 * guidance, content. That is the whole hierarchy — design.md §3 rule of 3.
 */
export function SubScreen({ backHref, titleKey, leadKey, leadVars, children }: Props) {
  const { t } = useT();
  return (
    <div className="subscreen">
      <Link className="subscreen__back" href={backHref}>
        <IconArrowLeft width={20} height={20} />
        {t("common.back")}
      </Link>
      <h1 className="subscreen__title">{t(titleKey)}</h1>
      {leadKey ? <p className="subscreen__lead">{t(leadKey, leadVars)}</p> : null}
      {children}
    </div>
  );
}
