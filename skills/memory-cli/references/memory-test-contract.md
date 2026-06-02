# Memory Test Contract

Use this reference when adding, reviewing, or migrating memory test cases.

## Command Semantics

- `init`: create `memories/` and `memory.config.json` for a memory project.
- `search`: retrieve the complete active matching memory list, sorted by priority.
- `check-conflicts`: run candidate memory queries against active memory before adding.
- `add`: add a memory JSON file; refuse conflicts unless `--force` is explicitly used.
- `list`: show IDs, priorities, statuses, tags, and sources for all memories, including retired ones.
- `show`: print the full memory record for one ID.
- `update`: merge fields from an updates JSON file into one memory.
- `retire`: mark a memory as retired without deleting its file.
- `test`: run all active retrieval unit tests.
- `bench`: measure active query and suite latency.

## Required Fields

```json
{
  "id": "mem-stable-id",
  "priority": 80,
  "content": "The durable memory text.",
  "queries": ["query one", "query two"],
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

## Example

```json
{
  "id": "mem-2026-05-30-memory-as-tests",
  "priority": 90,
  "status": "active",
  "content": "The user wants agent memory to be represented as retrieval unit tests. Adding memory means adding tests, and optimization should preserve the CLI contract.",
  "queries": [
    "memory system unit tests",
    "how should agent memory be stored",
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
- Each memory should have at least two realistic queries when possible.
- High-priority memories should have stricter `must_include` assertions.
- Queries should include the way a future agent is likely to ask, not only exact wording from the original conversation.
- A memory should be explicit and useful. Do not preserve raw conversation trivia unless it changes future behavior.
- If two memories conflict, create a new higher-priority memory that explains the current rule and retire or lower the stale one.

## Test Boundary

Use retrieval unit tests as validation gates and migration references. Do not make `search`, `check-conflicts`, or normal retrieval depend on test assertions as the live data source.

The implementation may generate or update runtime structures from test-backed memory records, such as JSON fields, code branches, indexes, databases, embeddings, or caches. Once generated, those runtime structures are the retrieval system; the tests remain the evidence that the behavior still holds.

## Passing Rule

For each query, the search result is a full ordered list of active memories. The expected memory may appear anywhere in that list. A test passes when the expected memory is present and the strings in `must_include` appear in that matched result's content.

Do not require exact content equality. Do not require the expected memory to be the top result. Do not truncate the result list before evaluating the test.

Retired memories remain available through `list` and `show` but should not participate in `search`, `check-conflicts`, `test`, or `bench`.
