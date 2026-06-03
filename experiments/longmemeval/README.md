# LongMemEval Smoke Harness

This harness evaluates memory systems produced by the `memory-cli` skill against LongMemEval cases.

## Data Flow

`prepare_cases.py` splits each raw LongMemEval item into three files:

- `memory_input.json`: visible to the memory-building agent. It contains only session ids, timestamps, roles, and content.
- `question_input.json`: visible to the QA agent. It contains only the question and question date.
- `private_eval/<question_id>.json`: visible only to evaluator scripts. It contains reference answers and evidence labels.

The builder agent must not read questions, answers, `has_answer`, or evidence ids.

## Smoke Run

Download the oracle split:

```powershell
experiments\longmemeval\scripts\download_dataset.cmd --dataset oracle --out-dir datasets\longmemeval\raw
```

Prepare a small processed split:

```powershell
experiments\longmemeval\scripts\prepare_cases.cmd --raw datasets\longmemeval\raw\longmemeval_oracle.json --out-dir datasets\longmemeval\processed\oracle --limit 3
```

Run the harness with mock agents:

```powershell
experiments\longmemeval\scripts\run_all.cmd --processed-dir datasets\longmemeval\processed\oracle --cases smoke --limit 3 --run-id smoke-mock --mock-agents
```

Run one real Codex-agent case:

```powershell
experiments\longmemeval\scripts\run_all.cmd --processed-dir datasets\longmemeval\processed\oracle --cases smoke --limit 1 --run-id smoke-real-1 --agent-command "codex exec --skip-git-repo-check" --agent-timeout-seconds 900
```

Run only the QA stage for an existing built case:

```powershell
experiments\longmemeval\scripts\qa_stage.cmd experiments\longmemeval\runs\ut-build-case1\cases\gpt4_2655b836 "codex exec --skip-git-repo-check"
```

## Outputs

Runs are written under `experiments/longmemeval/runs/<run_id>/`.

Each case contains:

- `work/.venv`: isolated command environment.
- `work/.memory`: memory project created by the builder agent.
- `outputs/answer.json`: QA agent answer.
- `outputs/retrieval.json`: retrieval traces and latency.
- `outputs/judge.json`: mock or Codex judge result.
- `outputs/metrics.json`: retrieval and answer metrics.

The run root contains `aggregate_metrics.json`.
