# terminal — TimeoutError Skill

Handles TimeoutError errors in terminal. Generated from 3 occurrences across 2 sessions.

## Triggers
- "terminal error"
- "terminal failed"
- "terminal issue"
- "timeouterror error"
- "error: timeouterror"
- "error: Command timed out after 30 sec"
- "Command timed out after 30 sec"
- "something went wrong"
- "operation failed"
- "task failed"

## Implementation

## Overview
This skill handles TimeoutError errors encountered in the terminal tool.
Generated from 2 affected session(s).

## Error Pattern
- **Tool**: terminal
- **Error Type**: TimeoutError
- **Severity**: HIGH
- **Message Pattern**: Command timed out after 30 seconds: curl https://a

## Resolution Steps

### 1. Diagnose the Issue
- Check the terminal configuration
- Verify API credentials and permissions
- Review recent changes to terminal setup

### 2. Common Fixes
- Retry the operation with exponential backoff
- Check network connectivity and timeouts
- Verify input parameters are valid
- Clear cache and retry

### 3. Prevention
- Implement proper error handling
- Add retry logic with backoff
- Log detailed error information for debugging
- Monitor terminal health metrics

## Implementation Notes
```
When triggered:
1. Capture full error context
2. Attempt automatic recovery if safe
3. If recovery fails, provide user with actionable next steps
4. Log the incident for pattern analysis
```

## Related Skills
- Error Recovery Framework
- Retry with Backoff
- Diagnostic Helper


---
* Deployed by hermes-evo on 2026-04-07T15:16:49.779384+00:00 *
* Confidence: 0.8 *

## Source
- Tool: terminal
- Error Type: TimeoutError
- Frequency: 3
- Severity: HIGH