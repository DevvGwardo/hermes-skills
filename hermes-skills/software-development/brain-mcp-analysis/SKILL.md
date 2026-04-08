---
name: brain-mcp-analysis
description: Analyze and improve the brain-mcp codebase — current state, known issues, and refactoring approach.
version: 1.0.0
---

# Brain-MCP Analysis & Improvement

## Repo Location
`/Users/devgwardo/brain-mcp/` — TypeScript MCP server, `@devvgwardo/brain-mcp` v1.0.0.

## Current Architecture State (as of 2026-04-07)

### The Dead Module Problem
`src/tools/` contains 6 "extracted" modules that are **NOT imported by index.ts**:
- `tools/identity.ts` — register, sessions, status
- `tools/messaging.ts` — post, read, dm, inbox
- `tools/state.ts` — set, get, keys, delete
- `tools/claims.ts` — claim, release, claims
- `tools/swarm.ts` — swarm, wake, respawn
- `tools/admin.ts` — clear, incr, counter, compact

These files exist but index.ts still has all 55 tool registrations inline (3143 lines, 136KB). The extraction was started but never wired up — **dead code duplication**.

### Critical: How to Detect This Pattern
When auditing a "partial refactoring" or "in-progress extraction":
1. Don't just check if extracted files exist — that gives false confidence
2. Grep for actual imports: `grep "import.*tools" src/index.ts`
3. If nothing found, the extraction is incomplete regardless of how many files exist
4. Run `node -e` with regex to enumerate all `server.tool('name')` registrations and compare against what's in the extracted files

### Remaining Extractions (11 groups still inline in index.ts)
- heartbeat (pulse, agents)
- barriers (wait_until, barrier_reset)
- contracts (contract_set, contract_get, contract_check)
- gate (gate, auto_gate)
- context (context_push, context_get, context_summary, checkpoint, checkpoint_restore)
- memory (remember, recall, forget)
- plan (plan, plan_next, plan_update, plan_status)
- workflow (workflow_compile, workflow_apply, workflow_run)
- metrics (metrics, metric_record) — note: `brain_metrics` and `brain_metric_record` are separate aliases
- router (route)
- git (commit, pr, clean_branches)
- security (security_scan)
- feature (feature_dev)

### Spawn Recovery Bug
`src/spawn-recovery.ts` line 477 still uses `stdio: 'ignore'` — this means stderr/stdout from spawned agents are discarded. If an agent fails immediately (bad CLI, missing env, oversized prompt), the failure is silent. The retry logic exists but can't classify errors it never sees.

**Fix:** Change to `stdio: ['pipe', 'pipe', 'pipe']`, capture stderr in the startup check callback.

### Watchdog State
`src/watchdog.ts` (397 lines) has active respawn logic, ghost detection, temp file cleanup. However, it runs as a separate detached process — check if it's actually running with `ps aux | grep watchdog | grep brain`. As of last check, only the main server process was running (PID 8402).

### Key Files
- `src/index.ts` — 3143 lines, main server, all 55 tool registrations
- `src/db.ts` — 66KB BrainDB (better-sqlite3 wrapper)
- `src/spawn-recovery.ts` — 605 lines, retry/backoff/escalation
- `src/watchdog.ts` — 397 lines, detached watchdog process
- `src/gate.ts` — integration gate (tsc + contracts)
- `src/workflow.ts` — workflow compiler
- `src/conductor.ts` — workflow runtime conductor
- `src/renderer.ts` — output rendering

### DB Location
`~/.claude/brain/brain.db` (SQLite via better-sqlite3)

### Build & Verify
```bash
cd /Users/devgwardo/brain-mcp
npx tsc --noEmit   # type check
npm run build      # compile to dist/
```

## Improvement Plan

### Phase 1: Wire Up Existing Modules
Import the 6 existing tools/ modules into index.ts, remove duplicate inline registrations. Verify `npx tsc --noEmit` passes.

### Phase 2: Extract Remaining Modules
Create and wire the remaining 11+ tool groups. Each module exports `register{Name}Tools(server, options)` per the convention in ARCHITECTURE.md.

### Phase 3: Fix Spawn stdio
Change `stdio: 'ignore'` to piped stdio in spawn-recovery.ts. Capture stderr for error classification.

### Phase 4: Verify
- `npx tsc --noEmit` passes
- All 55 tools still registered (no regressions)
- Spawn test with a known-bad command shows error in logs

## Pitfalls
- The extracted modules may have drifted from index.ts versions — diff before wiring
- `brain_metrics`/`brain_metric_record` are separate tool names from `metrics`/`metric_record` — both exist as aliases
- The `options` interface passed to register functions is defined in ARCHITECTURE.md and includes mutable refs (sessionId, sessionName)
- `src/tools/swarm.ts` is 24KB — the largest extracted module, contains wake/respawn which depend on tmux and spawn-recovery
