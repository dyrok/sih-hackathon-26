# ADR-0006 — Tech stack: FastAPI + PostgreSQL + Next.js + Expo/React Native

> Owner: kv · Status: accepted (2026-09-05) · Format: MADR v4 (lean)

## Decision
- **Backend/engines**: Python 3.11+, FastAPI, PostgreSQL (pseudonymized records + append-only audit).
- **Web consoles**: Next.js, bun tooling.
- **Mobile**: Expo / React Native with local SQLite (offline-first), native modules for on-device audio features.
- **Rules/ML**: pure Python rules engine v1; scikit-learn/lightgbm + SHAP reserved for v2.
- **Deployment story**: on-prem / NIC MeghRaj compatible; no foreign SaaS touches welfare data (Make-in-India / indigenous capability is a PS strategic requirement).

## Context
Hackathon constraints: 36h finale build, 6-person team (2 leads + 4 theory/QA), existing team skills (bun/React Native experience, Python), and the PS's sovereignty expectations.

## Options considered
| Option | Pros | Cons |
|---|---|---|
| **Chosen stack** | Fast to build; SHAP ecosystem native; team fluent | Two platforms (web+mobile) split attention |
| All-Node (Node ML) | One language | Weak explainability ecosystem |
| Flutter mobile | — | Team skill mismatch |

## Consequences
- Repo layout: `backend/` (Python), `web/` (Next.js), `mobile/` (Expo) — layout decided at prototype start, hour 1 of any build sprint.
- bun is the JS package manager/runner everywhere (team convention).
- Postgres chosen over Mongo for audit-integrity guarantees (append-only, constraints).

## Links
[architecture.md](../architecture.md) · [guides/setup](../../quality/test-plan.md)
