---
name: brain-swarm-workflow
description: Run a complete multi-agent feature development sprint using brain MCP — plan tasks, spawn agents via brain_swarm, validate with brain_gate, and consolidate results. Works with brain_feature_dev for complex work or brain_swarm directly for parallel task execution.
version: 1.0.0
author: Hermes Agent
tags: [brain-mcp, multi-agent, swarm, orchestration, feature-development]
related_skills: [brain-mcp-integration, brain-agent-monitor, writing-plans, subagent-driven-development]
---

# Brain Swarm Workflow

## Overview

Run complete multi-agent feature development using brain MCP. Spawn parallel agents that coordinate via shared state, validate their work through the integration gate, and consolidate results into a deliverable.

This skill covers the full lifecycle:
1. **Plan** — decompose work into parallel-ready tasks
2. **Spawn** — dispatch agents via brain_swarm
3. **Gate** — validate integration with brain_gate
4. **Consolidate** — collect results and report

Use `brain_feature_dev` when you want automated phase gating. Use this skill when you need manual control over the swarm or want to understand what's happening under the hood.

## When to Use

- Multi-file feature implementations (3+ files, 2+ agents)
- Parallel workstreams that can proceed independently
- When the user says "swarm", "multi-agent", "in parallel", "with N agents"
- Feature development where different agents handle different layers (API, UI, tests, etc.)

**Don't use when:**
- Single-file or single-agent tasks (use `subagent-driven-development` directly)
- Research-only tasks (use `mcp_claude_code_research` instead)
- Tasks requiring back-and-forth with the user (stays in the main session)

## Prerequisites

```text
# Verify brain MCP is healthy before starting
mcp_brain_brain_status     # Returns room info and session count
mcp_brain_brain_agents    # Shows active agents with status
```

If these fail, check the brain MCP connection before proceeding.

## Phase 1: Plan the Work

### 1. Analyze the scope

Before spawning agents, understand:
- How many distinct files or layers are involved?
- Which tasks can run truly in parallel (no shared files)?
- Which tasks have dependencies (must run sequentially)?

### 2. Create the task plan

Use `brain_plan` to set up task dependencies:

```text
mcp_brain_brain_plan tasks=[
  {
    "name": "define-types",
    "description": "Define TypeScript interfaces for the feature",
    "depends_on": []
  },
  {
    "name": "implement-api",
    "description": "Implement API routes and business logic",
    "depends_on": ["define-types"]
  },
  {
    "name": "implement-ui",
    "description": "Build UI components",
    "depends_on": ["define-types"]
  },
  {
    "name": "write-tests",
    "description": "Write unit and integration tests",
    "depends_on": ["implement-api", "implement-ui"]
  }
]
```

Returns a `plan_id`. Use `brain_plan_next` to get tasks that are ready to work on (all dependencies satisfied).

### 3. Assign agents to tasks

Each agent gets **different files** — never assign the same file to two agents. Use `brain_claim` before editing.

## Phase 2: Spawn the Swarm

### Option A: Use brain_swarm (recommended for feature dev)

```text
mcp_brain_brain_swarm
  task="Complete feature: [description]"
  agents=[
    {"name": "types-worker", "files": ["src/types.ts"], "task": "Define TypeScript interfaces for [feature]"},
    {"name": "api-worker", "files": ["src/api.ts"], "task": "Implement API routes for [feature]"},
    {"name": "ui-worker", "files": ["src/ui.tsx"], "task": "Build UI components for [feature]"}
  ]
  layout="tiled"  # Or "headless" for background
```

This automatically: registers as lead, creates task plan, spawns all agents, starts watchdog.

### Option B: Use brain_wake for manual control

```text
mcp_brain_brain_wake
  name="types-worker"
  task="Define TypeScript interfaces for [feature]. Read src/types.ts, implement the types."
  layout="horizontal"
```

Spawn one at a time or in parallel. Monitor with `brain_agents`.

### Key rules for spawned agents

Each agent should:
1. `brain_register` with their name
2. `brain_get` the shared context key
3. `brain_claim` files before editing
4. `brain_release` files when done
5. `brain_post` their results
6. `/exit` when finished

## Phase 3: Monitor and Gate

### Monitor progress

```text
mcp_brain_brain_agents           # List all active agents
mcp_brain_brain_read             # Read channel messages
mcp_brain_brain_inbox since_id=N # Check for DMs
```

### Run integration gate

When agents report "done", validate with:

```text
mcp_brain_brain_gate dry_run=true    # Check for type errors, no notifications
mcp_brain_brain_gate notify=true     # Full gate — DMs agents their errors
```

Gate catches: type errors, missing imports, param mismatches between agents.

### Retry failed agents

```text
mcp_brain_brain_respawn
  agent_name="api-worker"
  extra_context="The gate found a type mismatch in line 42. Fix it."
```

## Phase 4: Consolidate Results

### Collect agent results

```text
mcp_brain_brain_read channel="general"
```

Read all agent posts to get their work summaries.

### Save to memory

```text
mcp_brain_brain_remember
  key="cloud-chat-hub-brain-integration"
  category="architecture"
  content="Three-layer integration for cloud-chat-hub:
- Bridge layer: hermes-bridge/main.py handles brain MCP calls
- Gateway: localhost:18789 for evolution system
- Hub: localhost:5174 for agent coordination"
```

### Report to user

Summarize:
- What each agent did
- What the gate validated
- Any remaining work
- Next steps

## Common Patterns

### Pattern 1: Three-layer decomposition (cloud-chat-hub pattern)

Used for API + bridge + integration work:

```
architect → defines types and interfaces (first, no deps)
           ↓
implementor-agent → reads architect's output, implements the feature
           ↓
gateway-worker → evolution system integration
```

**Actual swarm from cloud-chat-hub:**
```text
brain_swarm
  task="Improve Hermes integration for cloud-chat-hub"
  agents=[
    {"name": "architect", "task": "Create three-layer integration map for hermes-bridge/main.py"},
    {"name": "implementor-agent", "task": "Implement the integration improvements in hermes-bridge/main.py"}
  ]
  layout="horizontal"
```

### Pattern 2: Parallel independent workers

For truly independent files (no shared state):

```
worker-a → src/auth/login.ts
worker-b → src/auth/session.ts  
worker-c → src/auth/passwords.ts
```

Full parallel — no dependencies between them.

### Pattern 3: Review and refine

After initial implementation:

```
implementer → first pass at all files
reviewer → brain_wake a reviewer to check quality
          ↓
implementer → addresses reviewer feedback
```

## Self-Healing Tips

### Agent not responding or stale

```text
# Check if it's stale (stopped heartbeating)
mcp_brain_brain_agents include_stale=true

# Get specific errors from gate first
mcp_brain_brain_gate --dry_run true

# Respawn with error context
mcp_brain_brain_respawn
  agent_name="implementor-agent"
  extra_context="Fix: [specific error from gate]"
```

### Gate failures

1. Dry run first: `brain_gate --dry_run true`
2. Identify which files have errors
3. `brain_dm` each agent their specific errors
4. Let them fix (2-3 min)
5. Re-run gate

### Context lost during swarm

```text
# Restore last checkpoint
mcp_brain_brain_checkpoint_restore

# Read recent context entries
mcp_brain_brain_context_get limit=30

# Check what each agent was working on
mcp_brain_brain_read channel="general"
```

### Claims blocking progress

```text
# See who's holding what
mcp_brain_brain_claims current_room=true

# Release a stuck claim (if agent exited without releasing)
mcp_brain_brain_release resource="src/api.ts"
```

## Workflow Summary

```
1. Plan:    brain_plan with task dependencies
2. Spawn:   brain_swarm (auto) or brain_wake (manual)
3. Monitor: brain_agents + brain_read
4. Gate:    brain_gate --dry_run → brain_gate --notify
5. Consolidate: collect results + brain_remember
6. Report:  summarize to user
```

## Related Skills

- `brain-mcp-integration` — replace stubbed functions with real brain agent calls (concrete implementation guide)
- `brain-agent-monitor` — display agent status with cron jobs
- `writing-plans` — create detailed implementation plans for agents
- `subagent-driven-development` — single-agent task execution

## Notes

- Agents auto-exit when done (panes close cleanly)
- Spawned agents run with `--dangerously-skip-permissions` automatically
- For 3+ agents, pass `layout: "tiled"` for the best grid view
- brain_swarm auto-registers as lead — no need to call brain_register manually for the lead
- Always dry_run gate before running with notifications
- The architect should run first, then post its output so subsequent agents can read it

## Ghost Sessions — Status Display Can Lie

When spawning headless agents via `brain_wake`, the named session entry stays at "queued" with "spawn queued; waiting for first heartbeat" even after the actual process starts working. The real agent gets a separate `session-XXXXX` entry that shows "working".

**Symptom:** `brain_agents` shows your named agents as "queued" or "stale" but work is actually happening under anonymous session IDs.

**Diagnosis:** Check the agent log files directly:
```python
# Log path is returned by brain_wake, or find them:
import glob
logs = glob.glob("/tmp/brain-agent-*.log")  # or /var/folders/... on macOS
```

**Implication:** Don't trust "queued" status for headless agents. Cross-reference with `brain_read` for posted results and check logs. This is a pre-registration gap — the session is registered before the process confirms it started.

## Using brain_wait_until for Synchronization

For "wait for N agents to finish" scenarios, `brain_wait_until` works as a barrier but agents must explicitly call it. For passive monitoring, polling `brain_agents` + `brain_read` every 30-60s is more reliable. If results are slow to appear, check log files — agents may be reading large files before posting.

## Recording Metrics

After agents complete, record outcomes with `brain_metric_record` for future model routing decisions:
```text
brain_metric_record agent_name="..." task_description="..." outcome="success" duration_seconds=N
```

## Stale Context Recovery (critical)

When restoring a brain-context from a previous session, check the journal first:

```bash
# Always check stale context BEFORE spawning
mcp_brain_brain_get "swarm:task"           # What was being worked on
mcp_brain_brain_get "swarm-context"        # Prior context summary
mcp_brain_brain_get "__brain_stale_agents__"  # Prior agents still listed?

# Read the workflow journal
read_file("~/workflow-journal/LATEST.md")
```

A previous session's context block is a snapshot — agents listed there may have exited or never finished. Don't assume their work is complete. Use the findings/files already produced (e.g. `AGENTS.md` with architect-findings and reviewer-findings) as your starting point, not the prior swarm task description.

## Dual Brain Integration Modes

When the target project has brain MCP integration already (even partial), identify which mode it uses BEFORE delegating:

| Mode | How | Used in |
|---|---|---|
| **Subprocess RPC** | `asyncio.create_subprocess_exec` + raw JSON-RPC over stdio | `main.py` |
| **HTTP gateway** | `httpx` calls to `localhost:18789` | `hermes_adapter.py` |

Both use `_brain_` prefixed helpers but differ in transport. HTTP mode is for fire-and-forget pooled caching (cross-session state). RPC mode is for full tool access (brain_set, pulse, claim, wake). Mixing them up causes silent failures — make sure agents know which mode applies to their file.

## Wrapper Refactor Trap

A common failure mode when refactoring: introducing wrapper functions (e.g. `_mark_request_started()`) but leaving stale inline code at the call site. Causes `UnboundLocalError` because the old code still references module globals without declaring `global`.

Detection: grep for the old inline code near where the wrapper is now called. Look for `_bridge_total_requests +=` or `_update_bridge_metrics` calls that overlap with wrapper responsibilities.

Prevention: delete the old inline block in the same commit that adds the wrapper.
