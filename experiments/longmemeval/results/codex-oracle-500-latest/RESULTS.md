# LongMemEval Codex Oracle 500 Results

This directory contains the unified Codex result set for all 500 LongMemEval oracle cases.

## Scope

| Item | Count |
|---|---:|
| Completed cases | 500 |
| Correct after manual review | 468 |
| Still failed | 32 |
| Strict substring correct | 336 |
| Manual review true | 132 |
| Manual review false | 32 |

## Overall Metrics

| Metric | Value |
|---|---:|
| recall@1 | 0.6442 |
| recall@5 | 0.9945 |
| recall@10 | 0.9955 |
| ndcg@5 | 0.9967 |
| ndcg@10 | 0.9967 |
| strict substring accuracy | 0.6720 |
| answer accuracy after manual review | 0.9360 |
| average total search latency ms | 724.9053 |
| average max search latency ms | 141.8859 |

## Metrics By Question Type

| Question type | Cases | Correct | Accuracy | recall@5 | Manual true | Manual false |
|---|---:|---:|---:|---:|---:|---:|
| knowledge-update | 78 | 77 | 0.9872 | 0.9936 | 19 | 1 |
| multi-session | 133 | 122 | 0.9173 | 0.9895 | 21 | 11 |
| single-session-assistant | 56 | 47 | 0.8393 | 1.0000 | 12 | 9 |
| single-session-preference | 30 | 27 | 0.9000 | 1.0000 | 27 | 3 |
| single-session-user | 70 | 70 | 1.0000 | 1.0000 | 15 | 0 |
| temporal-reasoning | 133 | 125 | 0.9398 | 0.9937 | 38 | 8 |

## Error Profile

The newly completed 209-case remainder has 17 incorrect cases after manual
review. All 17 have recall@5 = 1.0, so the new residual errors are primarily
QA-stage reasoning errors rather than retrieval misses. The full 500-case result
has 32 incorrect cases after manual review, including 15 from the prior
`real-combined-291-latest` snapshot.

| Error category | Count |
|---|---:|
| Quantity or arithmetic error | 5 |
| Temporal difference calculation error | 4 |
| Over-abstained despite available evidence | 4 |
| Answered concretely when abstention was required | 2 |
| Temporal or ordered-list reasoning error | 2 |

## Files

- `combined_metrics.json`: aggregate metrics and counts for the unified result set.
- `per_case_metrics.json`: one metrics record per completed case.
- `source_map.json`: maps each case to the source result used during consolidation.
- `case_ids.txt`: all included case ids.
- `failed_case_ids.txt`: cases still marked incorrect after manual review.
