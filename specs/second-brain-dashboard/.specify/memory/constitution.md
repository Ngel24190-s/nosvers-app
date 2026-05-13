<!--
SYNC IMPACT REPORT
==================
Version change: (template placeholders) → 1.0.0
Bump rationale: Initial ratification of the project 002 constitution. No prior
versioned constitution existed (file held template placeholders only); first
adoption is a MINOR-stable 1.0.0 baseline rather than 0.x to signal that these
principles are binding on Fase A and beyond.

Principles added (10, all new):
  I.   Soberanía
  II.  MCP-first
  III. Vault as Source of Truth
  IV.  Reuse 001, do not duplicate
  V.   No regression on existing infra
  VI.  Read-only Fase A
  VII. Real multi-user (JWT angel | africa)
  VIII.Light stack — no heavy frameworks
  IX.  Observability
  X.   Security baseline

Sections added:
  - Core Principles (I–X)
  - Additional Constraints (stack + hosting + dependency boundary)
  - Development Workflow (Spec Kit flow, gates, validation)
  - Governance (versioning, amendments, compliance)

Sections removed: none (template skeleton replaced wholesale).

Templates / runtime docs reviewed:
  ✅ .specify/templates/plan-template.md   — Constitution Check section is
       principle-agnostic (refers to "Gates determined based on constitution
       file"); no edits required. Plan authors must enumerate gates from the
       10 principles below when filling plan.md.
  ✅ .specify/templates/spec-template.md   — No principle-specific content;
       still aligned (user-story + FR + SC layout works for read-only Fase A).
  ✅ .specify/templates/tasks-template.md  — Story-grouped layout aligned with
       Principle VI (Fase A only) and Principle IV (reuse). No edits.
  ✅ .specify/templates/checklist-template.md — Not loaded in this pass; no
       known principle conflict.
  ✅ /home/nosvers/CLAUDE.md (runtime guidance) — Cites the 7-agent roster and
       NosVers ops norms; not in conflict. The dashboard is layered ON TOP of
       what CLAUDE.md describes; no edits required.
  ✅ specs/second-brain-dashboard/CLAUDE.md — Points to "current plan" for
       stack details; harmless deferral, no edits required.

Deferred / TODOs: none. RATIFICATION_DATE and LAST_AMENDED_DATE are both
2026-05-13 (today, first adoption).
-->

# Second Brain Dashboard (NosVers · Proyecto 002) Constitution

## Core Principles

### I. Soberanía

The dashboard MUST run end-to-end on infrastructure NosVers owns or controls
(VPS Hostinger, the existing nginx + FastAPI stack, the same vault filesystem
the rest of the platform uses). No proprietary cloud service (Vercel, Netlify,
Supabase, Firebase, managed graph DBs, hosted vector DBs, hosted auth, etc.)
MAY be introduced when a local alternative is feasible. Third-party services
already integrated through the existing MCP server (Google Calendar/Drive,
WordPress.com, Stripe, Ahrefs, Canva, Figma, Telegram) MAY continue to be
consumed via that MCP layer, but no new external dependency MAY be added to
the dashboard without an explicit waiver recorded in plan.md → Complexity
Tracking. *Rationale*: NosVers' mission is soberanía alimentaire y digital;
the second-brain dashboard cannot violate it for convenience.

### II. MCP-first

The dashboard is a **client**, not a logic owner. Any capability the dashboard
exposes (search, capture, agent execution, system status, calendar/email, etc.)
MUST be backed by an MCP tool on the existing `nosvers-mcp-2026` server (or a
module already wired through `voz/*` REST endpoints from project 001). New
capability flow is **strictly**: (1) define/extend an MCP tool, (2) add a thin
REST adapter only if browser cannot reach the MCP directly, (3) consume from
the React app. Putting business logic in the React or FastAPI dashboard layer
is a violation. *Rationale*: the MCP is reusable across Claude desktop, Claude
mobile, CLI, the bot, and future surfaces; duplicating logic in the dashboard
fragments the brain.

### III. Vault as Source of Truth

The dashboard MUST NOT introduce a parallel database. Every piece of state the
user sees is read directly from `/home/nosvers/public_html/knowledge_base/`
markdown files (frontmatter + body) via the same `voz/vault_io.py` and
`voz/buscar.py` modules used by project 001. Reads MAY be cached (in-process
LRU, ETag/If-Modified-Since, IndexedDB on the client) provided the cache is
invalidated by file mtime. Writes — when introduced in Fase B+ — MUST go to
markdown files only; no SQLite, no Postgres, no Redis-as-store. Ephemeral
state (rate-limit counters, JWT denylist, WebSocket presence) MAY use an
in-memory or Redis-as-cache layer if and only if losing it on restart is
acceptable. *Rationale*: divergence between vault and DB is the failure mode
that killed earlier "second brain" attempts. One copy. One truth.

### IV. Reuse 001, do not duplicate

The dashboard MUST import and reuse existing project 001 modules:
`voz/auth.py` (JWT issuing/validation, refresh tokens), `voz/buscar.py`
(full-text vault search), `voz/capturar.py` (note capture — Fase B+),
`voz/vault_io.py` (markdown read/write, frontmatter parse), `voz/contexto.py`
(day context). Re-implementing equivalent logic in a new module is a
violation. The existing `agt07_diario` agent MUST NOT be cloned or replaced;
if a behavior change is needed, extend it in place. New REST endpoints live
in `voz/rest.py` or a sibling module that re-exports `voz/*` primitives —
they do not own logic. *Rationale*: this is the same brain, just with a new
face. Forking modules silently is technical debt with compound interest.

### V. No regression on existing infra

Deploying Fase A (or any later phase) MUST NOT change the externally observed
behavior of: (a) the voz PWAs and their service workers, (b) the speaker-ID
flow on the Linux casa machine, (c) the `agt07_diario` cron, (d) the Telegram
bot at `@nosvers_hq_bot`, (e) any other agent cron in `/home/nosvers/agents/`,
(f) WordPress at `nosvers.com` (including LiteSpeed cache and Bricks
templates), (g) the freqtrade and grid_trading bots. The implementation plan
MUST list which existing services it touches (nginx vhosts, systemd units,
python virtualenvs, shared modules) and a rollback procedure. A "go-live"
ships only after a smoke test confirms all the systems above still pass their
own health checks. *Rationale*: a dashboard that breaks the bot is a net
negative regardless of how pretty it is.

### VI. Read-only Fase A

The Fase A deliverable MUST be strictly read-only from the dashboard's point
of view: every backend endpoint added in Fase A is `GET`; the React app has
no form submission, no `POST`/`PUT`/`DELETE`/`PATCH` calls, no optimistic
mutations. Authentication-related endpoints (`/auth/refresh`,
`/auth/whoami`) are permitted because they don't write to the vault. Capture,
edit, delete, kanban moves, automatizaciones — all MUST wait for an explicit
Fase B (or later) spec/plan/tasks cycle. *Rationale*: the dashboard's first
job is to prove the viewer works without risk of corrupting the vault; once
that's validated, write paths are added with a much smaller blast radius.

### VII. Real multi-user

The dashboard MUST treat Angel and África as first-class peers. Every backend
request MUST be authenticated by a JWT whose `sub` claim is `angel` or
`africa`; unauthenticated requests MUST receive HTTP 401. The timeline view
MUST show **both** authors' notes interleaved by date, with a visible author
chip on each entry; filtering to a single author is a UI affordance, not a
backend privilege. There is no admin role; both users have equal read access
to each other's notes (intentional, by Angel + África's agreement). Sessions
MUST be stateless on the server (JWT only, no server-side session store);
silent renewal uses refresh tokens from `voz/auth.py`. *Rationale*: NosVers
is a two-person team; pretending otherwise creates artificial barriers.

### VIII. Light stack — no heavy frameworks

The frontend MUST be Vite + React 18 + TypeScript + Tailwind CSS + shadcn/ui,
no Next.js, no Remix, no Gatsby, no Nuxt, no Astro, no full-stack meta-
framework. SSR is forbidden in Fase A. The backend extension MUST be a
FastAPI module loaded by the same uvicorn process that serves the MCP/REST
of project 001; a separate web server (Node, Express, NestJS) MUST NOT be
introduced. New runtime dependencies require justification in plan.md →
Complexity Tracking. *Rationale*: NosVers is a two-person operation on a
single VPS; every framework added is one more thing to update, debug, and
secure when nobody is watching.

### IX. Observability

Every new REST endpoint MUST log to the same structured log channel used by
`voz/rest.py` (request id, user `sub`, route, latency ms, status code).
Critical failures (5xx, JWT verify failure spike, vault read errors) MUST
notify the CEO via the existing Telegram bot using
`mcp__claude_ai_nosvers-mcp-2026__telegram_enviar` or its equivalent on the
server side, with an automatic deduplication window so the same error
doesn't page Angel ten times in a minute. Frontend errors MUST be captured
locally (browser console + IndexedDB ring buffer) and surfaced on a
diagnostics page; no third-party error tracker (Sentry, LogRocket, Datadog)
MAY be added. *Rationale*: Principle I prohibits external telemetry;
Telegram is already the alert channel Angel actually reads.

### X. Security baseline

Production traffic to `tablero.nosvers.com` (or whatever subdomain is
chosen in plan.md) MUST be HTTPS-only via Let's Encrypt, with HSTS enabled
and HTTP redirected to HTTPS at the nginx layer. Access tokens MUST have a
lifetime of ≤ 15 minutes; refresh tokens ≤ 30 days, rotation on use,
revocable. All API endpoints MUST be rate-limited at the nginx or FastAPI
layer (per-IP and per-`sub`). CORS MUST allow only the dashboard origin;
the wildcard `*` is forbidden. No secrets (JWT signing keys, OAuth tokens,
API keys) MAY ship in the React bundle; they live in `.env.local` on the
VPS, referenced server-side only. Dependency installs MUST pin versions in
`package-lock.json` / `pyproject.toml`. *Rationale*: this surface lives on
the open internet under Angel's name; the floor must be defined.

## Additional Constraints

**Hosting & repo layout.** The codebase lives at
`/home/nosvers/specs/second-brain-dashboard/` for design artifacts and at
`/home/nosvers/dashboard/` (or a sibling path chosen in plan.md) for
runtime code. The frontend is served as static files by nginx from the
build output directory; `/api/*` paths are proxied to the FastAPI process
on `127.0.0.1:<port>`.

**Performance budget.** Initial dashboard load (cold cache, 4G mobile)
MUST complete in ≤ 2 s as measured by Lighthouse "Time to Interactive"
on a representative timeline page with 30 notes. Full-text search via
`dia_buscar` MUST return p95 ≤ 500 ms with the current vault size; if a
larger vault degrades this, an index (server-side, file-backed, derived
from the vault — not a new source of truth) MAY be introduced under a
plan.md justification, and rebuilt from the vault on demand.

**Dependency boundary.** Project 001 MUST remain runnable without project
002 (i.e., uninstalling the dashboard does not break voz). Project 002
MAY require project 001 — that direction of dependency is encouraged.

## Development Workflow

The Spec Kit flow is the only path from idea to merge:
`/speckit-constitution` → `/speckit-specify` → `/speckit-clarify` (if any
NEEDS CLARIFICATION marker survives in spec.md) → `/speckit-plan` →
`/speckit-tasks` → `/speckit-implement` → STOP at Fase A boundary and wait
for the CEO's validation before opening Fase B.

**Constitution Check gate.** Plans MUST include a "Constitution Check"
section that maps every principle (I–X) to either "compliant" or "violation
+ justification". A plan with unjustified violations cannot enter Phase 0
research.

**Quality gates.** Before declaring Fase A done: (1) the smoke test for
existing services (Principle V) passes, (2) the read-only constraint
(Principle VI) is verified by grep'ing the frontend bundle for write verbs
to dashboard endpoints, (3) the Lighthouse budget (Additional Constraints)
is measured and reported, (4) JWT auth is exercised end-to-end with both
`sub: angel` and `sub: africa` tokens.

**Manual verification before Telegram.** Any "Fase X complete" message to
the CEO via Telegram is sent only after the gates above pass. The known
`telegram_enviar` MCP stall bug (memory: `project_telegram_enviar_stall`)
governs the send: abort at 30 s, retry once, on second stall mark
`MCP_STALL_FASE_A` and continue without blocking the user.

## Governance

This constitution supersedes any conflicting instruction in CLAUDE.md
files, ad-hoc chat, or external documentation **for this project (002)
only**. The user (Angel, CEO) remains the highest authority and MAY
override any principle in a specific conversation; such overrides MUST be
captured as constitution amendments at the next opportunity, not left as
oral tradition.

**Amendment procedure.** Amendments are proposed by editing this file
through `/speckit-constitution` (never directly). Each amendment MUST
update the Sync Impact Report at the top, bump the version per the
semver rules below, and propagate changes to the templates listed in
that report.

**Versioning policy.** Constitution versions use semantic versioning:
- **MAJOR** — a principle is removed or fundamentally redefined in a way
  that invalidates compliant plans/specs from the previous version
  (e.g., dropping "Vault as Source of Truth").
- **MINOR** — a principle is added, or an existing principle is
  materially expanded (e.g., adding a new mandatory section).
- **PATCH** — wording, typo, clarification, or non-semantic refinement.

**Compliance review.** Every `/speckit-plan` invocation MUST include the
Constitution Check section described above. Every `/speckit-implement`
run MUST verify principles VI (read-only Fase A), V (no regression), and
X (security baseline) before declaring completion.

**Version**: 1.0.0 | **Ratified**: 2026-05-13 | **Last Amended**: 2026-05-13
