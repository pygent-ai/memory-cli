# LongMemEval Cursor Results

This directory contains an interim unified result set for Cursor Agent runs on LongMemEval oracle.

## Scope

| Item | Count |
|---|---:|
| Completed cases with metrics | 83 |
| Target oracle cases | 500 |
| Strict substring correct | 62 |
| Review-adjusted correct | 68 |
| Still failed after review | 15 |
| Strict misses accepted after review | 6 |

## Run Metadata

| Item | Value |
|---|---|
| Agent | Cursor |
| Run id | `cursor-oracle-500-parallel` |
| Run dir | `experiments/longmemeval/runs-cursor/cursor-oracle-500-parallel` |
| Snapshot | `cursor-oracle-500-qa83` |
| Created at | 2026-06-11T11:21:35 |

## Overall Metrics

| Metric | Value |
|---|---:|
| recall@1 | 0.3271 |
| recall@5 | 0.7229 |
| recall@10 | 0.7229 |
| ndcg@5 | 0.7229 |
| ndcg@10 | 0.7229 |
| strict substring accuracy | 0.7470 |
| review-adjusted answer accuracy | 0.8193 |
| average total search latency ms | 308.8355 |
| average max search latency ms | 133.1838 |

## Metrics By Question Type

| Question type | Cases | Correct | Accuracy | recall@1 | recall@5 | recall@10 | ndcg@5 | ndcg@10 | Strict correct |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| multi-session | 24 | 17 | 0.7083 | 0.1854 | 0.5417 | 0.5417 | 0.5417 | 0.5417 | 17 |
| temporal-reasoning | 59 | 45 | 0.7627 | 0.3847 | 0.7966 | 0.7966 | 0.7966 | 0.7966 | 45 |

## Notes

- This is a partial Cursor run snapshot, not the full 500-case oracle benchmark.
- The primary answer result above is review-adjusted: 62 strict substring
  matches plus 6 semantically equivalent temporal-reasoning answers that strict
  matching missed.
- Most incomplete cases failed during the build stage because Cursor usage limits were reached.
- QA JSON repair was applied before evaluation for cases with recoverable `qa_stdout.txt`.
- Compare with Codex results in `results/real-combined-291-latest/`.

## Files

- `combined_metrics.json`: aggregate metrics and counts for the Cursor result set.
- `per_case_metrics.json`: one metrics record per completed case.
- `source_map.json`: maps each case to the Cursor run directory.
- `case_ids.txt`: all included case ids.
- `failed_case_ids.txt`: cases marked incorrect by harness substring matching.
- `review_adjusted_failed_case_ids.txt`: cases still marked incorrect after
  review adjustment.

