# Memory System Design

## Purpose

This project designs a skill that helps an agent build and operate its own memory system. The memory system is not a hidden note file and not a fixed database choice. It is a small software project with a stable command-line contract, a growing test suite, and an implementation that can evolve as the number of memories grows.

The central principle is:

> Treat every durable memory as a retrieval test.

If something is important enough to remember, it should be important enough to verify. Adding memory means adding one or more tests that prove the memory can be found later from keywords and key phrases.

## Design Principles

### 1. Memory Is Behavior

A memory is useful only if the agent can retrieve it at the right time. The stored text is secondary; the retrieval behavior is the primary artifact.

Each memory should define:

- the remembered content,
- runtime keywords, aliases, or indexed terms that help retrieve it,
- the priority of the memory,
- separate keyword or key-phrase test queries that should retrieve it,
- the expected fields or phrases that must appear in search results,
- optional tags, source, and timestamps.

Before adding a new memory, the agent should design candidate tests and run their queries against existing memory. If the candidate conflicts with existing memory, the agent should ask the user how to resolve the conflict. If there is no conflict, the agent may merge or modify existing tests instead of adding a duplicate memory.

### 2. Tests Are The Source Of Truth

The memory project should be shaped by tests. A new memory enters the system as a candidate containing both durable content and retrieval assertions. The default templates split that candidate into a runtime memory record under `memories/` and a retrieval test case under `test-cases/`. A retrieval implementation is correct only if it passes the full suite.

Agents should not weaken a test just to make implementation easier. A test passes when the expected memory appears anywhere in the full result list for a query and the required expected content appears in that matched result. Exact text equality and top-1 ranking are not required.

When a test is too broad, stale, or contradictory, the agent should update it intentionally and preserve the reason in metadata or commit history.

### 3. Start Simple, Optimize When Pressured

The default implementation may use JSON files and simple keyword matching. That is acceptable at the beginning.

As the suite grows, agents may choose stronger implementations:

- normalized keyword indexes,
- inverted indexes,
- SQLite FTS,
- vector search,
- hybrid lexical and semantic retrieval,
- caching,
- memory summarization layers.

The skill should not force one storage or retrieval strategy. The tests and performance budget decide when optimization is needed.

### 4. Retrieval Uses A CLI Contract

The memory system should expose stable commands:

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

The implementation behind those commands may change. The agent's workflow should depend on the command contract, not on internal files.

`memory-cli search <keyword-or-key-phrase>` should return the complete matching result list. It should not truncate results. The result list should be sorted by priority first, with retrieval score used only as a tie-breaker. When multiple keyword/key-phrase inputs are provided, `search` should return one result group per input in the same order.

`search` should only read runtime memory records and runtime indexes. Test assertions in `test-cases/` are for `test` and `bench`; they are not live retrieval content.

### 5. Priority Has Operational Meaning

Every memory test has a configurable priority. Priority affects:

- result ranking,
- failure severity,
- optimization focus,
- whether a failed test blocks task completion.

Suggested priority scale:

```text
100 = identity, hard constraints, long-term user preferences
80  = important project decisions
60  = common habits and workflow preferences
40  = temporary but still useful context
20  = low-value historical notes
```

### 6. Performance Is Part Of Correctness

A memory that is technically retrievable but too slow to use will eventually be ignored. The memory project should measure:

- single-query latency,
- full test-suite time,
- p50 and p95 search latency,
- performance trends as the test count grows.

When performance exceeds the configured budget, the agent should optimize the retrieval implementation before adding large amounts of new memory.

## Expected Skill Behavior

When an agent uses the skill, it should:

1. Find or initialize a memory CLI project.
2. Query memory before tasks that may depend on durable user or project context.
3. Add memories by creating retrieval tests and splitting them from runtime memory data.
4. Run correctness and performance checks after changing memories or retrieval code.
5. Optimize implementation only behind the stable CLI contract.
6. Keep the memory system understandable enough that future agents can continue it.

## Non-Goals

This project does not prescribe a single database, embedding model, or storage backend.

It also does not turn memory into an uncontrolled transcript archive. A memory should be explicit, useful, and testable. Ephemeral conversation details should not become durable memory unless they are likely to improve future behavior.
