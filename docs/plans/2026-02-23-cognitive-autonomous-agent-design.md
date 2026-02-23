# Cognitive Autonomous Agent — Design Document

**Date:** 2026-02-23
**Status:** Approved
**Language:** Python
**Runtime:** Async (asyncio)
**Persistence:** Required (agent survives restarts)
**Osma SDK:** Used for creating agents, tools, and messaging on the fly

---

## Theoretical Foundations

This architecture draws from 7 established theories of cognition, each contributing a specific capability:

| Theory | Contribution |
|---|---|
| **Global Workspace Theory** (Baars, 1988) | Central orchestration loop — many specialists, one broadcast workspace |
| **SOAR** (Newell, 1990) | 3-part long-term memory + impasse-driven sub-goal creation |
| **ACT-R** (Anderson, 1993) | Activation-based memory retrieval (recency + frequency + context) |
| **BDI** (Bratman, 1987) | Commitment to plans — persist unless there's reason to reconsider |
| **System 1/2** (Kahneman, 2011) | Adaptive reasoning depth — fast for routine, slow for novel |
| **Society of Mind** (Minsky, 1986) | Multi-agent decomposition — intelligence from many simple specialists |
| **Active Inference** (Friston, 2006) | Drives as predictions about preferred states, not explicit goals |

Reference framework: **CoALA** (Cognitive Architectures for Language Agents, Sumers et al., 2023).

---

## 1. Core Architecture — The Cognitive Loop

The agent runs a 5-phase cognitive loop inspired by Boyd's OODA loop + SOAR's reflect/chunk mechanism:

```
┌────────────────────────────────────────────┐
│            AUTONOMOUS AGENT                │
│                                            │
│   ┌────────────────────────────────────┐   │
│   │        COGNITIVE LOOP              │   │
│   │                                    │   │
│   │   1. PERCEIVE                      │   │
│   │      What changed since last wake? │   │
│   │      New tasks? Human responses?   │   │
│   │      Sub-agent results? Events?    │   │
│   │               │                    │   │
│   │   2. ORIENT                        │   │
│   │      Retrieve relevant memories    │   │
│   │      Prioritize across all tasks   │   │
│   │      Assess drive pressures        │   │
│   │               │                    │   │
│   │   3. REASON  (← Strategy here)     │   │
│   │      Pluggable: ReACT, Judge, etc  │   │
│   │      Receives CognitiveContext     │   │
│   │      Returns list[CognitiveAction] │   │
│   │               │                    │   │
│   │   4. ACT                           │   │
│   │      Execute actions returned by   │   │
│   │      the Strategy (sequentially    │   │
│   │      or in parallel as applicable) │   │
│   │               │                    │   │
│   │   5. REFLECT                       │   │
│   │      Did it work? Update memory    │   │
│   │      Learn patterns (procedural)   │   │
│   │      Should I continue or sleep?   │   │
│   │               │                    │   │
│   │      ───► loop or sleep ◄───       │   │
│   └────────────────────────────────────┘   │
│                                            │
│   Memory ──── Agency ──── Drives           │
│                   │                        │
│              Wakefulness                   │
└────────────────────────────────────────────┘
```

**Key principle:** The Strategy only controls step 3 (REASON). Everything else — perception, memory retrieval, action execution, reflection — is infrastructure that any strategy can rely on.

### Cognitive Cycle Decision: Continue or Sleep

After REFLECT, the agent evaluates:
- Are there active tasks that can make progress? → Continue loop
- Are all tasks blocked/completed and no drives are active? → Sleep
- Self-wake scheduled? → Sleep until wake condition

---

## 2. Memory Architecture

Based on SOAR's 3-part LTM taxonomy + ACT-R's activation-based retrieval.

### Working Memory

The agent's "consciousness" — limited capacity, pruned each cycle.

```python
@dataclass
class WorkingMemory:
    current_task: Task | None               # The task being reasoned about
    perceptions: list[Perception]           # What just happened
    scratchpad: list[Thought]               # Intermediate reasoning
    active_context: dict[str, Any]          # Key-value context for current cycle
```

### Long-Term Memory (Persistent)

Survives restarts. Three distinct stores:

**Episodic Memory** — "What happened"
- Records of past task executions, their outcomes, and the reasoning chain
- Each episode: (task_description, actions_taken, outcome, timestamp)
- Retrieval weighted by recency + relevance to current context

**Semantic Memory** — "What I know"
- Domain knowledge, facts, entity relationships
- Populated from task context, external sources, and human input
- Graph-structured or document-based

**Procedural Memory** — "How to do things"
- Compiled patterns: "when I see situation X, action Y usually works"
- Tool usage patterns, strategy preferences per task type
- From ACT-R: frequent multi-step patterns compile into single-step automaticities
- Example: after successfully using "search → filter → summarize" 5 times, this becomes a compiled procedure

### Retrieval Engine

Not just vector similarity. Uses ACT-R's base-level activation equation:

```
Activation(memory_i) = ln(Σ t_j^{-d}) + ContextBoost + Noise
```

Where:
- `t_j` = time since the j-th access of this memory
- `d` = decay parameter (~0.5)
- `ContextBoost` = spreading activation from working memory contents
- `Noise` = small random perturbation (prevents deterministic retrieval)

Memories that are **recent**, **frequently used**, and **contextually relevant** are easier to retrieve.

---

## 3. Strategy Interface

The Strategy is the pluggable reasoning engine. Stateless between invocations — all state lives in working memory.

### Input: CognitiveContext

```python
@dataclass
class CognitiveContext:
    working_memory: WorkingMemory
    perceptions: list[Perception]           # What just changed
    active_tasks: list[Task]                # All tasks with current states
    retrieved_memories: list[Memory]         # Relevant LTM from Orient step
    drive_pressures: dict[str, float]       # Which drives are active and how strong
```

### Output: list[CognitiveAction]

```python
CognitiveAction = Union[
    Execute(tool_call: ToolCall),            # Do something directly
    Delegate(agent_config: AgentConfig),     # Spawn a full sub-agent
    Dispatch(worker_task: WorkerTask),       # Spawn a lightweight worker
    AskHuman(question: str, context: dict),  # Request human input (blocks task)
    UpdateTask(task_id: str, status: str, result: Any),
    Think(thoughts: list[str]),              # Internal reasoning → working memory
    Sleep(wake_condition: WakeCondition),    # Go dormant
    Impasse(type: ImpasseType, details: dict),  # Signal stuck
]
```

A Strategy returns **one or more actions** per invocation. The cognitive loop executes them (in parallel where possible).

### Example Strategies

**ReACTStrategy** — Reason → Act → Observe loop:
- Generates a thought about what to do
- Returns Execute or Delegate actions
- Next cycle observes results, reasons again
- Best for: step-by-step tool usage

**JudgeStrategy** — Evaluate → Score → Decide:
- Evaluates the situation holistically
- Scores possible actions
- Returns the highest-scored action
- Best for: decision-making, prioritization

**TreeOfThoughtStrategy** — Branch → Evaluate → Prune → Expand:
- Generates multiple possible paths (Think actions)
- Evaluates branches
- Prunes bad ones, expands promising ones
- Best for: complex planning with uncertainty

**Future strategies** plug in by implementing the same `(CognitiveContext) → list[CognitiveAction]` interface.

---

## 4. Agency — Delegation & Impasse Resolution

Based on Society of Mind (multi-agent) + SOAR (impasse-driven sub-goals).

### Delegation Engine

Three delegation mechanisms:

**spawn_agent(config) → AutonomousAgent**
- Creates a full autonomous agent with its own cognitive loop, memory, strategy, and wakefulness
- Memory initially seeded from parent's relevant context
- Independent lifecycle — runs on its own schedule
- Use case: complex sub-problems requiring autonomy
- Example: "Research this topic thoroughly and report back"

**spawn_worker(task) → Worker**
- Lightweight, single-purpose executor
- No cognitive loop — just execute and return
- No independent memory, no ability to spawn further
- Use case: well-defined, bounded tasks
- Example: "Call this API and return the result"

**ask_human(question, context) → HumanRequest**
- Suspends the specific task, NOT the agent
- Question delivered via Osma's messaging layer
- When human responds, task unblocks and next cognitive cycle picks it up
- Agent continues working on other tasks while waiting

### Impasse Detection (SOAR)

The agent doesn't just delegate when told to. It **detects when it's stuck**:

| Impasse Type | Signal | Resolution |
|---|---|---|
| **InformationImpasse** | "I don't know X" | ask_human() or spawn_agent(research) |
| **CapabilityImpasse** | "I can't do X" | spawn_worker() with right tool, or ask_human() |
| **DecisionImpasse** | "I can't choose between A and B" | ask_human() for preference, or spawn_agent(evaluator) |
| **ResourceImpasse** | "This is too complex for one step" | Decompose into sub-tasks, spawn agents/workers |

### Coordination

- Parent-child relationship tracking
- Async, non-blocking result collection
- Escalation: child can escalate back to parent on failure
- BDI commitment: once delegated, don't re-do the work unless the child reports failure

---

## 5. Drives

Based on Active Inference: drives are **predictions about preferred states**, not explicit goals. The agent acts to reduce the gap between its expectations and reality.

| Drive | Prediction | Activates When |
|---|---|---|
| **TaskDrive** | "My task queue should be empty" | Pending tasks exist |
| **CuriosityDrive** | "I should have the information I need" | Information gaps detected |
| **CompletionDrive** | "Started tasks should reach completion" | Blocked or stalled tasks exist |
| **CoherenceDrive** | "My understanding should be consistent" | Contradictory information detected |

Drives are **naturally self-regulating**: when there's nothing to do, no drive activates, and the agent sleeps. Custom drives can be injected via configuration for domain-specific motivations.

Drive pressures are computed each cycle during ORIENT and passed to the Strategy as part of CognitiveContext.

---

## 6. Wakefulness

Configurable modes that determine when the agent's cognitive loop runs:

**ScheduledWake** — Classic heartbeat. Wakes every N seconds/minutes.
- Good for: monitoring, periodic checking, background processing.

**EventWake** — Wakes in response to external events:
- New task assigned
- Human responded to a question
- Sub-agent/worker completed
- Osma message received

**SelfWake** — The agent programs its own wake-up:
- "I delegated X, wake me in 5 minutes to check on it"
- "This task needs review tomorrow morning"
- Decided during REFLECT phase

All three modes can coexist. Configuration decides which are active.

---

## 7. Task Model

The Task is the unit of work. The agent's TaskQueue holds all tasks.

### Structure

```python
@dataclass
class Task:
    # Identity
    id: str
    parent_task_id: str | None              # For sub-tasks
    source: TaskSource                       # human | parent_agent | self

    # Content
    description: str
    context: dict[str, Any]
    acceptance_criteria: str | None
    priority: float                          # Drive-weighted importance

    # State
    status: TaskStatus                       # pending|active|blocked|completed|failed|cancelled
    blocked_by: str | None                   # task_id | human_request_id | agent_id
    blocked_reason: str | None

    # Execution History
    attempts: list[TaskAttempt]              # (timestamp, action_taken, result)
    delegations: list[Delegation]            # (agent_id|worker_id, status)
    human_requests: list[HumanRequest]       # (question, response, timestamp)

    # Relationships
    depends_on: list[str]                    # Task IDs
    blocks: list[str]                        # Task IDs
    subtasks: list[str]                      # Task IDs
```

### Task Lifecycle

```
pending ──► active ──► completed
   │          │            │
   │          ▼            ▼
   │       blocked      failed
   │          │
   │          ▼
   └──►  cancelled
```

- **pending**: in queue, not yet started
- **active**: currently being worked on
- **blocked**: waiting on something (human, sub-agent, dependency)
- **completed**: done, with result
- **failed**: attempted but could not complete
- **cancelled**: no longer needed

---

## 8. Osma SDK Integration

The Osma SDK is used as the foundational communication and creation layer:

- **Messaging**: Human-in-the-loop questions and responses flow through Osma
- **Agent Creation**: spawn_agent() uses Osma to create new agent instances
- **Tool Creation**: The agent can create new tools on the fly via Osma when it detects a CapabilityImpasse
- **Event Delivery**: EventWake triggers come through Osma's event system

The AutonomousAgent does NOT embed Osma — it uses Osma as an SDK/client. The cognitive architecture is independent; Osma provides the infrastructure.

---

## 9. Persistence & State Recovery

The agent's state must survive process restarts:

**What is persisted:**
- All tasks (full state including execution history)
- Long-term memory (episodic, semantic, procedural)
- Agent configuration and current strategy
- Wakefulness schedule (pending self-wake timers)
- Parent-child agent relationships

**What is NOT persisted:**
- Working memory (reconstructed from perceptions on wake)
- Current cycle state (the loop restarts from PERCEIVE)

**Recovery behavior:**
On restart, the agent wakes, runs PERCEIVE (which discovers its existing tasks and their states), and resumes the cognitive loop as if it had just woken from sleep.

---

## 10. Python Interface Overview

```python
# Configuration
agent = AutonomousAgent(
    strategy=ReACTStrategy(),
    memory_store=PostgresMemoryStore(...),
    osma_client=OsmaClient(...),
    wakefulness=[
        ScheduledWake(interval=timedelta(minutes=5)),
        EventWake(sources=["osma"]),
    ],
    drives=[TaskDrive(), CuriosityDrive(), CompletionDrive()],
)

# Start the agent
await agent.start()

# Submit a task
await agent.submit_task(Task(
    description="Analyze the Q4 sales report and summarize key findings",
    context={"report_url": "..."},
    acceptance_criteria="A 3-paragraph summary with key metrics",
))

# The agent runs autonomously from here.
# It will perceive the new task, reason about it,
# and may ask humans, spawn sub-agents, or create tools as needed.
```

---

## Design Principles

1. **Strategy is just reasoning** — The Strategy has no side effects. It receives context, returns actions. The cognitive loop handles execution.
2. **Impasses drive growth** — When stuck, the agent doesn't fail silently. It detects the impasse type and resolves it through delegation, research, or human input.
3. **Drives, not goals** — The agent is motivated by prediction errors (gap between expected and actual state), not by explicit goal-chasing. This makes it naturally self-regulating.
4. **Memory is earned** — Only information that passes through the cognitive loop gets stored in LTM. Peripheral data is forgotten, just like human cognition.
5. **Domain-agnostic** — The architecture knows nothing about any specific domain. Domain knowledge is injected through configuration (tools, prompts, semantic memory, custom drives).
6. **Composable agents** — A sub-agent is the same abstraction as the parent, enabling recursive composition for arbitrarily complex tasks.
