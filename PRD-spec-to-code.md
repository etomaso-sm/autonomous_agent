# PRD: Lineage — The Human-Driven, AI-Powered Project Platform

**Version:** 0.2 (Draft)
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

### 3.2 The Spec Document (Master Document)

A structured, versioned document that describes *what* the system should do. Not free-form prose — it has a schema:

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
│   │   └── Links: [→ TP-001, → impl:checkout/flow.ts, → BUG-042]
│   ├── FR-002: Real-time field validation
│   │   ├── Derived from: [H-002]
│   │   └── ...
│   └── ...
├── Non-Functional Requirements
│   └── NFR-001: Checkout < 2s p99
└── Open Questions / Decisions Log
```

**Key properties:**
- Every requirement has a **unique, stable ID** (FR-001, NFR-001) that persists across versions.
- Requirements **link back to discovery** — why does this requirement exist?
- The document is **versioned like git** — branches, diffs, merges, history.
- Sections can be in different **states**: draft, review, approved, implemented, deprecated.
- **AI-assisted writing**: LLM drafts requirements from discovery notes, human refines.
- **Collaborative editing** with comments, suggestions, and approval flows.
- **The system enforces**: you can't create a technical plan without an approved spec.

### 3.2 The Derivation Chain

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

### 3.3 Technical Plans

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

### 3.4 Implementation Sessions (The LLM Git)

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

### 3.5 The Changelog (Spec Evolution)

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

3. **Spec Editor** — Create and version functional specs with structured requirements (IDs, acceptance criteria). Markdown-based with schema enforcement. AI drafts from discovery notes.

4. **Plan Generation** — Given an approved spec, AI generates a technical plan. Human review + approval workflow. Decision log with rationale.

5. **Claude Code Integration** — Launch a Claude Code session with spec + plan context injected. Capture the session log and link commits to the plan.

6. **Project Dashboard** — Lifecycle status per project. Basic derivation chain view: Discovery → Spec → Plan → Commits. Forward and backward navigation.

7. **Spec Versioning** — Linear version history for specs. Diff viewer. Impact notifications when spec changes.

### Explicitly NOT in MVP:
- Multi-agent support (Codex, Cursor, etc.) — Claude Code only
- Automated spec-from-code (reverse engineering)
- CI/CD integration
- Advanced analytics / drift detection
- Branching/merging of specs (linear versioning only)
- Bug tracking integration (manual linking only)

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

1. **Storage model**: Do we build our own version store, or use git under the hood with a structured overlay? (Git has great tooling but isn't designed for structured docs.)

2. **Granularity of spec IDs**: Requirement level? Acceptance criteria level? How fine-grained should traceability go?

3. **Agent-agnostic vs agent-specific**: How much do we invest in being agent-agnostic (supporting any LLM tool) vs going deep with one (Claude Code)?

4. **Pricing model**: Per-seat (like Notion)? Per-spec? Per-session? Usage-based on LLM calls?

5. **Spec language**: Pure Markdown? A DSL? Visual editor? How structured vs flexible?

6. **Enforcement model**: Do we *hard-block* code without a spec, or just strongly encourage? (Hard-block is purer but adoption friction is higher.)

7. **Collaboration model**: Who owns the spec? One owner or collaborative like Google Docs? What's the approval flow?

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

*This is a living document. v0.2 — added project-as-repository model, discovery phase, human harness pattern. Let's iterate.*
