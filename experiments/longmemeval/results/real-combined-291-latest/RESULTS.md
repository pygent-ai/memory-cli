# LongMemEval Unified Results

This directory contains the unified latest result set for the 291 completed LongMemEval oracle cases.

## Scope

| Item | Count |
|---|---:|
| Completed cases | 291 |
| Correct after manual review | 276 |
| Still failed | 15 |
| Strict substring correct | 186 |
| Manual review true | 90 |
| Manual review false | 15 |

## Overall Metrics

| Metric | Value |
|---|---:|
| recall@1 | 0.6735 |
| recall@5 | 0.9931 |
| recall@10 | 0.9937 |
| ndcg@5 | 0.9952 |
| ndcg@10 | 0.9952 |
| strict substring accuracy | 0.6392 |
| answer accuracy after manual review | 0.9485 |
| average total search latency ms | 441.7569 |
| average max search latency ms | 121.8729 |

## Metrics By Question Type

| Question type | Cases | Correct | Accuracy | recall@5 | Manual true | Manual false |
|---|---:|---:|---:|---:|---:|---:|
| knowledge-update | 76 | 75 | 0.9868 | 0.9934 | 19 | 1 |
| multi-session | 39 | 36 | 0.9231 | 0.9744 | 11 | 3 |
| single-session-assistant | 51 | 43 | 0.8431 | 1.0000 | 12 | 8 |
| single-session-preference | 30 | 27 | 0.9000 | 1.0000 | 27 | 3 |
| single-session-user | 35 | 35 | 1.0000 | 1.0000 | 5 | 0 |
| temporal-reasoning | 60 | 60 | 1.0000 | 0.9917 | 16 | 0 |

## Files

- `combined_metrics.json`: aggregate metrics and counts for the unified result set.
- `per_case_metrics.json`: one metrics record per completed case.
- `source_map.json`: maps each case to the source result used during consolidation.
- `case_ids.txt`: all included case ids.
- `failed_case_ids.txt`: cases still marked incorrect after manual review.
