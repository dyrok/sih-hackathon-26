"use client";

import { useT } from "@saarthi/i18n";
import { Button } from "./Button";
import { IconInfo } from "./Icons";

export type ErrorStateProps = {
  titleKey: string;
  bodyKey: string;
  onRetry?: () => void;
};

/**
 * An error is a recovery path, never blame (design.md §8). Styled as a calm
 * notice — an amber rule, not a red stamp — with the way out as the one action.
 */
export function ErrorState({ titleKey, bodyKey, onRetry }: ErrorStateProps) {
  const { t } = useT();
  return (
    <div className="sa-errorstate" role="status">
      <IconInfo className="sa-errorstate__icon" width={24} height={24} />
      <div className="sa-errorstate__text">
        <p className="sa-errorstate__title">{t(titleKey)}</p>
        <p className="sa-errorstate__body">{t(bodyKey)}</p>
      </div>
      {onRetry ? (
        <Button variant="secondary" onClick={onRetry}>
          {t("common.retry")}
        </Button>
      ) : null}
    </div>
  );
}
