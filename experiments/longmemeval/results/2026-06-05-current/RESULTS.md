# LongMemEval Experiment Results Snapshot

Snapshot date: 2026-06-05

This directory consolidates the current LongMemEval oracle experiment results from two real-agent runs:

- `first10`: `experiments/longmemeval/runs/real-first10-20260604-153551`
- `remaining490-stopped`: `experiments/longmemeval/runs/real-remaining490-20260604-remaining`

The remaining run was stopped manually before all 490 remaining cases completed.

## Files

- `combined_metrics.json`: merged aggregate metrics across completed cases from both source runs.
- `per_case_metrics.json`: one normalized metrics record per completed case.
- `source_runs.json`: paths to the source run directories.
- `source_run_summaries/`: compact copied summaries/configs from the source runs.

Full per-case work directories, logs, memories, and intermediate artifacts remain in the source `runs/` directories.

## Run Coverage

| Scope | Count |
|---|---:|
| Oracle cases total | 500 |
| Completed with metrics | 291 |
| Excluded for rerun | 10 |
| Not completed | 199 |

Breakdown:

| Run | Started | Completed | Excluded for rerun | Interrupted/in progress at stop | Not started |
|---|---:|---:|---:|---:|---:|
| first10 | 10 | 10 | 0 | 0 | 0 |
| remaining490-stopped | 312 | 281 | 10 | 21 | 178 |

The 10 excluded cases are not counted as failed results in this snapshot. They
were removed from the reported result set and should be rerun later.

## Overall Metrics

| Metric | Value |
|---|---:|
| recall@1 | 0.6701 |
| recall@5 | 0.9895 |
| recall@10 | 0.9900 |
| ndcg@5 | 0.9917 |
| ndcg@10 | 0.9917 |
| strict substring accuracy | 0.5876 |
| answer accuracy after manual review | 0.8582 |
| average total search latency ms | 443.7209 |
| average max search latency ms | 119.8651 |

Answer counts:

| Answer metric | Count |
|---|---:|
| Strict substring correct | 171 / 291 |
| Manual corrections | 80 |
| Correct after manual review | 242 / 291 |

## Metrics By Question Type

| Question type | Cases | recall@5 | ndcg@5 | Strict accuracy | Corrected accuracy |
|---|---:|---:|---:|---:|---:|
| knowledge-update | 76 | 0.9934 | 0.9949 | 0.7237 | 0.9342 |
| multi-session | 39 | 0.9726 | 0.9793 | 0.6154 | 0.8974 |
| single-session-assistant | 51 | 1.0000 | 1.0000 | 0.3725 | 0.5686 |
| single-session-preference | 30 | 0.9667 | 0.9667 | 0.0000 | 0.8333 |
| single-session-user | 35 | 1.0000 | 1.0000 | 0.8286 | 0.9714 |
| temporal-reasoning | 60 | 0.9917 | 0.9961 | 0.7333 | 0.9412 |

## Notes

- `answer_substring_match` is intentionally strict. Many preference-style and semantically correct answers fail substring matching because the wording does not contain the exact reference string.
- `answer_correct` includes strict substring matches plus cases manually reviewed as semantically correct through `outputs/manual_review.json`.
- The weakest completed group is `single-session-assistant`: retrieval is perfect on completed cases, but answer reconstruction often returned `I don't know` or missed exact requested details.
- Retrieval quality is high across completed cases: overall recall@5 is 0.9895 and ndcg@5 is 0.9917.
