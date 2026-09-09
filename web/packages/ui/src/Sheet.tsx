"use client";

import { BaseDialog } from "./BaseDialog";
import type { BaseDialogProps } from "./BaseDialog";

export type SheetProps = BaseDialogProps;

/**
 * Bottom sheet — the "attention" plane of the 3-plane depth model (design.md
 * §4). Anchored to the thumb zone, backdrop click and Escape both close.
 */
export function Sheet(props: SheetProps) {
  return <BaseDialog {...props} variant="sheet" />;
}
