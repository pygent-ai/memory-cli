# Codex Runner Scripts

This directory contains the Codex-backed LongMemEval harness entrypoints.
It is the Codex peer of `experiments/longmemeval/scripts/cursor/`.

## Defaults

- Default agent command: `codex exec --skip-git-repo-check`
- Default run output directory: `experiments/longmemeval/runs/`
- QA stage uses `experiments/longmemeval/scripts/codex/qa_stage.cmd`

Prefer this directory for Codex runs. Cursor-specific wrappers live in the
neighboring `experiments/longmemeval/scripts/cursor/` directory.

## Smoke Run

```powershell
experiments\longmemeval\scripts\codex\download_dataset.cmd --dataset oracle --out-dir datasets\longmemeval\raw
experiments\longmemeval\scripts\codex\prepare_cases.cmd --raw datasets\longmemeval\raw\longmemeval_oracle.json --out-dir datasets\longmemeval\processed\oracle --limit 3
experiments\longmemeval\scripts\codex\run_all.cmd --processed-dir datasets\longmemeval\processed\oracle --cases smoke --limit 3 --run-id smoke-mock --mock-agents
```

## Run One Real Codex Case

```powershell
experiments\longmemeval\scripts\codex\run_all.cmd --processed-dir datasets\longmemeval\processed\oracle --cases smoke --limit 1 --run-id smoke-real-1 --agent-command "codex exec --ephemeral --skip-git-repo-check" --agent-timeout-seconds 900
```

## Run Only QA For An Existing Case

```powershell
experiments\longmemeval\scripts\codex\qa_stage.cmd experiments\longmemeval\runs\<run-id>\cases\<question-id> "codex exec --ephemeral --skip-git-repo-check"
```
