"use client";

import { useEffect, useState } from "react";
import { useT } from "@saarthi/i18n";
import {
  Button,
  ConfirmDialog,
  Field,
  Modal,
  Select,
  apiErrorStatus,
  useApi,
} from "@saarthi/ui";
import {
  approveUnmask,
  breakGlass,
  getCatalogue,
  readIdentity,
  requestUnmask,
} from "@saarthi/api/counsellor";
import type { Identity, UnmaskReasonCode } from "@saarthi/api/counsellor";
import { formatDateTime } from "./format";
import { useRole } from "./session";

export type UnmaskPanelProps = {
  caseId: string;
  pseudonymId: string | null;
  /** Called after any identity event, so the timeline can pick it up. */
  onChanged?: () => void;
};

type Stored = { requestId: string; status: string };

/** Break-glass reason sent to the audit log. It is a fixed statement of the one
 *  lawful ground (MHA 2017 §23(1) public-safety exception), not free text a
 *  counsellor can shape after the fact. */
const BREAK_GLASS_REASON = "imminent_harm: immediate welfare contact required";

function storageKey(caseId: string): string {
  return `saarthi.cons.unmask.${caseId}`;
}

function readStored(caseId: string): Stored | null {
  try {
    const raw = localStorage.getItem(storageKey(caseId));
    return raw ? (JSON.parse(raw) as Stored) : null;
  } catch {
    return null;
  }
}

function writeStored(caseId: string, value: Stored | null): void {
  try {
    if (value) localStorage.setItem(storageKey(caseId), JSON.stringify(value));
    else localStorage.removeItem(storageKey(caseId));
  } catch {
    /* private mode: the request id lives for this tab only */
  }
}

/**
 * Dual-key unmask (F06 screen 3, FR-16) and the graver break-glass path.
 *
 * The two keys are two *people*: the request carries the first principal's key,
 * and the second has to be given by someone else signed in on this console. A
 * single principal pressing both buttons leaves the request pending forever —
 * that is the design working, not an error, so the UI says so plainly.
 */
export function UnmaskPanel({ caseId, pseudonymId, onChanged }: UnmaskPanelProps) {
  const { t, locale } = useT();
  const role = useRole();
  const catalogue = useApi(() => getCatalogue(), [], { cacheKey: "cons.catalogue" });

  const [modalOpen, setModalOpen] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [reason, setReason] = useState("");
  const [requestId, setRequestId] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [identity, setIdentity] = useState<Identity | null>(null);
  const [breakGlassAt, setBreakGlassAt] = useState<{ expiresAt: string; name: string | null } | null>(
    null,
  );
  const [busy, setBusy] = useState(false);
  const [messageKey, setMessageKey] = useState<string | null>(null);

  // A pending request belongs to the case, not to the person who filed it: the
  // second keyholder opens the same case and finds it waiting.
  useEffect(() => {
    const stored = readStored(caseId);
    setRequestId(stored?.requestId ?? null);
    setStatus(stored?.status ?? null);
    setIdentity(null);
    setBreakGlassAt(null);
    setMessageKey(null);
  }, [caseId]);

  const reasonCodes = Object.keys(catalogue.data?.unmask_reason_codes ?? {});
  const options = reasonCodes.map((code) => ({
    value: code,
    labelKey: `cons.unmask.reason.${code}`,
  }));

  const fetchIdentity = async (id: string) => {
    try {
      const ident = await readIdentity(id);
      setIdentity(ident);
      setMessageKey(null);
      onChanged?.();
    } catch (err) {
      setMessageKey(apiErrorStatus(err) === 403 ? "cons.unmask.expired" : "cons.error.generic");
    }
  };

  const submitRequest = async () => {
    if (!pseudonymId || !reason || busy) return;
    setBusy(true);
    setMessageKey(null);
    try {
      const res = await requestUnmask(pseudonymId, reason as UnmaskReasonCode);
      setRequestId(res.request_id);
      setStatus(res.status);
      writeStored(caseId, { requestId: res.request_id, status: res.status });
      onChanged?.();
    } catch (err) {
      const code = apiErrorStatus(err);
      setMessageKey(code === 403 ? "cons.unmask.noConsent" : "cons.error.generic");
    } finally {
      setBusy(false);
    }
  };

  const submitApproval = async () => {
    if (!requestId || busy) return;
    setBusy(true);
    setMessageKey(null);
    try {
      const res = await approveUnmask(requestId);
      setStatus(res.status);
      writeStored(caseId, { requestId, status: res.status });
      if (res.status === "granted") await fetchIdentity(requestId);
      else setMessageKey("cons.unmask.secondKeyHint");
      onChanged?.();
    } catch (err) {
      const code = apiErrorStatus(err);
      setMessageKey(
        code === 403 ? "cons.unmask.denied" : code === 409 ? "cons.unmask.keyTaken" : "cons.error.generic",
      );
    } finally {
      setBusy(false);
    }
  };

  const submitBreakGlass = async () => {
    setConfirmOpen(false);
    if (!pseudonymId || busy) return;
    setBusy(true);
    setMessageKey(null);
    try {
      const res = await breakGlass(pseudonymId, BREAK_GLASS_REASON);
      setBreakGlassAt({ expiresAt: res.expires_at, name: res.identity.legal_name });
      onChanged?.();
    } catch (err) {
      const code = apiErrorStatus(err);
      setMessageKey(
        code === 429
          ? "cons.breakglass.capped"
          : code === 403
            ? "cons.breakglass.counsellorOnly"
            : "cons.error.generic",
      );
    } finally {
      setBusy(false);
    }
  };

  const granted = identity !== null;

  return (
    <section className="cons-card" aria-labelledby="cons-unmask-heading">
      <h2 className="cons-card__title" id="cons-unmask-heading">
        {t("cons.unmask.title")}
      </h2>

      {granted && identity ? (
        <p className="cons-identity">
          {t("cons.unmask.identity", {
            name: identity.legal_name,
            rank: identity.rank,
            unit: identity.unit_id,
          })}{" "}
          <span className="cons-identity__expiry">
            {t("cons.unmask.granted", {
              when: formatDateTime(identity.session_expires_at, locale),
            })}
          </span>
        </p>
      ) : (
        <p className="cons-card__note">{t("cons.case.identityHidden")}</p>
      )}

      {!granted && status === "pending" ? (
        <p className="cons-callout">
          {t("cons.unmask.pending")}
          {requestId ? ` · ${t("cons.unmask.requestId", { id: requestId })}` : ""}
        </p>
      ) : null}

      {messageKey ? (
        <p className="cons-card__note" role="status">
          {t(messageKey)}
        </p>
      ) : null}

      {!granted ? (
        <div className="cons-inline">
          <Button variant="secondary" onClick={() => setModalOpen(true)} disabled={!pseudonymId}>
            {t(status === "pending" ? "cons.unmask.approve" : "cons.unmask.title")}
          </Button>
        </div>
      ) : null}

      {/* Break-glass is the expensive path, so it is one deliberate click away
          rather than sitting open on every case screen. The disclosure is a
          native <details> — keyboard-reachable, never hover-only. */}
      <details className="cons-breakglass" open={breakGlassAt !== null}>
        <summary className="cons-breakglass__summary">{t("cons.breakglass.title")}</summary>
        <div className="cons-callout cons-callout--grave">
          <p className="cons-callout__body">{t("cons.breakglass.explain")}</p>
          {breakGlassAt ? (
            <p className="cons-callout__body" role="status">
              {breakGlassAt.name ? `${t("cons.breakglass.name", { name: breakGlassAt.name })} · ` : ""}
              {t("cons.breakglass.opened", {
                when: formatDateTime(breakGlassAt.expiresAt, locale),
              })}{" "}
              {t("cons.breakglass.notified")}
            </p>
          ) : (
            <div className="cons-inline">
              <Button
                variant="quiet"
                onClick={() => setConfirmOpen(true)}
                disabled={!pseudonymId || role !== "counsellor"}
                loading={busy && confirmOpen}
              >
                {t("cons.breakglass.open")}
              </Button>
              {role !== null && role !== "counsellor" ? (
                <span className="cons-card__note">{t("cons.breakglass.counsellorOnly")}</span>
              ) : null}
            </div>
          )}
        </div>
      </details>

      {modalOpen ? (
        <Modal
          titleKey="cons.unmask.title"
          subtitleKey="cons.unmask.explain"
          onClose={() => setModalOpen(false)}
          footer={
            <>
              <Button variant="quiet" onClick={() => setModalOpen(false)}>
                {t("common.cancel")}
              </Button>
              {status === "pending" && requestId ? (
                <Button onClick={submitApproval} loading={busy}>
                  {t("cons.unmask.approve")}
                </Button>
              ) : (
                <Button onClick={submitRequest} loading={busy} disabled={!reason || !pseudonymId}>
                  {t("cons.unmask.request")}
                </Button>
              )}
            </>
          }
        >
          <div className="cons-stack">
            <p className="cons-card__note">{t("cons.unmask.receiptNote")}</p>

            {status === "pending" && requestId ? (
              <>
                <p>{t("cons.unmask.pending")}</p>
                <p className="cons-card__note">{t("cons.unmask.secondKeyHint")}</p>
                <p className="cons-card__note">{t("cons.unmask.requestId", { id: requestId })}</p>
              </>
            ) : (
              <Field labelKey="cons.unmask.reason" htmlFor="cons-unmask-reason" required>
                <Select
                  id="cons-unmask-reason"
                  options={options}
                  placeholderKey="cons.unmask.reasonChoose"
                  value={reason}
                  disabled={catalogue.loading && options.length === 0}
                  onChange={(e) => setReason(e.target.value)}
                />
              </Field>
            )}

            {messageKey ? (
              <p className="cons-card__note" role="alert">
                {t(messageKey)}
              </p>
            ) : null}
          </div>
        </Modal>
      ) : null}

      {confirmOpen ? (
        <ConfirmDialog
          titleKey="cons.breakglass.title"
          bodyKey="cons.breakglass.explain"
          confirmKey="cons.breakglass.open"
          cancelKey="common.cancel"
          tone="grave"
          onConfirm={submitBreakGlass}
          onCancel={() => setConfirmOpen(false)}
        />
      ) : null}
    </section>
  );
}
