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

### Fix #4: Renderer shows "0 claims" for agents with claims (renderer.ts)

**Symptom**: `brain_agents` output shows "0 claims" even when agents have claimed files. Agent boxes render but claim counts are always wrong.
**Root cause**: `renderer.ts` line 286 checked `a.held_claims` but `db.getAgentHealth()` returns `a.claims` (the `AgentHealth` type has `claims: string[]`, not `held_claims`).
**Fix location**: `src/renderer.ts` line 286 — replace:
```typescript
const claims = a.held_claims?.length ? `${a.held_claims.length} claims` : '0 claims';
```
with:
```typescript
const claimList = a.claims ?? a.held_claims ?? [];
const claims = claimList.length ? `${claimList.length} claim${claimList.length !== 1 ? 's' : ''}` : '0 claims';
```
**Testing gap**: The existing `brain_agents` test only covered compact mode. Add tests for:
- Full renderer with `claims` array from DB
- `held_claims` fallback path
- STALE label for stale agents
- Claim count display (singular vs plural)

**Verification**: Run `npx tsx src/renderer.test.ts` then test with realistic data:
```javascript
node -e "
const { renderTool } = './dist/renderer.js';
console.log(renderTool('brain_agents', JSON.stringify({
  total: 1, working: 0, done: 0, failed: 0, stale: 0,
  agents: [{ name: 'test', status: 'idle', heartbeat_age_seconds: 5,
    claims: ['src/a.ts', 'src/b.ts'], is_stale: false }]
})));
"
```
Should show "2 claims", not "0 claims".

## Vitest Detection

The gate's `findProjectRoot` walks UP from CWD (not down), looking for the nearest `package.json` with a `test` script. If the room is `/Users/devgwardo` and no `package.json` there has a test script, it returns null and gate reports "no test framework detected" (which is correct behavior — not a false failure).

## Renderer Testing Pattern

When debugging renderer issues, test the full pipeline — don't rely on compact-mode-only tests:

1. **Direct renderer test**: Feed realistic data matching DB output shape into `renderTool()` via `node -e`
2. **Check field alignment**: The DB type (`AgentHealth`, `Session`, etc.) defines the actual field names. Compare against what the renderer reads — `held_claims` vs `claims` was a real bug.
3. **Always test non-compact**: Compact mode bypasses the renderer. If compact works but full doesn't, the renderer has a bug.
4. **Strip ANSI for assertions**: `result.replace(/\x1b\[[0-9;]*[a-zA-Z]/g, '')` before checking content in tests.

### Fix #5: better-sqlite3 NODE_MODULE_VERSION mismatch

**Symptom**: Heartbeat fails with `exit=0` — `hermes mcp test brain` returns "✗ Connection closed". stderr shows `ERR_DLOPEN_FAILED` with "NODE_MODULE_VERSION X vs Y" mismatch.

**Root cause**: `better-sqlite3` was compiled for a different Node.js version than the one brain-mcp actually runs with. Common on macOS with both nvm node and homebrew node installed — they have different module versions (e.g. v22=127, v24=137).

**How to diagnose**:
```bash
# Check which node brain-mcp uses (from config):
grep -A5 "brain:" ~/.hermes/config.yaml | grep command

# Check what node compiled better-sqlite3:
node -e "require('better-sqlite3')" 2>&1  # run from system node
/Users/devgwardo/.nvm/versions/node/v22.22.1/bin/node -e "require('better-sqlite3')" 2>&1  # test nvm node

# Check hermes test output for the actual error:
/Users/devgwardo/.local/bin/hermes mcp test brain 2>&1
```

**Fix**: Rebuild for the node version that brain-mcp actually uses, then update config if needed.

```bash
# 1. Identify which node is configured:
#    ~/.hermes/config.yaml → mcp_servers.brain.command

# 2. Rebuild better-sqlite3 for THAT node:
cd ~/brain-mcp
npm rebuild better-sqlite3   # uses whatever `node` is on PATH

# 3. Verify with the configured node path:
/opt/homebrew/bin/node -e "require('better-sqlite3')"  # should print nothing (success)

# 4. If rebuild used the wrong node, explicitly use the right one:
/opt/homebrew/bin/node -e "require('child_process').execSync('npm rebuild better-sqlite3', {cwd: '/Users/devgwardo/brain-mcp', stdio: 'inherit'})"

# 5. Test:
/Users/devgwardo/.local/bin/hermes mcp test brain 2>&1
# Should show: ✓ Connected
```

**Gotcha**: `which node` and the config command can disagree. Always rebuild using the exact node binary from `mcp_servers.brain.command` in config.yaml. If the config points to nvm node but system node is default, they'll have different module versions.

**If you change the config command**: The MCP server won't pick up the change until the next tool call triggers a respawn. Kill the current brain-mcp process to force a restart.

## Critical: MCP Server Restart Required

The MCP server loads compiled JS at startup — it does NOT hot-reload. After making changes:

1. `cd ~/brain-mcp && npx tsc` (builds to dist/)
2. Kill stale processes: `pkill -f 'brain-mcp/dist/index'`
3. Hermes will auto-respawn the MCP server on next tool call (may take 3-5s)
4. If MCP tools return `ClosedResourceError`, wait 5s and retry — the server is restarting

**Do NOT kill the MCP server from within a hermes session unless you're prepared for a brief outage.** The server respawns but the first tool call after kill will fail with `ClosedResourceError`.

## Post-Fix Full Verification Checklist

After any fix (especially native module rebuilds, config changes, or process cleanup), run through this full verification before declaring victory:

### 1. Process Cleanup
```bash
# Kill stale brain-mcp processes — only the newest should survive
ps aux | grep 'brain-mcp/dist/index' | grep -v grep
# Kill all but the most recent by PID
kill <old_pids>
```

### 2. Native Module Verification
```bash
# Must load from the brain-mcp directory (relative native bindings)
cd ~/brain-mcp && /opt/homebrew/bin/node -e "require('better-sqlite3')" 
# Silent output = success. Any error = still broken.
```

### 3. Config Alignment
```bash
# Config node command must match the node that compiled native modules
grep -A5 "brain:" ~/.hermes/config.yaml | grep command
# Compare with:
/opt/homebrew/bin/node -e "console.log(process.version)"
```

### 4. Brain Tool Health
```
mcp_brain_status          — should show 1 session, recent heartbeat
mcp_brain_agents          — check for stale/failed agents
mcp_brain_contract_check  — should return 0 mismatches
mcp_brain_claims          — should be clean (no zombie claims)
mcp_brain_keys            — look for stale state keys worth cleaning
```

### 5. Integration Gate (full)
```
mcp_brain_gate(dry_run=true) — all categories should pass:
  - tsc: passed or skipped (no tsconfig.json is OK if using tsx)
  - contracts: PASS
  - behavioral: all 5 checks pass
  - performance: all baselines pass
```

### 6. Metrics & History
```
mcp_brain_metrics — verify recent tasks succeeded, no failures
```

### 7. Cron Jobs
```
cronjob list — verify brain-heartbeat and brain-overseer are enabled
and last_run_at shows recent successful runs
```

### 8. Stale State Cleanup
Shared state often accumulates stale keys after crashes/rebuilds:
- `__brain_stale_agents__` — leftover from agent cleanup
- `swarm-task`, `swarm-beta-alive` — old swarm sessions
- `gate-behavioral-*` — old gate run artifacts

Use `mcp_brain_delete` to clean these up.

### 9. DB Location Sanity Check
```bash
# BrainDB defaults to 'brain.db' in the MCP server's CWD
# CWD is typically the room path (e.g. /Users/devgwardo)
# Check: ls -lh /Users/devgwardo/brain.db
# If BRAIN_DB_PATH env is set, check that path instead
grep "BRAIN_DB" ~/.hermes/config.yaml
```

### 10. Heartbeat Log Confirmation
```bash
tail -10 ~/.hermes/brain_heartbeat.log
cat ~/.hermes/brain_heartbeat.status  # should say "OK"
```

**Common gotcha**: The `hermes mcp test brain` command only checks basic connectivity. It can show "✓ Connected" while deeper issues (stale processes, stale state, misaligned DB) remain. Always run the full gate + agent check, not just the connection test.

### Fix #6: Fast-completing agents marked as failed (spawn-recovery.ts)

**Symptom**: Spawned agents complete their tasks successfully (messages appear in channel, DONE confirmed) but DB status shows `failed`. `brain_agents` output shows `✗ failed` instead of `✓ done`. Agents appear STALE/QUEUED.

**Root cause**: `waitForStartup()` in `src/spawn-recovery.ts` has a 1500ms `STARTUP_GRACE_MS` timer. If the spawned process exits before that timer fires, the `onExit` handler always returned `started: false` — even with exit code 0. Hermes agents complete fast (register → post → done in seconds), so they exit before 1500ms, and the code treated a clean exit as a spawn failure. Then `spawnWithRecovery` calls `db.pulse(agentSessionId, 'failed', ...)` based on `startup.started === false`.

**How to diagnose**:
```bash
# Check the brain DB directly
sqlite3 ~/.claude/brain/brain.db \
  "SELECT name, status, last_heartbeat FROM sessions ORDER BY created_at DESC LIMIT 10"
# Agents with 'failed' status but who posted DONE messages = this bug

# Cross-reference with channel messages
# If agent posted "✅ DONE" but DB says "failed" — confirmed
```

**Fix location**: `src/spawn-recovery.ts` line ~433, `dist/spawn-recovery.js` line ~308

In the `onExit` handler, add early return for exit code 0:

```typescript
const onExit = (code: number | null) => {
  earlyExitCode = code ?? -1;
  if (earlyExitCode === 0) {
    // Process completed successfully before startup grace — fast agent
    finish({ started: true });
    return;
  }
  const failure = readFailureDetails(logFile, exitCodeFile);
  finish({
    started: false,
    exitCode: failure.exitCode ?? earlyExitCode,
    error: failure.error ?? `exited with code ${failure.exitCode ?? earlyExitCode}`,
  });
};
```

**Note**: Must patch BOTH `src/spawn-recovery.ts` (source) and `dist/spawn-recovery.js` (compiled, what the server actually runs). The MCP server does NOT hot-reload — changes take effect on next swarm/wake call that re-imports the module.

## CLI Agent Listing via SQLite

The `~/.hermes/show_brain_agents.sh` script was a stub that looked for `/tmp/brain-agent-*` temp files. A proper version queries the brain SQLite DB directly:

```bash
#!/bin/bash
DB="$HOME/.claude/brain/brain.db"
sqlite3 -header -column "$DB" \
  "SELECT name, status, pid,
   CAST((julianday('now') - julianday(last_heartbeat)) * 86400 AS INTEGER) as age_sec
   FROM sessions
   WHERE last_heartbeat > datetime('now', '-5 minutes')
   ORDER BY last_heartbeat DESC"
```

**DB location**: `~/.claude/brain/brain.db` (default from `BrainDB` constructor: `join(homedir(), '.claude', 'brain', 'brain.db')`). Can be overridden with `BRAIN_DB_PATH` env var.

**Useful queries**:
```bash
# Active sessions (heartbeat within 5 min)
sqlite3 ~/.claude/brain/brain.db \
  "SELECT name, status, pid, last_heartbeat FROM sessions WHERE last_heartbeat > datetime('now', '-5 minutes')"

# Recent messages
sqlite3 ~/.claude/brain/brain.db \
  "SELECT id, sender_name, substr(content,1,80), created_at FROM messages ORDER BY id DESC LIMIT 10"

# Active claims
sqlite3 ~/.claude/brain/brain.db \
  "SELECT resource, owner_id FROM claims"

# Shared state keys
sqlite3 ~/.claude/brain/brain.db \
  "SELECT key, value, updated_by FROM state"
```
