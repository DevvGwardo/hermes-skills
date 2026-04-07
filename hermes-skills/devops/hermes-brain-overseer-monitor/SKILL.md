---
name: hermes-brain-overseer-monitor
description: Monitor the health of the Hermes Brain MCP system using the overseer script
category: devops
---
## Overview
Monitor the health of the Hermes Brain MCP system using the brain overseer monitoring approach. This skill provides a systematic approach to locate, execute, and interpret the brain overseer heartbeat monitoring by examining log files, status files, and the overseer script logic. The primary overseer is a shell script (`brain_overseer.sh`) that runs every 2 minutes via cron. It checks the freshness of the heartbeat status file and logs results to `brain_overseer.log`. A separate heartbeat script (`brain_heartbeat.sh`) runs every minute to directly test Brain MCP responsiveness.

**Critical note:** The `show_agents.py` script often fails with `ModuleNotFoundError: No module named 'hermes_tools'` because the hermes_tools package isn't in the Python path when run standalone. Rely on direct script execution and log analysis instead.

## When to Use
- Checking if the Brain MCP system is responsive
- Investigating system health alerts
- Verifying cron job execution for brain MCP monitoring
- Standard overseer scripts are not available or not executing

## Prerequisites
Monitor the health of the Hermes Brain MCP system using the brain overseer script and associated heartbeat monitoring tools. This skill provides a systematic approach to locate, execute, and interpret the brain overseer heartbeat monitoring by examining log files, status files, and the overseer script logic.

## Steps

### 1. Locate the brain overseer script and verify installation
```bash
# Check if the overseer script exists
ls -la ~/.hermes/brain_overseer.sh

# Check heartbeat script
ls -la ~/.hermes/brain_heartbeat.sh

# Verify log and status files exist
ls -la ~/.hermes/brain_overseer.log ~/.hermes/brain_heartbeat.log ~/.hermes/brain_heartbeat.status
```

All four files should exist. The overseer and heartbeat scripts should be executable.

### 2. Run the overseer check directly
```bash
~/.hermes/brain_overseer.sh
echo "Exit code: $?"
```

The script always exits with code 0 (it logs issues, doesn't fail). Check the log immediately after:
```bash
tail -5 ~/.hermes/brain_overseer.log
```

**Expected healthy output:** `OVERSEER HEARTBEAT_FRESH: Heartbeat is being updated regularly`

### 3. Check current heartbeat status and recent activity
```bash
# Current status
cat ~/.hermes/brain_heartbeat.status

# Recent heartbeat checks (last 20 lines)
tail -20 ~/.hermes/brain_heartbeat.log
```

The heartbeat script runs every minute and produces `HEARTBEAT_OK` or `HEARTBEAT_FAIL` entries.

### 4. Verify file freshness (critical for detecting stale monitoring)
```bash
# Check modification times to ensure monitoring is active
now=$(date +%s)
stat -f %m ~/.hermes/brain_heartbeat.status | xargs -I{} echo "status: $(( (now - {}) / 60 )) minutes old"
stat -f %m ~/.hermes/brain_heartbeat.log | xargs -I{} echo "log: $(( (now - {}) / 60 )) minutes old"
stat -f %m ~/.hermes/brain_overseer.log | xargs -I{} echo "overseer: $(( (now - {}) / 60 )) minutes old"
```

All files should be less than 3 minutes old. A stale `brain_heartbeat.status` with a fresh overseer log indicates the heartbeat script may be running slowly or getting stuck.

### 5. Check cron job configuration (for historical/verification purposes)
```bash
# List cron jobs
hermes cron list

# Or inspect the jobs JSON directly - note the structure has a "jobs" wrapper
python3 -c "import json; data=json.load(open('$HOME/.hermes/cron/jobs.json')); print(json.dumps([j for j in data['jobs'] if 'heartbeat' in j['name'].lower() or 'overseer' in j['name'].lower()], indent=2))"
```

Key jobs to verify:
- `brain-heartbeat` (schedule: `* * * * *`) - runs every minute
- `brain-overseer` (schedule: `*/2 * * * *`) - runs every 2 minutes

### 6. Interpret health from logs and status

### 6. Interpret health from logs and status files

**Overseer log patterns:**
- `OVERSEER HEARTBEAT_FRESH` — heartbeat file updated within 2.5 minutes (healthy)
- `OVERSEER HEARTBEAT_STALE` — no recent updates (warning)
- `OVERSEER LAST_STATUS: OK` with STALE — heartbeat mechanism partially functional but not updating frequently enough
- `OVERSEER RECENT_FAILURES:` followed by timestamps — shows historical failures, useful for spotting intermittent issues

**Heartbeat log patterns:**
- `HEARTBEAT_OK` — MCP responded within timeout (healthy)
- `HEARTBEAT_FAIL` — MCP unresponsive after retries (unhealthy)
- Clusters of failures followed by recovery indicate transient issues

**Status file:**
- `OK` — last successful check (may be stale if file not updated)
- Other values indicate specific error states

**File freshness cross-check:**
- Fresh `brain_overseer.log` + fresh `brain_heartbeat.log` + fresh `brain_heartbeat.status` = healthy monitoring system
- Fresh overseer + stale status file = heartbeat script not completing (possible hang)
- Stale overseer log = cron job not running

**Key insight:** Transient failures are common. A single or small cluster of `HEARTBEAT_FAIL` entries followed by `HEARTBEAT_OK` does not necessarily indicate a problem requiring action. Look for sustained failure patterns.

### 7. Troubleshooting

**Overseer script fails to run or missing:**
- Verify `~/.hermes/brain_overseer.sh` exists and is executable (`chmod +x`)
- Check cron daemon is running: `pgrep cron` or `systemctl status cron`
- Inspect cron job definition: `hermes cron list` should show `brain-overseer` job

**show_agents.py unreliable:**
- Do not rely on `show_agents.py` for critical health checks — it frequently fails with `ModuleNotFoundError: No module named 'hermes_tools'` due to missing PYTHONPATH configuration.
- The direct script + log analysis approach is more reliable.

**Persistent `HEARTBEAT_FAIL` entries:**
- Check if Brain MCP server process is running
- Review MCP server logs (location varies by installation)
- Consider restarting the hermes agent or MCP services
- Look for resource constraints (CPU, memory, disk space)

**Stale files (no updates for >5 minutes):**
- Overseer log stale: cron job not executing — check cron daemon and job configuration
- Heartbeat log stale but overseer fresh: heartbeat script may be hanging — check if `brain_heartbeat.sh` is running
- Status file stale with fresh logs: heartbeat script completing but MCP calls timing out

### 8. Complete Health Assessment Checklist

- [ ] `brain_overseer.sh` exists and is executable
- [ ] `brain_heartbeat.sh` exists and is executable
- [ ] All three files (status, heartbeat log, overseer log) modified within last 3 minutes
- [ ] Overseer log shows `HEARTBEAT_FRESH` on most recent check
- [ ] Heartbeat log shows predominantly `HEARTBEAT_OK` entries
- [ ] No clusters of 5+ consecutive `HEARTBEAT_FAIL` entries in last 30 minutes
- [ ] Cron jobs `brain-heartbeat` and `brain-overseer` are enabled and scheduled correctly

### 9. Notes

- The overseer is intentionally conservative: it logs issues but does **not** attempt automatic restarts to avoid interfering with manual troubleshooting.
- The heartbeat script runs *every minute*; the overseer runs *every 2 minutes*. This overlap ensures detection even if one check is temporarily missed.
- Cron output files in `~/.hermes/cron/output/[job_id]/` provide historical execution records for trend analysis.
- This approach complements (does not replace) direct MCP tool availability checks when building or testing Hermes agents.
- The `check_brain_heartbeat.py` file in `~/.hermes/hermes-agent/` is a small wrapper for cron to execute; the real work happens in the shell scripts.