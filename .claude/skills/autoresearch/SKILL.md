---
name: autoresearch
description: >
  Autonomously research any topic, question, or skill improvement task — deeply,
  without stopping, until you have something genuinely useful to show.
  Use when the user asks you to research how something works, improve an existing
  skill, explore a domain, answer a hard question through investigation, or says
  anything like "figure out X", "go research Y", "dig into Z", "improve the
  [skill] skill", or "learn about X and come back with findings".
  The goal is depth over speed: keep going, follow threads, synthesize,
  and produce something the user can actually use — not a quick surface answer.
---

# Autoresearch

Autonomous deep research on any topic. Research until you have something genuinely useful, then present it.

## When this skill applies

Any time the user hands you a question, topic, or improvement target and wants you to go figure it out — not just answer off the top of your head, but actually investigate:

- **Conceptual questions** — "How does money work?", "How do neural networks learn?"
- **Craft / process questions** — "How do you create a compelling character?", "How does good dialogue work?"
- **Technical investigations** — "How should we parse EPUB files?", "What's the best way to handle auth in this stack?"
- **Skill improvement** — "Improve the parse-epub skill", "Make the autoresearch skill better"
- **Domain exploration** — "What are the key ideas in behavioral economics?"

## Research process

### Step 1: Understand the goal

Before diving in, be clear on what a good outcome looks like:
- What does the user actually need? (quick orientation? deep expertise? a working improvement?)
- What form should the output take? (a summary, an updated skill, a how-to, a list of key ideas, code?)
- Are there existing resources to build on? (existing skills, project files, prior context in the conversation?)

If it's ambiguous, make a reasonable assumption and state it — don't stall asking clarifying questions when you can just start.

### Step 2: Plan research approach

Sketch a brief plan before starting. For most topics this means:
1. What sources will you consult? (web search, docs, code, books, the codebase itself)
2. What are the key sub-questions to answer?
3. What's the dependency order — what do you need to understand first before the harder parts make sense?

### Step 3: Investigate deeply

Go broad first, then go deep on what matters. Research tactics by type:

**Conceptual / domain topics** (money, character creation, etc.)
- Search for authoritative sources, not just the first result
- Find multiple perspectives — beginner explanations AND expert nuance
- Look for frameworks, mental models, and principles — not just facts
- Follow threads: if something is mentioned as important, go understand it

**Technical topics** (how to parse EPUB, how auth works, etc.)
- Look at the spec / standard if one exists
- Find real implementations — libraries, open source code
- Look at edge cases and failure modes, not just the happy path
- Check for existing tools before building from scratch

**Skill improvement** (improve parse-epub, make X skill better)
- Read the existing skill carefully first
- Research what the skill is trying to do — is the approach right?
- Find better techniques, libraries, edge case handling
- Look at what's missing: what would a user realistically run into that the skill doesn't handle?

### Step 4: Synthesize

Don't just collect information — form a view. After gathering:
- What are the 2-3 most important things to understand about this topic?
- What surprised you? What was wrong in your initial assumptions?
- What are the practical implications for the user's specific situation?
- What trade-offs or debates exist that the user should know about?

### Step 5: Produce output

Match the output format to the goal:

| Goal | Output |
|---|---|
| Understand a concept | Structured explanation with key ideas, examples, and "the thing most people miss" |
| Improve a skill | Updated SKILL.md (and scripts/references if needed) — with a summary of what changed and why |
| Answer a technical question | Concrete answer + the reasoning, not just the conclusion |
| Explore a domain | Mental model / framework + key resources to go deeper |

**For skill improvements specifically:** edit the skill files directly, explain what you changed and why, and flag anything you're uncertain about.

### Step 6: Flag what you don't know

Good research surfaces uncertainty, not just confidence. If there are things you couldn't verify, debates that are unresolved, or areas where the user should do their own verification — say so explicitly.

## Depth heuristic

Ask yourself: "If the user asked a smart friend who actually knew this domain, would this answer satisfy them?" If the answer feels shallow or obvious, keep going. The bar is genuinely useful, not technically correct.

A few rounds of research on a rich topic beats one fast pass.

## Output structure (default)

Unless the goal calls for something different:

```
## What I found: [topic]

**The core idea**: [1-2 sentence essence]

**Key points**:
- ...
- ...

**The thing most people miss**: [insight or nuance]

**Practical takeaway**: [what the user should actually do or know]

**Where to go deeper**: [1-3 sources worth reading]

**What I'm uncertain about**: [honest gaps]
```

For skill improvements, skip this template — just edit the skill and write a short summary of the changes.
