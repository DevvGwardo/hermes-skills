---
name: system-health-monitoring
description: Systematic health verification using monitoring scripts combined with direct system validation and log analysis.
category: devops
---

# System Health Monitoring via Script + Direct Validation

## When to Use

- User asks to "run the heartbeat script" or "check if X is healthy" and provides a script path
- The script is silent or produces minimal output
- Need to verify not just the script's result but the actual system state
- Monitoring script may be failing while system is fine (or vice versa)

## Approach

1. Execute the given script with timeout; record exit code and output.
2. Read the script to understand:
   - What it actually tests (command, patterns)
   - Where it logs (`*.log`) and writes status (`*.status`)
   - Any self-healing logic (killing zombies, restarting)
3. Check those log and status files for recent entries.
4. Independently verify the system component:
   - Run the actual test/query directly (e.g., `hermes mcp test brain`)
   - Check process list (`ps aux | grep ...`)
   - Verify ports, sockets, files as needed.
5. Compare script results with direct verification.
6. Investigate anomalies:
   - Exit code 0 but no output → likely silent success or pattern mismatch
   - Multiple instances → may be normal or orphaned
   - Missing watchdog/daemon → self-healing disabled
7. Report clearly: script result, actual system status, discrepancies, recommendations.

## Pitfalls

- Scripts run in cron may have different PATH/environment; test with full paths or replicate environment if needed.
- Grep patterns in scripts may be too strict or miss transient output states.
- Status files may be stale if script hasn't run recently.
- Multiple processes may be intentional (load balancing) or indicate failure to clean up.

## Example Output Structure

```
Heartbeat script: exit X, output: ...
Status file: ...
Last log entry: ...
Direct system test: ...
Process count: N
Issues found: ...
Recommendations: ...
```

## Notes

This skill complements existing specific monitoring skills (e.g., `brain-mcp-health-monitor`) with a generic methodology applicable to any custom monitoring script.