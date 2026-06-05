# Memory Test Contract

Use this reference when adding, reviewing, or migrating memory test cases.

## Command Semantics

- `init`: create `memories/`, `test-cases/`, and `memory.config.json` for a memory project.
- `search`: retrieve complete active matching memories for one or more keyword/key-phrase inputs. A single input returns one ordered match list. Multiple inputs return one ordered match list per input, preserving input order.
- `check-conflicts`: run candidate memory queries against active memory before adding.
- `add`: add a candidate memory JSON file; refuse conflicts unless `--force` is explicitly used, then split runtime memory fields into `memories/` and retrieval assertions into `test-cases/`.
- `list`: show IDs, priorities, statuses, tags, and sources for all memories, including retired ones.
- `show`: print the full memory record for one ID.
- `update`: merge fields from an updates JSON file into one memory.
- `retire`: mark a memory as retired without deleting its file.
- `test`: run all active retrieval unit tests.
- `bench`: measure active query and suite latency.

## Candidate Required Fields

```json
{
  "id": "mem-stable-id",
  "priority": 80,
  "content": "The durable memory text.",
  "queries": ["keyword one", "key phrase two"],
  "must_include": ["required phrase"]
}
```

## Recommended Fields

```json
{
  "status": "active",
  "tags": ["project", "preference"],
  "source": "user conversation",
  "created_at": "2026-05-30",
  "updated_at": "2026-05-30"
}
```

## Runtime Memory Fields

After `add`, runtime memory files under `memories/` should not contain `queries` or `must_include`. They contain the durable searchable fact and runtime retrieval terms:

```json
{
  "id": "mem-stable-id",
  "priority": 80,
  "content": "The durable memory text.",
  "keywords": ["keyword one", "key phrase two"],
  "aliases": ["alternate name"]
}
```

## Test Case Fields

Retrieval assertions live under `test-cases/`:

```json
{
  "memory_id": "mem-stable-id",
  "priority": 80,
  "queries": ["keyword one", "key phrase two"],
  "must_include": ["required phrase"]
}
```

## Example

```json
{
  "id": "mem-2026-05-30-memory-as-tests",
  "priority": 90,
  "status": "active",
  "content": "The user wants agent memory to be represented as retrieval unit tests. Adding memory means adding tests, and optimization should preserve the CLI contract.",
  "keywords": [
    "memory system",
    "retrieval tests",
    "CLI contract"
  ],
  "queries": [
    "memory system unit tests",
    "agent memory retrieval tests",
    "test driven memory retrieval"
  ],
  "must_include": [
    "retrieval unit tests",
    "Adding memory means adding tests",
    "CLI contract"
  ],
  "tags": ["memory", "testing", "skill"],
  "source": "user conversation",
  "created_at": "2026-05-30"
}
```

## Review Rules

- Before adding a memory, design candidate tests and run each candidate query against existing memory.
- If a new memory conflicts with existing memory, ask the user how to resolve the conflict before changing tests.
- If there is no conflict, distill the candidate into the current retrieval implementation, or merge/modify existing tests when that better preserves the intended memory than adding a duplicate case.
- Each memory should have at least two keyword or key-phrase queries when possible.
- High-priority memories should have stricter `must_include` assertions.
- Queries should capture exact names, aliases, categories, relationships, and concise key phrases that should retrieve the memory.
- Multiple queries may intentionally retrieve the same memory. Each query is evaluated independently.
- A memory should be explicit and useful. Do not preserve raw conversation trivia unless it changes future behavior.
- If two memories conflict, create a new higher-priority memory that explains the current rule and retire or lower the stale one.
- For memories with exact answer-bearing details, `must_include` should include the exact value or name when practical, not only broad topic words.
- For list or enumeration memories, queries should cover item lookup by position, distinguishing attribute, and category when relevant.
- For reusable preferences, queries should include source-context, generalized, and transfer-context phrasing.
- For changing facts, `must_include` should include the current value and enough timeline context to distinguish it from older values.

## Test Boundary

Use retrieval unit tests as validation gates and migration references. Do not make `search`, `check-conflicts`, or normal retrieval depend on test assertions as the live data source.

Keep test-only resources outside the runtime search path. `search` must be able to run without `tests/`, `test-cases/`, fixtures, benchmark data, or unit-test assertions. It may read only runtime memory records, runtime config, and generated runtime retrieval artifacts such as indexes, databases, embeddings, or caches.

The implementation may generate or update runtime structures from test-backed candidate files, such as JSON fields, code branches, indexes, databases, embeddings, or caches. Once generated, those runtime structures are the retrieval system; the tests remain the evidence that the behavior still holds. Treat `queries` and `must_include` as test metadata unless the project has explicitly copied selected terms into a runtime field such as `aliases`, `keywords`, or indexed content.

## Passing Rule

For each keyword or key phrase in `queries`, the search result is a full ordered list of active memories. The expected memory may appear anywhere in that list. A test passes when the expected memory is present and the strings in `must_include` appear in that matched result's content.

When `search` receives multiple keyword/key-phrase inputs, it returns one result group per input in the same order. The same memory may appear in multiple groups when multiple inputs match it.

Do not require exact content equality. Do not require the expected memory to be the top result. Do not truncate the result list before evaluating the test.

Retired memories remain available through `list` and `show` but should not participate in `search`, `check-conflicts`, `test`, or `bench`.
