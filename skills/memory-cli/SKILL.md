---
name: memory-cli
description: Build, query, test, and optimize a local agent memory CLI where durable memories are represented as retrieval unit tests. Use when the user asks Codex to create, maintain, inspect, or improve a memory-cli project; when a workspace already contains a memory-cli, .memory, or memories project; or when Codex must add, update, retire, or validate durable memory records through a CLI contract.
---

# Memory CLI

## Command Contract

Read this command set before using or changing a memory project:

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

Keep this command surface stable. Improve retrieval internals without changing command names or JSON output shape unless the user explicitly asks for a breaking contract change.

## Core Model

Treat durable memory as tested retrieval behavior. Retrieval unit tests are gates and regression contracts, not the runtime retrieval system.

Build or update the retrieval system by distilling the facts and keyword/key-phrase intent expressed by the tests into the project's chosen implementation. That implementation may be JSON structure, code paths, if/else rules, indexes, caches, databases, vector stores, or another suitable design. The tests prove the behavior; they should not be the data source that `search` depends on at runtime.

## Runtime / Test Boundary

Keep runtime retrieval resources separate from retrieval unit-test resources. A portable `memory-cli search` package must run with only runtime code, runtime memory data, config, and optional generated runtime indexes. It must not read from `tests/`, test fixtures, test-case files, benchmark fixtures, unit-test assertions, or any other test-only resource.

Use a layout like:

- `src/` or `memory_cli/`: CLI and retrieval implementation.
- `memories/`: durable runtime memory records used by `search`, `list`, `show`, conflict checks, and indexes.
- `indexes/` or `.memory-index/`: optional generated runtime retrieval artifacts.
- `tests/`, `test-cases/`, or `fixtures/`: retrieval unit-test queries and assertions.

`search` may read only runtime memory records and runtime indexes. `test` and `bench` may read test cases and then call the public CLI/search path. If a candidate file contains both memory content and retrieval tests, `add` should distill or split it into runtime memory data and test-only assertions before relying on it.

## Workflow

1. Locate an existing memory project in the workspace. Prefer directories named `memory-cli`, `.memory`, `memory`, or project documentation that points to a memory command.
2. If no memory project exists, choose a language template and copy it into an appropriate workspace directory:
   - `assets/default-memory-cli-py/`: Python `uv` project.
   - `assets/default-memory-cli-js/`: JavaScript Node.js project.
   - `assets/default-memory-cli-ts/`: TypeScript Node.js project.
   Prefer the user's requested language. If unspecified, prefer `assets/default-memory-cli-py/` for smallest setup.
3. Install or run the copied template so the `memory-cli` command is available:
   - Python: run `uv tool install -e .` from the copied project.
   - JavaScript: run `npm link` from the copied project, or use `node src/cli.js ...` during development.
   - TypeScript: run `npm install && npm run build && npm link`, or use `npm test` during development.
4. Query memory before acting on tasks that may depend on durable context:

```bash
memory-cli search "<keyword-or-key-phrase>" ["another-keyword-or-key-phrase"...]
```

Use keyword and key-phrase queries for retrieval unit tests and normal searches. Multiple keyword arguments may match the same memory. When `search` receives multiple keyword arguments, it returns one result group per input keyword in the same order.

5. Add memory by designing candidate retrieval tests first. Save the candidate as JSON and run `memory-cli check-conflicts --file <candidate.json>`.
6. If candidate memory conflicts with existing memory, ask the user how to resolve it. If it does not conflict, distill the candidate into the current retrieval implementation with `memory-cli add --file <candidate.json>`, or merge with/modify existing test cases when that preserves the intended memory better than adding a separate case.
7. After changing memory cases or retrieval code, run:

```bash
memory-cli test
memory-cli bench
```

8. If correctness fails, fix the memory case or retrieval implementation. If performance exceeds the configured budget, optimize retrieval behind the same CLI contract.

## Memory Records

Read `references/memory-test-contract.md` before adding, reviewing, migrating, or changing memory records. Use it for the JSON schema, review rules, conflict handling, and test passing rule.

When extracting new memory from conversations, documents, project history, or external source material, read `references/memory-extraction-guide.md`. Use it to turn source material into answerable, testable memories with entities, aliases, time/place facts, relationships, state changes, and keyword/key-phrase retrieval tests.

Retired memories stay on disk for audit history but must not appear in normal search results, conflict checks, tests, or benchmarks.

## Priority Semantics

Use priority to decide ranking and failure severity. Search results must be sorted by priority first, then by retrieval score as a tie-breaker:

```text
100 = identity, hard constraints, long-term user preferences
80  = important project decisions
60  = common habits and workflow preferences
40  = temporary but still useful context
20  = low-value historical notes
```

Respect the project's config. A typical config treats failed memories at or above `blocking_failure` as blocking.

## Retrieval Implementation

Start with the simplest implementation that passes tests. It is acceptable for early memory projects to use JSON scans or hard-coded logic.

Do not implement retrieval by reading unit-test assertions as the live search corpus. Treat fields such as `queries` and `must_include` as test metadata unless the project explicitly defines separate runtime aliases or keywords. In memory records, `queries` should be keyword or key-phrase test inputs, not full prompts. Use tests to drive and verify the implementation, then store or encode the resulting memory facts in the system's runtime structures.

When the test suite grows or `bench` exceeds budget, read `references/retrieval-optimization-guide.md` and improve internals without changing the CLI output contract.

Do not delete or weaken high-priority memory tests to hide retrieval problems.

## Bundled Resources

- `assets/default-memory-cli-py/`: minimal Python memory CLI template.
- `assets/default-memory-cli-js/`: minimal JavaScript memory CLI template.
- `assets/default-memory-cli-ts/`: minimal TypeScript memory CLI template.
- `references/memory-extraction-guide.md`: guidance for extracting answerable, index-like facts from source material.
- `references/memory-test-contract.md`: detailed test-case schema and review rules.
- `references/retrieval-optimization-guide.md`: guidance for choosing stronger retrieval implementations.
