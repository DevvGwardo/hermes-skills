# Hermes Skills

> The craftsman's workshop for a Claude-powered AI agent. Every skill is a tool — sharp, purpose-built, and ready to use.

[![Skills](https://img.shields.io/badge/skills-40%2B-6366f1?style=flat-square)](#) [![Storage](https://img.shields.io/badge/lines-228K-10b981?style=flat-square)](#)

This is the operational skill library for [Hermes](https://github.com/DevvGwardo/hermes-agent) — a collection of 40+ composable skills spanning software development, research, media, MLOps, creative work, and automation. Each skill is a self-contained unit: documentation, scripts, templates, and references bundled together so Hermes knows exactly how to wield it.

No fluff. Just tools that work.

---

## What a Skill Looks Like

```
software-development/systematic-debugging/
├── SKILL.md          ← the briefing: when to use it, how it works
├── references/       ← deep dives, cheatsheets, gotchas
├── templates/        ← ready-to-fill patterns
└── scripts/          ← executable helpers
```

Skills are loaded on-demand by Hermes. The agent reads the SKILL.md, follows the workflow, and executes with the included tooling. No plugin installation, no version pinning, no ceremony.

---

## The Workshop

```
hermes-skills/
├── software-development/    ◆ coding, debugging, code review, agentic workflows
├── mlops/                   ◆ training, fine-tuning, inference, evaluation
│   ├── training/            ◆ axolotl, unsloth, trl, peft, grpo
│   ├── inference/           ◆ vllm, llama.cpp, gguf, guidance, outlines
│   └── models/              ◆ whisper, stable diffusion, clip, audiocraft
├── research/                ◆ arxiv, blogwatcher, polymarket, paper writing
├── creative/                 ◆ ascii-art, excalidraw, manim, songwriting
├── media/                   ◆ youtube, heartmula, gif-search, songsee
├── devops/                  ◆ cron health, filesystem, logs, webhooks
├── autonomous-ai-agents/    ◆ codex, opencode, hermes-agent, agent-panel
├── github/                   ◆ pr workflow, code review, issues, repo management
├── productivity/            ◆ notion, linear, google-workspace, powerpoint
├── apple/                    ◆ imessage, reminders, notes, findmy (macOS only)
├── social-media/            ◆ xitter, discord bot-to-bot
├── gaming/                   ◆ pokemon-player, minecraft-modpack-server
├── smart-home/               ◆ openhue
├── email/                    ◆ himalaya
├── note-taking/             ◆ obsidian
└── red-teaming/             ◆ godmode
```

**40+ skills across 8 domains.** Everything you need to run a serious AI-assisted workflow.

---

## Highlights

| Category | Standouts |
|----------|-----------|
| **Coding** | `systematic-debugging` — 6-strategy approach, 0 guesswork. `subagent-driven-development` — spawns parallel coding agents with file locking. `brain-mcp-integration` — orchestrates multi-agent via MCP. |
| **Training** | `unsloth` — 2-5x faster LoRA fine-tuning. `grpo-rl-training` — online RL with TRL. `brain-mcp-rl-improver` —闭环 self-improvement from session trajectories. |
| **Inference** | `vllm` — high-throughput serving. `llama-cpp` — CPU/Apple Silicon. `obliteratus` — remove refusal behaviors from open models. |
| **Research** | `arxiv` — search and fetch papers. `polymarket` — prediction markets API. `ml-paper-writing` — NeurIPS/ICML/ACL templates with full workflows. |
| **Creative** | `ascii-video-pipeline` — numpy + PIL + ffmpeg pipeline for generative ASCII art video. `manim-video` — mathematical animation. `excalidraw` — hand-drawn diagrams from JSON specs. |
| **Agents** | `agent-panel` — DSPy-based multi-agent with role profiles. `agent-pool-coordinator` — spawns coder/researcher/reviewer/writer agents. `agentic-coder` — four-phase MiniMax coding agent. |

---

## Quick Start

```bash
# Browse the library
ls ~/.hermes/skills/

# Use any skill — just ask Hermes
# "Use the systematic-debugging skill to fix the memory leak in worker.ts"

# Sync to GitHub (hourly cron, or manual)
~/hermes-evo/scripts/sync-skills-to-repo.sh

# Clone the backup elsewhere
git clone https://github.com/DevvGwardo/hermes-skills.git
```

---

## The Philosophy

**One skill, one job.** No mega-skills that do everything. A skill that requires a 50-step tutorial is a framework, not a skill. The skills here are designed to be invoked in a single turn, deliver a complete result, and get out of the way.

**Scripts are passengers.** The SKILL.md is the captain. Scripts only run when the agent decides to run them, guided by the briefing in the markdown.

**References are first-class.** Every skill has a `references/` folder. Not "further reading" — concrete cheatsheets, troubleshooting guides, and architecture docs that the agent actually uses mid-task.

**Templates beat prompts.** When the output has structure (a PR body, a research paper, a code review), a template file beats a language model every time. Skills include templates, not just instructions.

---

## What This Isn't

- Not a plugin system. Skills aren't installed — they're loaded from disk.
- Not a prompt library. The markdown is workflow guidance, not example exchanges.
- Not a one-size-fits-all agent. This library assumes a capable reasoning model reading structured documentation and making decisions.

---

## Maintenance

This repo is synced hourly from the live Hermes installation. The most recent commit is your operational skill state at any given moment. Use it for:
- **Disaster recovery** — restore a corrupted skill library instantly
- **Environment cloning** — spin up a new Hermes instance with the same toolkit
- **Version control** — see exactly what changed between yesterday and today
- **Collaboration** — share skill subsets with other Hermes users

---

## Contributing

Found a gap? Built a skill that works? Open a PR.

Good skills:
1. Have a one-line `description` in the SKILL.md header
2. Include at least one `references/` doc
3. Keep scripts minimal — Hermes interprets the markdown, not the scripts
4. Follow the `category/skill-name/` directory structure
