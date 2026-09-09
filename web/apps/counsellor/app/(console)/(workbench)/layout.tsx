"use client";

import type { ReactNode } from "react";
import { QueueRail } from "../../components/QueueRail";

/**
 * Master–detail (design-client-apps.md §2): the queue stays on the left while a
 * case is open on the right, so working a caseload is never a sequence of
 * back-navigations. Under 1100px the two panes stack, queue first.
 */
export default function WorkbenchLayout({ children }: { children: ReactNode }) {
  return (
    <div className="cons-workbench">
      <QueueRail />
      <div className="cons-detail">{children}</div>
    </div>
  );
}
