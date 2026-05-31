# Memory CLI Skill

This repository contains the design and first implementation of a Codex skill for building an agent-owned memory system.

The core idea is simple:

> A memory is not just stored text. A memory is a retrieval behavior that must keep passing tests.

The skill lives in `skills/memory-cli`. The design principles live in `docs/`.

## Structure

```text
docs/
  memory-system-design.md
skills/
  memory-cli/
    SKILL.md
    agents/openai.yaml
    references/
    assets/default-memory-cli-py/
    assets/default-memory-cli-js/
    assets/default-memory-cli-ts/
```

## What This Skill Does

The `memory-cli` skill guides an agent to:

- initialize a local memory CLI project,
- represent memories as retrieval test cases,
- retrieve memories through a command-line contract,
- add new memories by adding tests,
- optimize retrieval logic when correctness or performance degrades.

The default templates are intentionally minimal. The `-py` template is a `uv` Python CLI project, the `-js` template is a Node.js JavaScript project, and the `-ts` template is a Node.js TypeScript project. All three use JSON memory cases and simple keyword matching so the first version always works. Agents may later replace the retrieval implementation with indexing, SQLite FTS, vectors, caching, or a hybrid design as the memory test suite grows.

## Quick Start For Agents

Install or copy the skill folder into a Codex skills directory, then ask Codex to use `memory-cli` when it needs to build or maintain durable memory.

The skill carries a default project template at:

```text
skills/memory-cli/assets/default-memory-cli-py/
skills/memory-cli/assets/default-memory-cli-js/
skills/memory-cli/assets/default-memory-cli-ts/
```

The Python template can be copied into a workspace and installed with `uv`:

```bash
uv tool install -e .
```

After installation, run it directly:

```bash
memory-cli init
memory-cli search "memory skill"
memory-cli check-conflicts --file candidate.json
memory-cli add --file memory.json
memory-cli list
memory-cli show mem-2026-05-30-memory-as-tests
memory-cli update mem-2026-05-30-memory-as-tests --file updates.json
memory-cli retire mem-2026-05-30-memory-as-tests --reason "stale"
memory-cli test
memory-cli bench
```

During template development, `uv run memory-cli ...` works without installing the command globally.

For the JavaScript template, use `npm test` or `node src/cli.js ...` during development.

For the TypeScript template, run `npm install` once, then use `npm test` or `npm run build` during development.
