"use client";

import type { ComponentType, ReactNode, SVGProps } from "react";
import { useT } from "@saarthi/i18n";

export type EmptyStateProps = {
  icon: ComponentType<SVGProps<SVGSVGElement>>;
  titleKey: string;
  bodyKey?: string;
  action?: ReactNode;
};

/**
 * Empty states teach, they never scold (design.md §6): "first check-in takes
 * 10 seconds", not "you have no data". No alarm colour, no exclamation marks.
 */
export function EmptyState({ icon: Icon, titleKey, bodyKey, action }: EmptyStateProps) {
  const { t } = useT();
  return (
    <div className="sa-empty">
      <Icon className="sa-empty__icon" width={32} height={32} />
      <p className="sa-empty__title">{t(titleKey)}</p>
      {bodyKey ? <p className="sa-empty__body">{t(bodyKey)}</p> : null}
      {action ? <div className="sa-empty__action">{action}</div> : null}
    </div>
  );
}
