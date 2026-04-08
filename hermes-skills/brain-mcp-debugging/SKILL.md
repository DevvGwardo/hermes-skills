---
name: brain-mcp-debugging
category: devops
description: Debug and fix brain-mcp issues — systematic testing, common failure patterns, and source locations.
---

# Brain-MCP Debugging Guide

Use when brain-mcp tools behave unexpectedly, the integration gate fails, or you need to verify system health.

## Source Location

Brain-mcp source: `~/brain-mcp/src/`
Key files:
- `src/db.ts` — BrainDB class (state, counters, DMs, contracts, claims, sessions, barriers)
- `src/gate.ts` — Integration gate (TSC, contract validation, test detection, behavioral checks, performance baselines)
- `src/tools/messaging.ts` — post, read, dm, inbox tools
- `src/tools/state.ts` — set, get, keys, delete tools
- `src/tools/admin.ts` — incr, counter, compact, clear, sessions tools
- `src/tools/claims.ts` — claim, release, claims tools
- `src/tools/contracts.ts` — contract_set, contract_get, contract_check tools
- `src/index.ts` — Main server, tool registrations, spawn logic (~3100 lines)

## Systematic Testing Steps

1. **Basic health**: `mcp_brain_status` — check session, room, PID, heartbeat
2. **Agents**: `mcp_brain_agents` — check for stale/failed agents
3. **Contracts**: `mcp_brain_contract_check` — verify provides/expects alignment
4. **Shared state**: `mcp_brain_keys` — inspect state store
5. **Claims**: `mcp_brain_claims` — check for zombie claims
6. **Gate (dry run)**: `mcp_brain_gate(dry_run=true)` — run full integration gate
7. **Edge cases**:
   - DM to nonexistent session — should return error (see Fix #1 below)
   - Counter on missing key — should return `{ value: 0, found: false }` (see Fix #2)
   - Double-claim by same owner — refreshes TTL (expected behavior)

## Common Failure Patterns & Fixes

### Fix #1: DM to nonexistent session (messaging.ts)

**Symptom**: `dm` to a fake session ID returns `{ ok: true }` silently.
**Root cause**: `sendDM()` inserts into DB without validating target session exists.
**Fix location**: `src/tools/messaging.ts` — add session validation before `db.sendDM()`:

```typescript
const targetExists = sessions.some(s => s.id === targetId);
if (!targetExists) {
  return reply({ ok: false, error: `Target session '${to}' not found.` });
}
```

### Fix #2: Counter indistinguishable from missing key (db.ts)

**Symptom**: `get_counter` returns `0` for both "not initialized" and "actually zero".
**Root cause**: `get_counter` returned just a number, no `found` flag.
**Fix location**: `src/db.ts` — change return type from `number` to `{ value: number; found: boolean }`:

```typescript
get_counter(key: string, scope: string): { value: number; found: boolean } {
  const entry = this.db.prepare('SELECT value FROM state WHERE key = ? AND scope = ?').get(key, scope);
  if (!entry) return { value: 0, found: false };
  return { value: parseInt(entry.value, 10) || 0, found: true };
}
```

**IMPORTANT**: Changing this return type requires updating ALL callers:
- `src/pi-core-tools.ts` — brain_counter tool
- `src/index.ts` — inline counter tool
- `src/tools/admin.ts` — counter tool
- `src/test-harness.ts` — test assertions (`.value === N`)

### Fix #3: Gate test detection picking up wrong files (gate.ts)

**Symptom**: Gate reports 63+ test failures from `.cloudchat/`, `.codex/worktrees/`, and unrelated projects.
**Root cause**: `detectTestCommand` used `find .` from the room CWD (`/Users/devgwardo`), searching the entire home directory. Also, `vitest.config` checks lacked file extensions.
**Fix location**: `src/gate.ts` — replace `detectTestCommand` with:

1. Add `findProjectRoot(cwd)` — walks up directories looking for `package.json` with `scripts.test`
2. Rewrite `detectTestCommand` to use project root, check vitest/jest configs with extensions (`.ts`, `.js`, `.mts`, `.mjs`), parse test script for framework hints
3. Update `runTests` to execute from `projectRoot` instead of `cwd`
4. Update `runGate` to use `projectRoot` for TSC checks too

## Critical: MCP Server Restart Required

The MCP server loads compiled JS at startup — it does NOT hot-reload. After making changes:

1. `cd ~/brain-mcp && npm run build`
2. Kill stale processes: `pkill -f 'brain-mcp/dist/index'`
3. Restart the MCP server from Claude's MCP config

TypeScript compilation (`npx tsc --noEmit`) validates syntax but doesn't mean the running server has your changes.

## Vitest Detection

The gate's `findProjectRoot` walks UP from CWD (not down), looking for the nearest `package.json` with a `test` script. If the room is `/Users/devgwardo` and no `package.json` there has a test script, it returns null and gate reports "no test framework detected" (which is correct behavior — not a false failure).
