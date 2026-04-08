---
name: brain-mcp-analysis
description: Analyze and improve the brain-mcp codebase — current state, known issues, and refactoring approach.
version: 2.0.0
---

# Brain-MCP Analysis & Improvement

## Repo Location
`/Users/devgwardo/brain-mcp/` — TypeScript MCP server, `@devvgwardo/brain-mcp` v1.0.0.

## Current Architecture State (as of 2026-04-07, post-refactoring)

### Refactoring Complete: Modules Wired
`src/index.ts` reduced from 3143 lines → 599 lines (~80% reduction). All 18 tool modules now imported and wired via `registerXxxTools(server, options)`:

| Module | Tools | Extra Options Needed |
|--------|-------|---------------------|
| context | context_push, context_get, context_summary, checkpoint, checkpoint_restore | base toolOptions |
| memory | remember, recall, forget | base toolOptions |
| plan | plan, plan_next, plan_update, plan_status | base toolOptions |
| heartbeat | pulse, agents, respawn | compactMode, startLeadWatchdog, renderTool |
| contracts | contract_set, contract_get, contract_check | base toolOptions |
| gate | gate, auto_gate | base toolOptions |
| admin | clear, incr, counter, compact | compactMode, setCompactMode |
| metrics | brain_metrics, brain_metric_record, metrics, metric_record, compact | compactMode, setCompactMode, reply |
| identity | register, sessions, status | sessionId, sessionName, setSessionId, setSessionName |
| messaging | post, read, dm, inbox | sessionName |
| state | set, get, keys, delete | base toolOptions |
| claims | claim, release, claims | base toolOptions |
| swarm | swarm, wake, respawn | sessionName, sessionId, minimalAgentPrompt, startLeadWatchdog |
| router | route, wake | router (TaskRouter instance) |
| git | commit, pr, clean_branches | base toolOptions |
| security | security_scan | base toolOptions |
| feature-dev | feature_dev | sessionName, startLeadWatchdog |
| workflow | workflow_compile, workflow_apply, workflow_run | sessionName, startLeadWatchdog, minimalAgentPrompt |

### Still Inline (2 tools)
- `wait_until` — barrier primitive (no module extracted)
- `barrier_reset` — barrier cleanup (no module extracted)

### Spawn Recovery Fix Applied
`src/spawn-recovery.ts` line 476: changed `stdio: 'ignore'` → `stdio: ['ignore', 'pipe', 'pipe']` so spawned processes capture stdout/stderr for debugging.

## Key Lessons from Refactoring

### 1. Verify Actual State Before Planning
The summary claimed 6 modules were "already wired" but they weren't — only 3 (context, memory, plan) had register calls. Always grep for `registerXxxTools(` to confirm, don't trust summaries.

### 2. Module Options Vary
Not all modules take `toolOptions` alone. Some need:
- `compactMode` / `setCompactMode` — admin, metrics
- `sessionName` / `sessionId` — identity, messaging, swarm, feature-dev, workflow
- `startLeadWatchdog` — heartbeat, swarm, feature-dev, workflow
- `minimalAgentPrompt` — swarm, workflow
- `reply` — metrics (for compact output)
- `renderTool` — heartbeat
- `router` (TaskRouter) — router-tools

Check each module's exported interface: `grep -A20 "interface.*Options" src/tools/*.ts`

### 3. Duplicate Tool Registration
Both `admin.ts` and `metrics.ts` register `compact`. This is a conflict — only one should own it. Prefer admin.ts since it also has clear/incr/counter.

### 4. Brain Agent Spawns Fail Silently
With `stdio: 'ignore'`, spawned agents that crash immediately produce no output. The 90% ghost session rate was caused by this. The fix enables stderr capture but the spawn-recovery logic also needs to read it.

### 5. File Size Reduction Strategy
- Extract tools to modules with `register{Name}Tools(server, options)` pattern
- Each module owns its own schemas and handler logic
- index.ts becomes orchestration only: imports, options, register calls, server start

## Build & Verify
```bash
cd /Users/devgwardo/brain-mcp
npx tsc --noEmit   # type check
npm run build      # compile to dist/
```

## Remaining Work
- Extract barriers module for `wait_until` and `barrier_reset`
- Run `npx tsc --noEmit` to verify no compile errors
- Smoke test: start server, confirm all 55 tools register
- Remove duplicate `compact` registration (admin vs metrics)

## Key Files
- `src/index.ts` — 599 lines, orchestration only
- `src/db.ts` — 66KB BrainDB (better-sqlite3 wrapper)
- `src/spawn-recovery.ts` — 605 lines, retry/backoff/escalation (stdio fixed)
- `src/watchdog.ts` — 397 lines, detached watchdog process
- `src/gate.ts` — integration gate (tsc + contracts)
- `src/tools/*.ts` — 18 extracted tool modules

## DB Location
`~/.claude/brain/brain.db` (SQLite via better-sqlite3)
