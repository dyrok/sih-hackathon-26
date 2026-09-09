"use client";

import { BaseDialog } from "./BaseDialog";
import type { BaseDialogProps } from "./BaseDialog";

export type ModalProps = BaseDialogProps;

/**
 * Centred dialog for the two consoles (unmask, break-glass, handoff forms).
 * Same primitive as Sheet — only the anchoring changes, so behaviour never
 * diverges between surfaces.
 */
export function Modal(props: ModalProps) {
  return <BaseDialog {...props} variant="modal" />;
}
