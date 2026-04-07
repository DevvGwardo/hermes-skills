---
name: brain-agent-failure-recovery
category: software-development
description: Handle brain_swarm/brain_wake agent failures — detect silent spawn failures, use failure as diagnostic data, fall back to direct analysis.
---

# Brain Agent Failure Recovery

Use when brain_swarm or brain_wake agents go stale at "spawned by swarm; initializing" or fail to produce output.

## When to use

- Spawned brain agents show status "working" but progress stays at "spawned by swarm; initializing"
- Agents go stale (>60s) without any heartbeat or post
- You need the analysis/work done and agents aren't delivering
- You want to diagnose WHY brain agents are failing

## Detection Pattern

After spawning agents with brain_swarm or brain_wake:
1. Wait 30-45 seconds
2. Call `brain_agents` — check for stale agents with heartbeat_age > 45s
3. If agents are stale at "spawned by swarm; initializing", they silently failed

## Failure Root Causes (brain-mcp headless spawn)

The headless spawn in `src/index.ts` (swarm tool, ~line 1120-1156):
- Creates a detached bash script that runs `hermes chat -q <prompt> -Q` or `claude -p <prompt>`
- Uses `stdio: 'ignore'` — errors are invisible
- Writes output to `/tmp/brain-agent-<sessionId>.log`
- If the process dies immediately, no log is created
- The session is pre-registered as "working" BEFORE spawn — so failed spawns become ghost "working" sessions that persist in the DB

Common causes:
- CLI (`hermes` or `claude`) not found in spawned process PATH
- Prompt too large for shell argument
- Workspace copy/symlink issues (isolation mode)
- Missing env vars in spawned process

## Recovery Steps

### Step 1: Confirm failure (30s after spawn)
```
brain_agents  → check for stale agents with heartbeat_age > 45s
brain_inbox   → check if any agent DM'd before dying (rare)
```

### Step 2: Fall back to direct analysis
Don't re-spawn — do the work yourself:
- Read the target files directly with read_file
- Use search_files for pattern analysis
- Check /tmp/brain-agent-*.log for any partial output
- Post findings to brain channel yourself

### Step 3: Use the failure as diagnostic data
The fact that agents failed IS a finding:
- Check if this is the known 90% failure pattern
- Note which CLI was used (hermes vs claude)
- Record in brain context_push for future reference
- Save to persistent memory if it reveals a new failure mode

### Step 4: Don't pre-register as "working"
If modifying brain-mcp spawn logic, register as "queued" first:
- Only mark "working" after first successful heartbeat
- This prevents ghost sessions from polluting metrics

## Diagnostics

Check spawned agent logs:
```bash
ls -la /tmp/brain-agent-*.log /tmp/brain-prompt-*.txt /tmp/brain-swarm-*.sh 2>/dev/null
```

Check if hermes CLI is available:
```bash
which hermes && hermes --version
```

Test a minimal spawn manually:
```bash
cd <workspace> && env BRAIN_DB_PATH=... BRAIN_ROOM=... BRAIN_SESSION_ID=test BRAIN_SESSION_NAME=test hermes chat -q "echo test" -Q 2>&1
```

## What NOT to do

- Don't keep re-spawning agents hoping it will work — it's likely the same root cause
- Don't wait indefinitely (>2 min) — agents that haven't started by 60s won't start
- Don't ignore the failure — it's diagnostic data about the system
