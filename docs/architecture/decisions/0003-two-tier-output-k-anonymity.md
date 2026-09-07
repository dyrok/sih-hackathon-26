# ADR-0003 — Two-tier output + architectural welfare firewall (k ≥ 5)

> Owner: kv · Status: accepted (2026-09-05) · Format: MADR v4 (lean)

## Decision
**Individual risk scores are physically incapable of reaching command hierarchy, ACR, promotion or posting decisions.** Enforced in architecture, not in a policy sentence:

1. Two-tier output — individual risk goes to the counsellor only, consent-gated. Commander sees unit aggregates only, with k-anonymity ≥ 5, no names.
2. Analytics run on pseudonyms. Unmasking (pseudonym → identity) requires counsellor + welfare officer (dual key); every unlock is logged and visible to the subject ("who viewed my data").
3. Silent consent withdrawal — withdrawing consent is invisible to command, otherwise the withdrawal itself becomes a signal nobody will ever risk.
4. 90-day raw-data expiry — raw self-reports auto-expire; only the derived risk trend persists.

## Context
PS challenge #2 (stigmatization) and challenge #1 (privacy). A promise ("we promise scores won't be used against you") is worthless in a force with ACR culture. The demo's most memorable 15 seconds is the jawan's phone showing who accessed their record.

## Options considered
| Option | Pros | Cons |
|---|---|---|
| **Architectural firewall (chosen)** | Cannot be misused even by a malicious admin; audit-provable; demo-able | Harder to build; limits future "features" that would be punitive anyway |
| Policy promise + RBAC alone | Easy | One query away from abuse; zero demo value; judges see through it |

## Consequences
- Commander dashboard APIs reject personnel-ID lookups for welfare data at the route level.
- Audit log is append-only; break-glass access notifies the subject it happened.
- Aggregation service suppresses any cell with < 5 contributors (also where differential-privacy noise lands in future).

## Links
[ADR-0001](0001-rules-engine-v1-not-ml.md) · [F08](../../features/F08-privacy-safety-architecture.md) · [rbac-matrix.md](../../compliance/rbac-matrix.md)
