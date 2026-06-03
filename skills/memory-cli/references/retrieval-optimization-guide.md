# Retrieval Optimization Guide

Use this reference when `memory-cli bench` exceeds the configured budget or the memory suite becomes slow or noisy.

## Optimization Ladder

1. Normalize text consistently: lowercase, trim punctuation, split words.
2. Add keyword weighting: score query hits in runtime fields such as `content`, `tags`, `aliases`, and `keywords` differently.
3. Build an inverted index from token to memory IDs.
4. Persist the index if startup time becomes expensive.
5. Use SQLite FTS when memory count is large enough that JSON scans are slow.
6. Add vector or semantic search only when keyword and key-phrase retrieval cannot meet validated recall requirements.
7. Use hybrid ranking for important systems: lexical score plus semantic score plus priority.

## Guardrails

- Keep the CLI contract stable.
- Run all correctness tests before trusting a faster implementation.
- Compare p95 latency before and after optimization.
- Prefer understandable implementations until performance data proves the need for complexity.
- Optimize by distilling test-backed memory behavior into better runtime structures, not by making tests part of live retrieval.
- Do not optimize by scoring `queries`, `must_include`, unit-test fixtures, or benchmark-only data as runtime search fields.
