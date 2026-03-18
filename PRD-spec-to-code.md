# PRD: Lineage — The Human-Driven, AI-Powered Project Platform

**Version:** 0.3 (Draft)
**Date:** 2026-03-18
**Status:** Ideation

---

## 1. Problem Statement

### The AI Acceleration Trap

AI coding agents (Claude Code, Codex, Cursor) have made *generating code* 10x faster. But they've made *understanding what was built and why* 10x harder. The bottleneck has shifted from "can we build it?" to "should we build it, and do we know what we built?"

Today's reality:
- **No forcing function for thinking first.** AI makes it so easy to jump to code that teams skip the "what are we building and why?" step entirely. The result: fast code, wrong product.
- **Specs rot instantly.** Written in Docs/Notion, disconnected from code. Dead on arrival.
- **AI sessions are ephemeral.** A Claude Code session produces great code, but the *reasoning*, the *context*, the *decisions* evaporate. Six months later, nobody knows why.
- **Discovery is informal.** Teams do user research, competitive analysis, technical spikes — but none of it is structured or linked to what gets built.
- **The human lost control.** AI agents execute fast but the human directing them has no dashboard, no history, no way to steer across multiple sessions.

### The Core Insight

> **AI is a power tool. Power tools need a workbench.**
>
> The workbench is: a structured project lifecycle where humans think first (discovery, spec, plan), AI executes (implementation), and everything is connected and versioned.

### Who feels this pain?

| Persona | Pain |
|---------|------|
| **Founder/PM** | "We shipped fast with AI but I can't explain what we built or why" |
| **Tech Lead** | "I have 5 devs using Claude Code independently. No coherence." |
| **Solo Developer** | "I use AI for everything but my project is a mess of disconnected sessions" |
| **QA** | "What should this feature actually do? Nobody wrote it down." |
| **New Team Member** | "I can't understand this codebase — there's no record of intent" |

---

## 2. Vision

**Lineage** is a cloud platform that structures the full lifecycle of a software project — from discovery to spec to plan to AI-powered implementation — where the **human drives** and the **AI executes**, and every step is connected, versioned, and traceable.

It's not a spec tool. It's not a project manager. It's **the workbench for humans building with AI**.

### One-liner
> "The project cockpit for the AI coding era — where thinking comes before building, and everything is connected."

### The Mental Model

Think of Lineage as a **repository of projects**, not a repository of code. Each project is a structured journey:

```
Project
├── Discovery Phase (research, interviews, competitive analysis, spikes)
├── Functional Spec (the "what" — versioned master document)
├── Technical Plans (the "how" — derived from spec)
├── Implementation Sessions (AI agent executions — fully recorded)
├── Verification (does code match spec?)
└── Evolution (spec changes → cascading updates)
```

The human is always in the driver's seat. AI assists at every phase but never decides alone.

---

## 3. Core Concepts

### 3.0 The Project (Top-Level Entity)

Everything lives inside a **Project**. A project is not a repo — it's the full lifecycle container.

```
Project: "Acme Checkout Redesign"
├── Status: in_progress
├── Team: [@maria (PM), @carlos (tech lead), @dev1, @dev2]
├── Discovery ──────── (research, spikes, context)
├── Spec ────────────── (functional requirements — the master document)
├── Plans ──────────── (technical plans derived from spec)
├── Sessions ───────── (AI implementation sessions)
├── Code ───────────── (linked repos, commits, PRs)
├── Bugs & Issues ──── (linked back to spec)
└── Timeline ───────── (chronological view of all activity)
```

A user's home screen is a **dashboard of projects** — like GitHub repos but for the full product lifecycle, not just code.

### 3.1 Discovery Phase

Before writing a spec, you **discover**. Lineage structures this:

```
Discovery
├── Research Notes
│   ├── User interview: "Users abandon checkout at step 3"
│   ├── Competitive analysis: "Stripe Checkout does X, Y, Z"
│   └── Technical spike: "Our payment API supports webhooks"
├── Hypotheses
│   ├── H-001: "Reducing steps from 5 to 3 will increase conversion"
│   └── H-002: "Real-time validation reduces abandonment"
├── Constraints identified
│   ├── "Must support mobile (60% of traffic)"
│   └── "PCI compliance required"
└── Decision: Ready to spec ✅
    └── Key findings that feed into the spec are explicitly linked
```

**Why Discovery matters:**
- Forces the team to do homework before jumping to solutions.
- AI assists: "Based on your research notes, here are suggested requirements."
- Creates an audit trail: "Why did we build this?" → trace to discovery research.
- Discovery artifacts are referenceable from the spec: `[ref: D-001]`.

### 3.2 The Spec Document & Master Spec

#### The Master Spec (Stable Branch)

Every project has a **Master Spec** — the single source of truth for "what are we building right now?". Think of it as the `main` branch of functional requirements.

```
Master Spec (stable, approved, the truth)
│
├── Branch: "add-2fa-to-checkout"        ← PM is drafting new requirements
│   └── FR-009: Two-factor auth at payment (draft)
│   └── FR-010: SMS fallback (draft)
│
├── Branch: "simplify-returns-flow"      ← Under review
│   └── FR-003 modified: reduce steps from 4 to 2
│   └── FR-011: auto-refund for items < $50 (new)
│
└── Branch: "q2-performance-targets"     ← Approved, ready to merge
    └── NFR-001 modified: p99 from 2s to 1.5s
    └── NFR-005: CDN caching for static assets (new)
```

**Key rules:**
- The Master Spec is **always deployable** — it represents the current approved functional reality.
- Changes to the spec happen on **branches** (like git branches).
- A branch goes through: `draft → review → approved → merged to master`.
- Merging to master = "this is now officially what the product does."
- **Conflict detection**: if two branches modify the same requirement, the system flags it.

#### The Spec Document Schema

Each requirement in the spec is a structured, versioned document — not free-form prose:

```
Spec Document
├── Metadata (owner, status, version, approvals)
├── Context & Goals
│   └── Problem statement, success metrics, constraints
│   └── Links to Discovery: [D-001, D-003, H-001]
├── Functional Requirements
│   ├── FR-001: User can complete checkout in 3 steps
│   │   ├── Derived from: [H-001, D-research-interview-1]
│   │   ├── Acceptance criteria
│   │   ├── Edge cases
│   │   ├── Status: ✅ implemented
│   │   └── Links: [→ TP-001, → impl:checkout/flow.ts, → BUG-042]
│   ├── FR-002: Real-time field validation
│   │   ├── Derived from: [H-002]
│   │   ├── Status: 🔨 in_progress
│   │   └── ...
│   └── ...
├── Non-Functional Requirements
│   └── NFR-001: Checkout < 2s p99
└── Open Questions / Decisions Log
```

**Key properties:**
- Every requirement has a **unique, stable ID** (FR-001, NFR-001) that persists across versions and branches.
- Requirements **link back to discovery** — why does this requirement exist?
- The Master Spec is **branched like git** — work on branches, merge when approved.
- Each requirement has an individual **status**: draft, approved, plan_generated, in_progress, implemented, verified, deprecated.
- **AI-assisted writing**: LLM drafts requirements from discovery notes, human refines.
- **Collaborative editing** with comments, suggestions, and approval flows.
- **The system enforces**: you can't promote a requirement to a plan unless it's approved in the Master Spec (or an approved branch).

### 3.3 The Spec Dashboard (Spec = Ticket)

The spec is NOT a long document you scroll through. It's a **dashboard of requirement cards** — each requirement is a "ticket" you can act on.

```
┌─────────────────────────────────────────────────────────────────────┐
│  Acme Checkout Redesign — Spec Dashboard                    [main ▼]│
│                                                    Branch: master   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Filter: [All ▼] [Status ▼] [Owner ▼]     Search: [___________]   │
│                                                                     │
│  ┌─ Functional Requirements ────────────────────────────────────┐  │
│  │                                                               │  │
│  │  ┌──────────────────────┐  ┌──────────────────────┐          │  │
│  │  │ FR-001               │  │ FR-002               │          │  │
│  │  │ Checkout in 3 steps  │  │ Real-time validation │          │  │
│  │  │                      │  │                      │          │  │
│  │  │ ✅ Implemented       │  │ 🔨 In Progress      │          │  │
│  │  │ Plan: TP-001         │  │ Plan: TP-002         │          │  │
│  │  │ 2 commits · 0 bugs  │  │ 1 commit · 1 bug     │          │  │
│  │  │                      │  │                      │          │  │
│  │  │ [@carlos] [3 days]   │  │ [@dev1] [today]      │          │  │
│  │  │ [View] [▶ Promote]   │  │ [View] [▶ Promote]   │          │  │
│  │  └──────────────────────┘  └──────────────────────┘          │  │
│  │                                                               │  │
│  │  ┌──────────────────────┐  ┌──────────────────────┐          │  │
│  │  │ FR-003               │  │ FR-004               │          │  │
│  │  │ Order confirmation   │  │ Guest checkout       │          │  │
│  │  │                      │  │                      │          │  │
│  │  │ 📋 Approved          │  │ 📝 Draft             │          │  │
│  │  │ No plan yet          │  │ No plan yet          │          │  │
│  │  │ —                    │  │ —                     │          │  │
│  │  │                      │  │                      │          │  │
│  │  │ [@maria] [1 week]    │  │ [@maria] [today]     │          │  │
│  │  │ [View] [▶ Promote]   │  │ [View] [Edit]        │          │  │
│  │  └──────────────────────┘  └──────────────────────┘          │  │
│  │                                                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─ Non-Functional Requirements ────────────────────────────────┐  │
│  │  ┌──────────────────────┐                                     │  │
│  │  │ NFR-001              │                                     │  │
│  │  │ Checkout < 2s p99    │                                     │  │
│  │  │ 📋 Approved          │                                     │  │
│  │  │ [View] [▶ Promote]   │                                     │  │
│  │  └──────────────────────┘                                     │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  Summary: 4 FR + 1 NFR │ 1 implemented │ 1 in progress │ 3 pending│
│                                                                     │
│  Branches: [master] [add-2fa ●2 new] [simplify-returns ●1 mod]    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Key UX decisions:**

- **Each requirement is a card** — shows status, linked plan, commits, bugs, owner, age.
- **The [▶ Promote] button** — the central action. Click it to promote a spec requirement to a technical plan. Only available when the requirement is in `approved` state.
- **Branch selector** — switch between Master Spec and branches. See what's in draft, what's under review, what's ready to merge.
- **Filterable/searchable** — by status, owner, keyword. For large specs this is essential.
- **Summary bar** — at-a-glance: how many requirements, how many implemented, how many pending.

#### The "Promote to Plan" Flow (UI-Driven)

When a user clicks **[▶ Promote]** on a requirement card:

```
Step 1: Select requirements to include in the plan
┌──────────────────────────────────────────────────┐
│  Promote to Technical Plan                       │
│                                                  │
│  Primary: FR-003 (Order confirmation)            │
│                                                  │
│  Include related requirements?                   │
│  ☑ FR-001 (Checkout in 3 steps) — related       │
│  ☑ NFR-001 (Checkout < 2s p99) — constraint     │
│  ☐ FR-002 (Real-time validation) — suggested    │
│                                                  │
│  [Cancel]                    [Generate Plan →]   │
└──────────────────────────────────────────────────┘

Step 2: AI generates plan draft (loading state, ~30s)
┌──────────────────────────────────────────────────┐
│  Generating Technical Plan...                    │
│                                                  │
│  Reading: FR-003 + related requirements          │
│  Reading: existing codebase (github.com/acme/...)│
│  Analyzing: architecture constraints             │
│  ████████████░░░░░░░░░ 60%                       │
│                                                  │
└──────────────────────────────────────────────────┘

Step 3: Review & edit the generated plan
┌──────────────────────────────────────────────────┐
│  Technical Plan: TP-003 (draft)                  │
│  Derived from: FR-003, FR-001, NFR-001           │
│                                                  │
│  ## Architecture Decisions                       │
│  - Use existing order service, add confirmation  │
│    endpoint (Rationale: reuse > new service)     │
│  - Email via SendGrid (existing integration)     │
│                                                  │
│  ## Implementation Steps                         │
│  1. Add confirmation template to email service   │
│  2. Create POST /orders/:id/confirm endpoint     │
│  3. Add webhook for payment provider callback    │
│  4. Update order status state machine            │
│                                                  │
│  ## Estimated Scope                              │
│  Files: ~4 │ Tests: ~8 │ Complexity: Medium      │
│                                                  │
│  [Edit Plan] [Request Review] [Approve & Lock]   │
└──────────────────────────────────────────────────┘

Step 4: Approved plan → unlocks [▶ Build] button on the card
```

**After promotion, the requirement card updates:**

```
┌──────────────────────┐
│ FR-003               │
│ Order confirmation   │
│                      │
│ 📐 Plan Ready        │   ← status changed
│ Plan: TP-003 ✅      │   ← plan linked
│ —                    │
│                      │
│ [@carlos] [today]    │
│ [View] [▶ Build]     │   ← action changed to Build
└──────────────────────┘
```

### 3.4 The Requirement Lifecycle (Card States)

Each requirement card progresses through a clear lifecycle:

```
📝 Draft ──→ 📋 Approved ──→ 📐 Plan Ready ──→ 🔨 Building ──→ ✅ Implemented ──→ ✔ Verified
                │                                                       │
                │         ← spec branch merged                          │
                │                                                       ↓
                └──── can be re-opened if ────────────────────── 🐛 Has Bugs
                      spec changes or
                      bugs found
```

| State | Meaning | Available Actions |
|-------|---------|-------------------|
| 📝 Draft | Requirement being written | Edit, Delete |
| 📋 Approved | Reviewed & approved in Master Spec (or approved branch) | **▶ Promote to Plan** |
| 📐 Plan Ready | Technical plan generated & approved | **▶ Build** (launch AI session) |
| 🔨 Building | AI agent implementing | Monitor, Pause |
| ✅ Implemented | Code committed, tests passing | Mark Verified, Report Bug |
| ✔ Verified | Human confirmed it works | — (terminal state) |
| 🐛 Has Bugs | Bug linked to this requirement | View Bugs, ▶ Fix Plan |

### 3.5 The Derivation Chain

The core innovation. Every artifact in the system is linked in a directed acyclic graph:

```
Spec (FR-001)
  → Technical Plan (TP-001)
    → Implementation Session (IS-001)  [Claude Code / Codex session]
      → Commits (abc123, def456)
        → Tests (test_signup.py:test_happy_path)
  → Bug Report (BUG-042)
    → Fix Plan (TP-007)
      → Implementation Session (IS-012)
        → Commits (ghi789)
```

This chain enables:
- **Forward traceability**: "What code implements FR-001?" → instant answer.
- **Backward traceability**: "Why does this function exist?" → trace back to the spec requirement.
- **Impact analysis**: "If I change FR-001, what code, tests, and plans are affected?"
- **Coverage analysis**: "Which requirements have no implementation? Which have no tests?"

### 3.6 Technical Plans

A technical plan is a *derived artifact* from one or more spec requirements. It describes *how* something will be implemented.

```
Technical Plan (TP-001)
├── Derived from: [FR-001, FR-002, NFR-001]
├── Architecture decisions
│   └── Decision: Use OAuth2 + magic links (not passwords)
│       ├── Rationale: "Security + UX per FR-001 acceptance criteria"
│       ├── Alternatives considered: [passwords, SSO-only]
│       └── Status: approved
├── Implementation steps
│   ├── Step 1: Create user model + migration
│   ├── Step 2: Implement OAuth2 flow
│   └── Step 3: Email service integration
├── Agent instructions
│   └── Prompt/context to pass to Claude Code / Codex
└── Status: approved → in_progress → implemented → verified
```

**Key properties:**
- Auto-generated draft from the spec using an LLM, then human-reviewed.
- Every decision records *why* and *what alternatives were considered*.
- Versioned independently from the spec (spec v3 might still use plan v1).

### 3.7 Implementation Sessions (The LLM Git)

When an AI agent (Claude Code, Codex, Cursor, etc.) implements a plan, the session is captured:

```
Implementation Session (IS-001)
├── Plan reference: TP-001
├── Agent: Claude Code (claude-opus-4-6)
├── Input context: [spec sections, plan, codebase snapshot]
├── Conversation log (full transcript)
├── Decisions made
│   ├── "Used bcrypt for hashing because plan specified OAuth2"
│   ├── "Created separate email service module (not inline)"
│   └── "Chose connection pooling for DB (not in plan, pragmatic decision)"
│       └── Flag: DEVIATION_FROM_PLAN
├── Artifacts produced
│   ├── Commits: [abc123, def456]
│   ├── Files changed: [auth/signup.ts, db/migrations/001.sql, ...]
│   └── Tests added: [test_signup.py]
└── Verification
    ├── Tests passing: ✅
    └── Spec coverage: FR-001 ✅, FR-002 ⏳, NFR-001 ❌
```

**Key properties:**
- Every agent session is logged, not just the output.
- **Deviations from plan are flagged** — when the agent makes a decision not covered by the plan.
- Spec coverage is computed automatically by tracing the chain.

### 3.8 The Changelog (Spec Evolution)

When the spec changes, the system tracks:

```
Spec Change: FR-001 v2 → v3
├── What changed: "Added 2FA requirement to signup"
├── Changed by: @maria (PM)
├── Impact analysis (auto-computed):
│   ├── Technical Plans affected: [TP-001] → needs update
│   ├── Code affected: [auth/signup.ts, auth/2fa.ts (new)]
│   ├── Tests affected: [test_signup.py] → needs update
│   └── Open bugs affected: [BUG-042] → possibly resolved
└── Action items generated:
    ├── "Update TP-001 to include 2FA flow"
    ├── "Create implementation session for 2FA"
    └── "Re-verify BUG-042 against new spec"
```

---

## 4. The Human Harness Model

### Philosophy: Human Drives, AI Executes

Lineage is explicitly designed as a **harness** — the human holds the reins at every decision point:

```
HUMAN decisions (cannot be delegated):     AI execution (fast, recorded):
──────────────────────────────────────     ───────────────────────────────
"What problem are we solving?"         →   Summarize research, suggest gaps
"What should we build?"                →   Draft spec from discovery notes
"Is this spec correct?"                →   N/A — human judgment only
"How should we build it?"              →   Draft technical plan from spec
"Is this plan sound?"                  →   N/A — human judgment only
"Go build it"                          →   Implement via Claude Code/Codex
"Is this implementation correct?"      →   Run tests, flag deviations
"Ship it"                              →   N/A — human decision only
```

**The harness pattern:**
1. AI proposes, human approves (never the reverse)
2. Every AI output is a *draft* until human-approved
3. The human can override any AI suggestion
4. The system records both the AI proposal and the human decision

---

## 5. User Flows

### Flow 0: Create a Project

```
1. User creates a new Project
   └── Names it, assigns team, links repo(s)
   └── Project starts in "Discovery" phase

2. Project dashboard shows lifecycle status:
   ┌─────────────────────────────────────────────────┐
   │  Acme Checkout Redesign                         │
   │                                                 │
   │  [Discovery] → [Spec] → [Plans] → [Build] → [✓]│
   │    ●active     ○        ○         ○          ○  │
   │                                                 │
   │  Team: @maria @carlos @dev1                     │
   │  Repo: github.com/acme/checkout                 │
   │  Created: 2026-03-18                            │
   └─────────────────────────────────────────────────┘
```

### Flow 1: Discovery → Spec → Plan → Build (Happy Path)

```
1. DISCOVERY (human-driven, AI-assisted)
   └── Team adds research notes, interviews, spikes
   └── AI: "Based on your notes, I see 3 themes: [X, Y, Z]"
   └── Human marks discovery as "ready to spec"

2. SPEC (human writes/approves, AI drafts)
   └── AI drafts requirements from discovery notes
   └── Human refines, adds acceptance criteria
   └── Team reviews. Approval workflow.
   └── ✅ Spec approved → unlocks plan generation

3. PLAN (AI drafts, human approves)
   └── AI reads spec + existing codebase → proposes technical plan
   └── Tech lead reviews architecture decisions
   └── Edits, approves. Plan locked.
   └── ✅ Plan approved → unlocks implementation

4. BUILD (AI executes, human monitors)
   └── Developer selects plan → triggers Claude Code session
   └── Agent receives: spec context + plan + codebase
   └── Session recorded: conversation, decisions, commits
   └── Dashboard shows real-time: "Implementing FR-001... FR-002..."

5. VERIFY (system + human)
   └── Auto: tests pass? Spec coverage computed.
   └── Auto: deviations from plan flagged
   └── Human: reviews implementation against spec
   └── ✅ Verified → spec requirements marked as "implemented"
```

### Flow 2: Bug Fix

```
1. Bug reported (manually or from monitoring)
   └── System suggests: "This might relate to FR-001, FR-003"
        (based on code → plan → spec tracing)

2. Developer confirms spec link
   └── Bug is now: BUG-042 → FR-001

3. Fix plan generated
   └── LLM reads: bug, spec, original plan, original implementation session
   └── Proposes fix with full context of original intent

4. Fix implemented & traced
   └── Fix commits link back to BUG-042 → FR-001
   └── Spec dashboard shows: "FR-001: 1 bug fixed, 0 open"
```

### Flow 3: Spec Change (Ripple Effect)

```
1. PM updates a requirement in the spec

2. System computes impact
   └── "3 technical plans affected, 12 files, 4 test suites"

3. For each affected plan:
   └── LLM proposes plan update (diff)
   └── Tech lead reviews

4. For each updated plan:
   └── Implementation session with full context of what changed and why
```

---

## 6. Architecture (High Level)

```
┌──────────────────────────────────────────────────────────┐
│                    Lineage Cloud                         │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ Discovery│  │   Spec   │  │   Plan   │  │ Session │ │
│  │ Workspace│  │  Editor  │  │  Engine  │  │ Recorder│ │
│  │          │  │(collab + │  │(LLM-based│  │(agent   │ │
│  │(notes,   │  │ version) │  │ planning)│  │ adapter)│ │
│  │ research)│  │          │  │          │  │         │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬────┘ │
│       │              │              │              │      │
│  ┌────┴──────────────┴──────────────┴──────────────┴───┐ │
│  │            Derivation Graph Engine                   │ │
│  │  (DAG: discovery → spec → plan → session → code)    │ │
│  └─────────────────────┬───────────────────────────────┘ │
│                        │                                  │
│  ┌─────────────────────┴───────────────────────────────┐ │
│  │              Project Store                           │ │
│  │  (git-like versioning for ALL project artifacts)     │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌─────────────────────────────────────────────────────┐ │
│  │              Integrations                            │ │
│  │  GitHub │ Claude Code │ Codex │ Linear │ Slack      │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌─────────────────────────────────────────────────────┐ │
│  │              Project Dashboard & Analytics           │ │
│  │  (lifecycle status, coverage, drift, health)         │ │
│  └─────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

### Key Technical Components

1. **Project Store** — Git-inspired storage for ALL project artifacts (not just code). Discovery notes, specs, plans, session logs — all versioned with branching, diffing, and merge support. Preserves semantic structure (requirement IDs, links) across versions.

2. **Derivation Graph** — A persistent DAG that tracks relationships between all artifacts across the full lifecycle. Enables impact analysis, coverage queries, and traceability in both directions. The key query: "given any artifact, show me everything connected to it."

3. **Agent Adapter Layer** — Middleware that injects spec+plan context into AI agent sessions and captures everything back: conversation logs, decisions made, deviations from plan, commits produced.

4. **Discovery Workspace** — Structured space for pre-spec research. Not a blank document — prompts the team to capture interviews, hypotheses, constraints, spikes. AI summarizes and suggests themes.

5. **Spec Editor** — Collaborative editor (Notion meets GitHub). Structured authoring with schema enforcement and approval workflows. AI drafts from discovery, human refines.

6. **Project Dashboard** — The "cockpit" view. Where is each project in its lifecycle? What's the spec coverage? Which requirements have no implementation? Which have bugs?

---

## 7. What Makes This Different

| Existing Tool | What it does | What it misses |
|---------------|-------------|----------------|
| **Notion/Docs** | Write specs | No versioning, no code link, specs rot |
| **Jira/Linear** | Track tasks | Tickets ≠ specs, no traceability to intent |
| **GitHub** | Version code | No spec layer, no project lifecycle |
| **Claude Code/Codex** | Generate code | No record of why, no spec context, ephemeral sessions |
| **Confluence** | Document decisions | Dead docs, no live links |
| **Vercel v0 / Bolt** | Prototype from prompts | No spec, no plan, no traceability, toy to prod gap |

### The positioning gap

```
                    Strategic ("why")
                         │
                    Product Strategy (no tool owns this well)
                         │
              ┌──────────┴──────────┐
              │      LINEAGE        │  ← THIS IS THE GAP
              │  Discovery → Spec   │
              │  → Plan → Build     │
              │  (all connected)    │
              └──────────┬──────────┘
                         │
                    Code ("how")
                         │
                    GitHub + Claude Code + Codex
```

**Lineage is the workbench between strategy and code.** It's where thinking becomes building, with full traceability.

---

## 8. MVP Scope (v0.1)

**Target user:** Solo developer or small team (2-5) using Claude Code.

For the first version:

1. **Project creation** — Create a project, link a GitHub repo, invite collaborators.

2. **Lightweight Discovery** — Add research notes (markdown). AI summarizes and extracts themes/hypotheses. Mark as "ready to spec."

3. **Spec Dashboard** — The primary UI. Requirements displayed as cards with status, owner, linked plans, commits, and bugs. Filterable and searchable. Branch selector to switch between Master Spec and working branches.

4. **Master Spec + Branching** — The Master Spec as stable branch. Create branches to draft new requirements or modify existing ones. Review and merge flow (like a PR for specs).

5. **Promote to Plan (from UI)** — Click [▶ Promote] on an approved requirement card. Select related requirements. AI generates a technical plan draft. Human reviews, edits, approves. Plan links back to the requirement card.

6. **Build from Plan (from UI)** — Click [▶ Build] on a plan-ready card. Launches a Claude Code session with spec + plan context injected. Session recorded and linked. Card status updates in real-time.

7. **Spec Versioning** — Full version history per requirement and per branch. Diff viewer between versions. Impact notifications when a merged spec change affects existing plans.

8. **Basic Traceability** — From any card: see discovery notes → spec → plan → commits. Forward and backward navigation.

### Explicitly NOT in MVP:
- Multi-agent support (Codex, Cursor, etc.) — Claude Code only
- Automated spec-from-code (reverse engineering)
- CI/CD integration
- Advanced analytics / drift detection
- Bug tracking integration (manual linking only)
- Parallel branches with conflict resolution (simple linear merges only in v0.1)

---

## 9. Success Metrics

| Metric | Target |
|--------|--------|
| Spec coverage | >80% of requirements have linked implementations |
| Spec freshness | Specs updated within 1 week of code changes |
| Bug traceability | >60% of bugs linked to a spec requirement |
| Plan accuracy | <20% of implementation sessions flag major deviations |
| Time to context | Developer can understand "why" of any code in <2 min |

---

## 10. Open Questions

1. **Storage model**: Do we build our own version store, or use git under the hood with a structured overlay? The branching model for Master Spec feels very git-like — could we literally use git for specs?

2. **Granularity of traceability**: Requirement level (FR-001) or acceptance criteria level (FR-001.AC-3)? How deep does the card go?

3. **Agent-agnostic vs agent-specific**: MVP is Claude Code only. But should the plan schema be agent-neutral from day one?

4. **Pricing model**: Per-seat (like Notion)? Per-project? Per-session? Usage-based on LLM calls for plan generation?

5. **Spec card detail**: How much info on the card vs. the detail view? Cards that are too dense become noisy. Cards that are too sparse lose the "dashboard" feel.

6. **Branch permissions**: Can anyone create a spec branch, or only certain roles? Who can merge to Master?

7. **Promote granularity**: Promote one requirement at a time, or a group? Can a single plan span multiple requirements? (Current design says yes — is that right?)

8. **Offline/local mode**: Does this need to work offline, or is cloud-only acceptable for MVP?

---

## 11. Risks

| Risk | Mitigation |
|------|------------|
| Adoption friction (forcing spec-first) | Gradual enforcement: suggest → nudge → require |
| Specs become bureaucracy | Keep specs lightweight. Templates, not essays. LLM assists writing. |
| LLM hallucination in plans | Plans are always drafts requiring human approval |
| Over-engineering the DAG | Start with simple parent-child links, evolve to full DAG |
| Integration complexity | MVP: Claude Code only. One integration done well. |

---

## 12. Name Candidates

- **Lineage** (used in this doc) — the chain from idea to code, the ancestry of every decision
- **Derive** — specs derive plans derive code
- **Chronicle** — the recorded history of decisions
- **Workbench** — where humans build with AI tools
- **Tracer** — emphasizes traceability
- **Provenance** — the origin story of every line of code

---

## 13. Competitive Moat

The moat isn't any single feature. It's the **network effect of the derivation graph**:

1. The more projects you run through Lineage, the richer the graph becomes.
2. The graph enables increasingly powerful queries: "Across all our projects, which types of specs produce the most bugs?" "Which architectural patterns lead to the most plan deviations?"
3. Over time, AI suggestions improve because they're trained on your team's actual discovery→spec→plan→code patterns.
4. **Switching cost**: your entire product decision history lives here. This is stickier than a code editor.

---

*This is a living document.*
*v0.2 — added project-as-repository model, discovery phase, human harness pattern.*
*v0.3 — added Spec Dashboard (spec=ticket), Master Spec with branching, Promote-to-Plan UI flow, requirement lifecycle states.*
