# Memory CLI Skill

[中文说明](README.zh.md)

![Memory CLI overview](docs/assets/memory-cli-overview.svg)

This repository provides an agent-oriented memory system skill. It does not ask an agent to keep a static note file, and it does not prescribe one fixed database. Instead, it teaches an agent to build, use, test, and continuously improve a long-term memory system inside its own workspace.

The core idea is: memory is not "stored text"; it is "behavior that can be retrieved correctly later." An important memory enters the system with retrieval tests. Only when keywords and key phrases can find it again does it count as truly remembered.

## What This Project Solves

Many agent memory systems drift into one of two shapes: unverifiable chat summaries, or external black-box storage. `memory-cli` takes a different path. It lets an agent maintain a local memory project, read and write memories through a stable CLI contract, define reliability with tests, and use performance benchmarks to guide retrieval upgrades.

That means the memory system can grow through use:

- New memories become testable retrieval cases before they enter long-term storage.
- Old memories can be updated, deprioritized, or retired without being casually deleted.
- When retrieval becomes slow or inaccurate, the agent can optimize the internals without breaking the command contract.
- Future agents can understand why the memory system exists and how to maintain it by reading the tests and documentation.

## Skill Package

`skills/memory-cli` is the core skill package in this repository. It contains the main skill instructions, three default project templates, three reference documents, and an agent configuration example.

```text
docs/
  memory-system-design.md
  assets/
skills/
  memory-cli/
    SKILL.md
    agents/openai.yaml
    references/
      memory-test-contract.md
      memory-extraction-guide.md
      retrieval-optimization-guide.md
    assets/
      default-memory-cli-py/
      default-memory-cli-js/
      default-memory-cli-ts/
tests/
  test_skill_templates.py
```

### `SKILL.md`

The main skill file defines how an agent should work with this memory system:

- First look for an existing `memory-cli`, `.memory`, or `memory` project in the current workspace.
- If no project exists, copy the most suitable default template.
- Before tasks that may depend on durable context, query memory with `memory-cli search`.
- Before adding memory, write a candidate memory JSON file and check it with `check-conflicts`.
- After changing memories or retrieval logic, run `memory-cli test` and `memory-cli bench`.
- When correctness or performance breaks, fix the memory cases or retrieval implementation instead of weakening high-value memories.

### Default Templates

The repository includes three copyable starting points:

- `assets/default-memory-cli-py/`: Python + `uv`, suitable for fast setup and minimal dependencies.
- `assets/default-memory-cli-js/`: Node.js JavaScript, suitable for lightweight scripting environments.
- `assets/default-memory-cli-ts/`: Node.js TypeScript, suitable for projects that want type checking.

All three templates start with JSON files and simple keyword matching. Early memory systems do not need elaborate architecture; they need a project that runs, can be tested, and can be understood by future maintainers.

### Reference Documents

`references/memory-test-contract.md` defines the JSON structure, command semantics, conflict handling, and test-passing rules for memory records. It turns "what was remembered" into an auditable regression contract.

`references/memory-extraction-guide.md` guides agents as they extract answerable facts from conversations, documents, project history, or external material. It emphasizes entities, aliases, time, location, relationships, and state changes instead of broad summaries.

`references/retrieval-optimization-guide.md` describes retrieval upgrade paths: text normalization, keyword weighting, inverted indexes, SQLite FTS, vector retrieval, and hybrid ranking. Optimization should serve tests and performance evidence, not technical complexity for its own sake.

## How Memory Grows

![Memory lifecycle](docs/assets/memory-lifecycle.svg)

A healthy agent memory system follows a loop:

1. **Extract**: Identify facts worth retaining from tasks, conversations, documents, or code history.
2. **Model**: Write those facts as memory records with `queries` and `must_include`.
3. **Check conflicts**: Run candidate queries against existing memory, and ask the user or maintainer to decide when facts contradict each other.
4. **Add**: Add the memory after conflict checks pass, or merge it into a better existing memory.
5. **Retrieve**: Query relevant memories before starting work so durable context returns to the task.
6. **Regress**: Run tests to confirm important memories can still be found by future keyword and key-phrase queries.
7. **Optimize**: Upgrade the internal implementation when test quality, retrieval speed, or recall begins to degrade.

The point is not to "save more." The point is for each memory to participate in future behavior. As the memory system grows, the test suite grows with it. As the test suite becomes richer, the agent can improve retrieval with confidence.

## Command Contract

All templates are built around the same command surface:

```bash
memory-cli init [--path <dir>]
memory-cli search <keyword-or-key-phrase> [keyword-or-key-phrase...]
memory-cli check-conflicts --file <candidate.json>
memory-cli add --file <memory.json> [--force]
memory-cli list
memory-cli show <id>
memory-cli update <id> --file <updates.json>
memory-cli retire <id> [--reason <text>]
memory-cli test
memory-cli bench
```

This command surface should stay stable. An agent may replace JSON scanning with an inverted index, SQLite FTS, vector retrieval, or hybrid ranking, but the outer workflow should keep depending on the same commands and JSON output shape.

## Memory Records

A memory contains at least these fields:

```json
{
  "id": "mem-stable-id",
  "priority": 80,
  "content": "The durable memory text.",
  "queries": ["keyword one", "key phrase two"],
  "must_include": ["required phrase"]
}
```

Recommended optional fields:

```json
{
  "status": "active",
  "tags": ["project", "preference"],
  "source": "user conversation",
  "created_at": "2026-05-30",
  "updated_at": "2026-05-30"
}
```

`priority` is operational, not decorative. It affects ranking, failure severity, and optimization priority:

```text
100 = identity, hard constraints, long-term user preferences
80  = important project decisions
60  = common habits and workflow preferences
40  = temporary but still useful context
20  = low-value historical notes
```

## Daily Agent Workflow

![Skill package architecture](docs/assets/skill-architecture.svg)

A typical workflow looks like this:

```bash
# After copying a template project, install or run it from the template directory.
uv tool install -e .

# Retrieve relevant durable context before starting work.
memory-cli search "memory skill" "retrieval tests"

# Check whether a candidate memory conflicts with existing memory.
memory-cli check-conflicts --file candidate.json

# Add the memory after conflict checks pass.
memory-cli add --file memory.json

# Verify correctness and performance after changing memories or retrieval code.
memory-cli test
memory-cli bench
```

During template development, global installation is optional:

```bash
# Python
uv run memory-cli search "test driven memory"

# JavaScript
node src/cli.js search "test driven memory"

# TypeScript
npm install
npm test
npm run build
```

## Why Use Tests To Define Memory

Tested memory gives an agent three abilities.

First, **self-checking**. The agent does not need to trust that a memory "should be searchable"; it can run the query and inspect the result.

Second, **maintainable growth**. As memory count increases, the agent can optimize retrieval while old tests protect existing behavior.

Third, **cross-session continuity**. Future agents do not need to guess why the system was designed this way. They can read the records, run the tests, inspect the benchmarks, and keep extending the system.

That is the central positioning of this project: it is not a finished memory database product. It is a skill that lets an agent build its own memory capability. Ownership stays with the agent, and the growth path emerges through everyday use, verification, and optimization.

## Development Verification

The current repository tests mainly check that the skill package and default templates keep their contracts aligned:

```bash
python -m unittest
```

When changing template paths, README template descriptions, `package.json` bin configuration, or test scripts, update tests and documentation together.
