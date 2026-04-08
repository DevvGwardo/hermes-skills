---
name: brain-mcp-health-monitor
description: Monitor and maintain brain MCP system health including overseer scripts, heartbeat checks, and Node.js module compatibility
category: software-development
---

# Brain MCP Health Monitor Skill

## Description
Monitor and maintain the health of the brain MCP (Model Context Protocol) system. This skill provides procedures for checking system health, diagnosing common issues (particularly Node.js module compatibility), and maintaining the overseer/heartbeat monitoring infrastructure.

## When to Use
- When agents appear unresponsive or stale
- When overseer logs show heartbeat failures
- Before relying on brain MCP functionality for agent spawning
- As part of routine system health monitoring
- When encountering `ERR_DLOPEN_FAILED` or `NODE_MODULE_VERSION` errors

## Procedure

### 1. Read the Heartbeat Script (if silent or unexpected output)
If the heartbeat script produces no output or you need to understand its logic:
```bash
cat ~/.hermes/brain_heartbeat.sh
```
Identify:
- The command it runs (`hermes mcp test brain`)
- Success pattern (grep for `successful|✓|passed|Connected`)
- Log and status file locations
- Self-healing actions (killing zombies, restarting via watchdogs)

### 2. Check Overseer Logs
First, examine the brain overseer logs to understand recent health status:
```bash
cat ~/.hermes/brain_overseer.log
```
Look for:
- HEARTBEAT_STALE vs HEARTBEAT_FRESH status
- RECENT_FAILURES sections
- Recovery attempt logs

### 2. Verify Heartbeat Status
Check the current heartbeat status file:
```bash
cat ~/.hermes/brain_heartbeat.status
```
Should contain "OK" for healthy state or "FAIL" for issues.

### 3. Examine Heartbeat Log
Review recent heartbeat checks:
```bash
tail -20 ~/.hermes/brain_heartbeat.log
```
Look for patterns of HEARTBEAT_OK vs HEARTBEAT_FAIL.

### 4. Test Brain MCP Connectivity
Directly test the brain MCP connection:
```bash
hermes mcp test brain
```
Watch for:
- Successful connection messages (✓ Connected)
- Node.js compatibility errors (ERR_DLOPEN_FAILED, NODE_MODULE_VERSION mismatches)
- Connection timeouts or closures

### 5. Check Watchdog and Server Processes
The heartbeat script relies on watchdog processes for self-healing. Verify they're active:
```bash
# Check for brain-mcp servers
ps aux | grep 'brain-mcp/dist/index.js' | grep -v grep

# Check for watchdog processes
ps aux | grep 'watchdog.js' | grep -v grep
```
- If watchdogs are absent, the script cannot auto-restart failed servers.
- Multiple server instances may be normal (load distribution) or indicate orphaned processes from previous runs.

### 5. Enable and Test Brain MCP Tools
If the MCP connection is successful but you need to use brain tools:
```bash
# Enable all brain MCP tools (if not already enabled)
hermes tools enable brain:*

# List available brain tools to verify they're accessible
hermes tools list | grep brain

# Call specific brain MCP tools using the tools call command
hermes tools call brain:sessions          # List active sessions
hermes tools call brain:pulse             # Report progress and stay alive
hermes tools call brain:status            # Show session info
hermes tools call brain:agents            # Check health of all agents
```

### 6. Diagnose Node.js Issues (If Applicable)
If you see Node.js version errors:
```bash
# Check current Node.js version
node --version

# Navigate to brain-mcp directory
cd ~/.hermes/brain-mcp || cd /path/to/brain-mcp

# Rebuild native modules
npm rebuild better-sqlite3

# Alternative: full reinstall
# npm install
```

### 7. Run Overseer Check
Manually trigger the overseer script:
```bash
~/.hermes/brain_overseer.sh
```
Then check updated logs:
```bash
tail -10 ~/.hermes/brain_overseer.log
```

### 8. Verify Cron Jobs
Ensure the monitoring cron jobs are active:
```bash
crontab -l | grep -E "(brain_|overseer|heartbeat)"
```
Should show entries for both heartbeat (every minute) and overseer (every 2 minutes).
Should show entries for both heartbeat (every minute) and overseer (every 2 minutes).

## Expected Output
Healthy system indicators:
- Overseer log shows HEARTBEAT_FRESH status
- Heartbeat status file contains "OK"
- Recent heartbeat logs show HEARTBEAT_OK entries
- `hermes mcp test brain` returns successful connection
- No Node.js compatibility errors in test output
- Overseer script runs without errors

## Troubleshooting Steps
If the system appears unhealthy:
1. **Node.js module issues**: Rebuild better-sqlite3 in brain-mcp directory
2. **Stale processes**: Check if brain MCP server is running
3. **Cron not running**: Verify cron daemon is active and jobs are scheduled
4. **Permission issues**: Ensure scripts are executable (`chmod +x *.sh`)
5. **Path issues**: Verify brain-mcp directory exists and is accessible
6. **Heartbeat script exit 0 but no success log**: The script may be failing to match its success pattern due to transient output (e.g., cold start yielding incomplete data). Check the heartbeat log for pattern failures and verify system health directly with `hermes mcp test brain`. Understanding the script's grep pattern is key to diagnosing false negatives.

## Integration Testing (Multi-Agent Primitives)

Use this when you need to verify brain-mcp primitives work end-to-end, not just that the server is alive. This exercises the full stack: spawn, communicate, share state, checkpoint, gate.

### Step 1: Basic Primitives
```
- brain_register (name yourself)
- brain_set / brain_get (shared state round-trip)
- brain_delete (cleanup)
- brain_incr / brain_counter (atomic counters)
- brain_contract_check (validates all contracts)
- brain_post (channel messaging)
- brain_plan (DAG task planning with dependencies)
```

### Step 2: Checkpoint Round-Trip
```
- brain_checkpoint (save current task state)
- brain_checkpoint_restore (verify data survives)
```

### Step 3: Spawn a Test Agent
```
- brain_wake with a task that tells the agent to:
  1. brain_register with a name
  2. brain_set a verification key
  3. brain_post a status message to channel
  4. brain_pulse working → brain_pulse done
  5. /exit
- Use headless mode + 120s timeout
```

### Step 4: Multi-Agent Communication
```
- brain_agents (verify agent is alive and registered)
- brain_dm to the spawned agent
- brain_inbox (check DM delivery)
- brain_read (verify agent's channel posts)
- brain_get the key the agent was supposed to set
```

### Step 5: Gate Validation
```
- brain_gate with dry_run=true
- Checks: tsc, contracts, behavioral tests, performance baselines
- On a clean workspace, behavioral + performance should pass
```

### Step 6: Metrics
```
- brain_metric_record (record test outcome)
- brain_brain_metrics (query history)
```

### Step 7: Cleanup
```
- Delete test keys from shared state
- brain_context_push to log the test run
```

### Known Issues
- **Ghost sessions**: Spawned agents may appear twice — once as QUEUED (stale) and once as IDLE (alive). This is the "90% ghost session" issue. Not a blocker but causes confusion in brain_agents output.
- **list_prompts / list_resources**: Not implemented (MCP discovery endpoints). Non-critical.
- **Gate tests**: If run from workspace root with multiple repos, vitest may pick up stray test files and report false failures. The tsc and contracts checks are more reliable indicators.

## Notes
- The heartbeat script runs every minute via cron
- The overseer script runs every 2 minutes via cron
- Stale agent entries in logs are normal from previous runs
- Node.js version mismatches can cause the test command to run but fail to actually connect
- Self-healing attempts are logged but actual restart depends on MCP management setup

## Example Usage
```bash
# Quick health check
cat ~/.hermes/brain_heartbeat.status
hermes mcp test brain

# Detailed diagnosis
tail -20 ~/.hermes/brain_overseer.log
tail -10 ~/.hermes/brain_heartbeat.log

# Fix Node.js issues
cd ~/.hermes/brain-mcp && npm rebuild better-sqlite3

# Manual oversight check
~/.hermes/brain_overseer.sh
```

## Related Files
- `~/.hermes/brain_overseer.sh` - Overseer monitoring script
- `~/.hermes/brain_heartbeat.sh` - Heartbeat checking script  
- `~/.hermes/brain_overseer.log` - Overseer activity log
- `~/.hermes/brain_heartbeat.log` - Heartbeat activity log
- `~/.hermes/brain_heartbeat.status` - Current status file
- `~/.hermes/brain-mcp/` - Brain MCP server directory