---
name: brain-mcp-integration
description: Approach for integrating brain MCP agent execution into existing codebases by replacing simulated/stubbed functions with real brain agent invocation
category: software-development
---

# Brain MCP Integration Approach

## Overview
Systematic method for replacing simulated agent execution or stubbed functions in existing codebases with actual brain MCP agent execution. This approach enables real multi-agent collaboration instead of simulated work.

## When to Use
- When you encounter simulated agent steps (e.g., `await new Promise(r => setTimeout(r, 50))`)
- When functions return hardcoded/fake results instead of actual agent work
- When you want to replace stubbed implementations with real brain MCP agent coordination
- When integrating brain MCP capabilities into orchestration systems like OpenClaw Evo

## Preparation
- Ensure brain MCP is operational: `mcp_brain_brain_status` returns room info
- Identify target function/stub to replace
- Understand expected input/output interface
- Verify spawn works: `mcp_brain_brain_wake --task "test" --name "test-verify" --layout headless`

## Steps

### 1. System Verification
```text
mcp_brain_brain_status          # Room info, session count
mcp_brain_brain_agents         # Active agents with status
mcp_brain_brain_checkpoint     # Save test checkpoint before starting
mcp_brain_brain_gate --dry_run true  # Check integration without notifying agents
```

### 2. Target Analysis
- Locate simulated/stubbed function (search for "Placeholder", "Simulate", "Fake", `setTimeout`)
- Document exact function signature and return type
- Identify available inputs (context, model, task description)
- Determine what real agent should do instead

### 3. Agent Design
- Define specific task for the brain agent
- Choose model: haiku (simple), sonnet (standard), opus (complex)
- Choose layout: headless (background), horizontal (side-by-side), tiled (grid)
- Plan tool access: terminal, file, web
- Define how agent reports results back (brain_post, brain_dm, or file output)

### 4. Spawn Strategy
**Option A — brain_swarm (recommended for feature dev):**
```text
mcp_brain_brain_swarm
  task="Complete feature: [description]"
  agents=[
    {"name": "worker-1", "files": ["src/file1.ts"], "task": "Task description"},
    {"name": "worker-2", "files": ["src/file2.ts"], "task": "Task description"}
  ]
```
Auto-registers as lead, creates task plan, spawns agents in parallel.

**Option B — brain_wake (manual control):**
```text
mcp_brain_brain_wake
  name="worker-1"
  task="Task description with full context"
  layout="horizontal"
  model="sonnet"
```
Spawn one at a time or in parallel. Monitor with `brain_agents`.

### 5. Agent Lifecycle (for spawned agents)
Each agent should:
1. `brain_register` with their name
2. `brain_get` the shared context key (e.g., "feature-context")
3. `brain_claim` files before editing (prevents conflicts)
4. Do the work
5. `brain_release` files when done
6. `brain_post` results to the channel
7. `/exit` when finished

### 6. Verification
After implementation:
```text
mcp_brain_brain_gate --dry_run true              # Check for type errors
mcp_brain_brain_gate --notify true               # Full gate — DMs agents their errors
mcp_brain_brain_security_scan files=["src/"]     # Scan modified files
```

## Best Practices from Recent Swarms

### What Worked Well
- **Clear task scoping**: Agents perform best with specific, well-scoped tasks (not "implement auth system" but "add login route with email/password validation")
- **File claim pattern**: Prevents two agents from editing the same file simultaneously
- **Tiled layout for 3+ agents**: Best visibility for watching parallel work
- **Gate before respawn**: Run gate first to get specific error messages, then respawn with context

### Common Pitfalls
- **Overly complex tasks**: Break into smaller steps. If a task takes >10 minutes, split it.
- **Missing context**: Agents need file paths, existing code patterns, and exact requirements upfront
- **Skipping claims**: Two agents edit same file → merge conflict at gate
- **No timeout handling**: Long-running agents can hang. Use 2-5 minute timeouts.
- **Gate without dry run**: Running full gate notifies agents of errors. Always dry_run first.

### Troubleshooting

**Agent not responding:**
```text
mcp_brain_brain_agents include_stale=true   # Check if it's stale
mcp_brain_brain_respawn agent_name="X"       # Respawn with context
```

**Gate failures:**
1. Dry run: `brain_gate --dry_run true` to see all errors
2. Dm each agent: `brain_dm --to "agent-name" --content "Fix line 42"`
3. Wait for fixes
4. Re-run gate

**Context lost:**
```text
mcp_brain_brain_checkpoint_restore     # Restore last state
brain_context_get limit=20             # Review recent context
```

## Example: Replacing a Simulated Agent

**Before (stubbed):**
```typescript
async function executeStep(task: string): Promise<Result> {
  // TODO: replace with real agent
  await new Promise(r => setTimeout(r, 50));
  return { success: true, output: "fake" };
}
```

**After (real brain agent):**
```text
# In the main session, spawn the agent:
mcp_brain_brain_wake
  name="step-executor"
  task="Execute: [task]. Read [relevant files], implement, write results to /tmp/step-result.json, then exit."
  layout="headless"
  timeout=120

# Monitor with:
mcp_brain_brain_agents

# Read results:
mcp_terminal command="cat /tmp/step-result.json"
```

For full multi-agent orchestration patterns, see `brain-swarm-workflow`.

### 4. Implementation Strategy
Replace the stub with:
1. **Agent spawning**: Use `brain_wake` or equivalent to spawn a headless agent
2. **Context passing**: Provide the agent with necessary context (task, files, constraints)
3. **Execution waiting**: Wait for agent completion via polling or result reading
4. **Result translation**: Convert agent output to expected return format
5. **Error handling**: Manage agent failures, timeouts, and unexpected results

### 5. Example Pattern (TypeScript/Node.js)
```typescript
import { spawn } from 'child_process';
import { randomUUID } from 'crypto';

// Instead of:
// await new Promise(r => setTimeout(r, 50));
// return fakeResult;

// Use:
async function realAgentStep(context, modelInfo): Promise<ActualResultType> {
  const agentId = `agent-${randomUUID()}`;
  
  // Build prompt for the agent
  const prompt = `
    Task: [describe what needs to be done]
    Context: [relevant context information]
    Available tools: [list brain MCP tools agent can use]
    Report results via: [how agent should communicate results]
  `;
  
  // Spawn headless Claude agent (what brain_wake does internally)
  const agentProcess = spawn('claude', [
    '-p', prompt,
    '--model', getModelAlias(modelInfo),
    '--dangerously-skip-permissions'
  ], {
    env: {
      ...process.env,
      BRAIN_DB_PATH: process.env.BRAIN_DB_PATH,
      BRAIN_ROOM: process.env.BRAIN_ROOM,
      BRAIN_SESSION_ID: process.env.BRAIN_SESSION_ID,
      BRAIN_SESSION_NAME: process.env.BRAIN_SESSION_NAME
    }
  });
  
  // Wait for completion with timeout
  const result = await new Promise((resolve, reject) => {
    let output = '';
    let error = '';
    
    agentProcess.stdout.on('data', (data) => output += data.toString());
    agentProcess.stderr.on('data', (data) => error += data.toString());
    
    agentProcess.on('close', (code) => {
      if (code === 0) {
        resolve({ success: true, output: output.trim() });
      } else {
        reject(new Error(`Agent failed with code ${code}: ${error}`));
      }
    });
    
    // Timeout after 2 minutes
    setTimeout(() => {
      agentProcess.kill();
      reject(new Error('Agent execution timed out'));
    }, 120000);
  });
  
  // Translate result to expected format
  return translateToExpectedFormat(result);
}
```

### 6. Brain MCP Direct Alternative
If available in your environment, you can use direct brain MCP tool calls:
```text
# Instead of simulation:
mcp_brain_brain_wake --task "[specific task]" --name "worker-[timestamp]" --layout headless --model [appropriate] --timeout 120
# Then wait for completion and read results via brain_read or checkpoints
```

### 7. Verification
- Test the modified function in isolation if possible
- Verify it produces actual results (not simulations)
- Check that error handling works correctly
- Confirm performance characteristics are reasonable
- Ensure no regressions in existing functionality

## Key Learnings from Practice

### What Works Well
- **Headless layout**: Reliable for background agent execution without tmux dependencies
- **Clear task definition**: Agents perform best with specific, well-scoped tasks
- **Timeout management**: Essential to prevent hanging processes (2 minutes per step is reasonable)
- **Environment propagation**: Passing BRAIN_* environment variables ensures agents connect to correct MCP instance
- **Result validation**: Always verify agent output makes sense before proceeding

### Common Pitfalls
- **Overly complex tasks**: Agents struggle with vague or multi-part instructions
- **Missing context**: Agents need sufficient information to act effectively
- **Timeout too short**: Complex tasks need adequate time to complete
- **Tool access assumptions**: Don't assume agents have access to specific files/tools without granting it
- **Result parsing**: Agent output format may vary; build in flexibility

### Verification Checklist
[ ] Function compiles without errors
[ ] Function returns correct type/format
[ ] Function produces actual work (not simulation/hardcoded results)
[ ] Function handles success case appropriately
[ ] Function handles error/timeouts gracefully
[ ] No regression in existing functionality
[ ] Performance is acceptable for use case
[ ] Agents clean up properly (no zombie processes)

## Safety Considerations
- Start with simple, well-scoped tasks when testing
- Monitor agent resource usage (especially in loops/cycles)
- Implement circuit breakers for repeatedly failing agents
- Consider rate limiting if spawning many agents rapidly
- Test in isolation before deploying to production systems

## Applicable Systems
This approach works well with:
- Orchestration systems with simulated agent steps
- Multi-agent frameworks using placeholder implementations
- Any system with "fake it till you make it" agent simulations
- Codebases wanting to leverage real MCP agent capabilities
- Educational/demonstration code with stubbed implementations

## Example Applications
- Replacing `executeAgentStep` in OpenClaw Evo's ultrawork.ts
- Converting simulated coding agents to real brain MCP agents
- Turning mock testing frameworks into actual agent-driven test generation
- Converting architecture diagram generators to real agent-created designs
- Swapping fake data processors for real agent-based ETL pipelines

## Troubleshooting
If agents aren't performing as expected:
1. Verify the prompt is clear and actionable
2. Check that agents have necessary file/system access
3. Ensure sufficient timeout for task complexity
4. Validate BRAIN_* environment variables are correctly set
5. Check agent logs/output for error messages
6. Try simpler tasks to isolate the issue
7. Consider if the task needs decomposition into smaller steps

This approach transforms simulated agent systems into genuinely collaborative multi-agent environments by leveraging the brain MCP infrastructure for real agent execution and coordination.