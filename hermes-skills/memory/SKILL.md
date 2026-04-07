---
name: memory
description: Persistent cross-session memory with categories, TTL, and natural language commands
version: 1.0.0
author: integration-layer
license: MIT
metadata:
  hermes:
    tags: [memory, persistence, storage, context]
    homepage: https://github.com/NousResearch/hermes-agent
    related_skills: []
---

# Memory Skill for Hermes-Agent

This skill adds persistent memory capabilities to Hermes, allowing it to remember
information across conversations and retrieve it when needed.

## Features

- **Persistent storage** - memories survive across sessions
- **Category system** - organize memories as user, project, session, or general
- **Configurable TTL** - automatic cleanup based on time-to-live
- **Natural language** - use "remember that..." or "what do you know about..."
- **Tool integration** - full OpenAI-compatible tool definitions for direct LLM use

## Installation

Place `hermes_integration.py`, `hermes_agent_skill.py`, and `config.yaml` in
`~/.hermes/memory-integration/`, then load the skill in your Hermes session:

```
/skill memory
```

Or preload it:

```
hermes chat -s memory
```

## Configuration

Edit `~/.hermes/memory-integration/config.yaml`:

```yaml
backend: json                    # or "sqlite"
storage_path: ~/.hermes/memory-integration/data
default_ttl_hours: 720           # 30 days
category_ttl:
  session: 24                    # session memories expire after 1 day
  user: 2160                     # user memories: 90 days
  project: 2160                  # project memories: 90 days
  general: 720                   # general: 30 days
```

## Memory Categories

| Category | TTL Default | Use For |
|----------|-------------|---------|
| `user`   | 90 days     | User name, preferences, contact info, personal details |
| `project`| 90 days     | Project requirements, architecture, decisions, progress |
| `session`| 24 hours    | Temporary state for current workflow, auto-cleaned |
| `general`| 30 days     | Facts that don't fit other categories |

## Key Naming Conventions

Use colon-separated hierarchical keys for clarity and easy prefix search:

- `user:name` - User's full name
- `user:email` - Contact email  
- `user:preferences:theme` - UI theme preference
- `project:myapp:architecture` - Design decisions
- `project:myapp:status` - Current development progress
- `session:last_command` - Last executed command
- `session:intermediate_results` - Temporary calculation results

## Available Tools

### save_memory
Store a memory entry with optional category and TTL.

```json
{
  "tool": "save_memory",
  "args": {
    "key": "user:name",
    "value": "Alice",
    "category": "user",
    "ttl_hours": 2160
  }
}
```

### get_memory
Retrieve a memory entry by key.

```json
{
  "tool": "get_memory",
  "args": { "key": "user:name" }
}
```

### search_memory
Search entries by key prefix.

```json
{
  "tool": "search_memory",
  "args": { "prefix": "user:", "limit": 20 }
}
```

### list_memory
List entries, optionally filtered by category.

```json
{
  "tool": "list_memory",
  "args": { "category": "project", "limit": 100 }
}
```

### delete_memory
Delete an entry by key.

```json
{
  "tool": "delete_memory",
  "args": { "key": "user:old_preference" }
}
```

### memory_stats
Get statistics about your memory store.

```json
{
  "tool": "memory_stats",
  "args": {}
}
```

## Natural Language Commands

You can also use plain language:

| Command | Action | Example |
|---------|--------|---------|
| `remember that <fact>` | Save to memory | "remember that I'm working on a CLI tool" |
| `what do you know about <topic>` | Search by prefix | "what do you know about user?" |
| `forget <key>` | Delete entry | "forget user:old_preference" |
| `what memories do you have` | List all (limited) | "what memories do you have" |

These are parsed and converted to tool calls automatically.

## When to Use Memory

**Remember:**
- User states name, email, or preferences
- User mentions preferred tools, languages, or frameworks
- You make an architecture or design decision worth recalling
- Project requirements or specifications are provided
- Important file paths or API endpoints are shared
- Current task status or next steps

**Do NOT remember:**
- Sensitive secrets (API keys, passwords) — use a secure vault instead
- Temporary data that's already in the conversation context
- Trivial facts that won't be reused

**Forget/update:**
- When user asks to remove information
- When preferences change (overwrite the same key)
- When a project is completed (cleanup with prefix)

## Migration

If you have existing Hermes brain memory, use the migration tool:

```bash
# Migrate from default brain memory location
python ~/.hermes/memory-integration/migrate.py brain

# Migrate from custom location
python ~/.hermes/memory-integration/migrate.py brain /path/to/brain/memory

# Import JSON backup
python ~/.hermes/memory-integration/migrate.py json backup.json

# Import CSV (needs columns: key,content,category)
python ~/.hermes/memory-integration/migrate.py csv memories.csv

# Run all sources
python ~/.hermes/memory-integration/migrate.py --all ~/.hermes/memory backup.csv exported.json
```

Migration is **idempotent** — you can safely re-run it; keys already present with
newer timestamps will be skipped.

## Troubleshooting

**Memory not persisting:**
- Check storage path exists and is writable
- Verify `backend: json` or `sqlite` in config
- Look at logs in `~/.hermes/logs/`

**Tools not showing:**
- Load skill explicitly: `/skill memory`
- Check toolset is enabled (`/tools` → ensure "memory" is checked)
- Restart session (`/reset`) after loading skill

**Natural language not working:**
- The parser is simple — use direct tool calls for complex cases
- "remember that" must start exactly with that phrase
- Keys from natural language are auto-generated as slugs
