# Cursor Runner Scripts

This directory contains Cursor-specific LongMemEval harness entrypoints.
It is the Cursor peer of `experiments/longmemeval/scripts/codex/` so Codex and Cursor runs do not
overwrite each other.

## Differences from the default runner

- Default agent command: `agent -p --trust --force`
- QA stage uses `experiments/longmemeval/scripts/cursor/qa_stage.cmd` and `invoke_agent.ps1`
- Default run output directory: `experiments/longmemeval/runs-cursor/`
- Default run id prefix: `cursor-YYYYMMDD-HHMMSS`

The Python evaluation logic is reused from `experiments/longmemeval/scripts/codex/`.
Only the agent invocation layer and run output location are Cursor-specific.

## Prerequisites

Install the Cursor CLI once:

```powershell
irm 'https://cursor.com/install?win32=true' | iex
```

Verify:

```powershell
experiments\longmemeval\scripts\cursor\check_agent.cmd
agent --version
```

## Smoke run with mock agents

```powershell
experiments\longmemeval\scripts\cursor\download_dataset.cmd --dataset oracle --out-dir datasets\longmemeval\raw
experiments\longmemeval\scripts\cursor\prepare_cases.cmd --raw datasets\longmemeval\raw\longmemeval_oracle.json --out-dir datasets\longmemeval\processed\oracle --limit 3
experiments\longmemeval\scripts\cursor\run_all.cmd --processed-dir datasets\longmemeval\processed\oracle --cases smoke --limit 3 --run-id cursor-smoke-mock --mock-agents
```

## Run one real Cursor-agent case

```powershell
experiments\longmemeval\scripts\cursor\run_all.cmd --processed-dir datasets\longmemeval\processed\oracle --cases smoke --limit 1 --run-id cursor-smoke-real-1 --agent-timeout-seconds 900
```

## Run only the QA stage for an existing built case

```powershell
experiments\longmemeval\scripts\cursor\qa_stage_only.cmd experiments\longmemeval\runs-cursor\<run-id>\cases\<question-id>
```

## Useful flags

```powershell
# Custom agent command
experiments\longmemeval\scripts\cursor\run_all.cmd --agent-command "agent -p --trust --force --model sonnet-4"

# Custom output directory
experiments\longmemeval\scripts\cursor\run_all.cmd --run-dir experiments\longmemeval\runs-cursor\my-custom-run

# Single case
experiments\longmemeval\scripts\cursor\run_case.cmd --processed-dir datasets\longmemeval\processed\oracle --question-id gpt4_2655b836 --run-dir experiments\longmemeval\runs-cursor\single-case
```

## Parallel full run (500 cases, concurrency 5)

Prepare all oracle cases and start a background parallel run:

```powershell
experiments\longmemeval\scripts\cursor\start_oracle_500_parallel.cmd
```

Or run directly:

```powershell
experiments\longmemeval\scripts\cursor\prepare_cases.cmd --raw datasets\longmemeval\raw\longmemeval_oracle.json --out-dir datasets\longmemeval\processed\oracle
experiments\longmemeval\scripts\cursor\run_all_parallel.cmd --processed-dir datasets\longmemeval\processed\oracle --cases all --workers 5 --run-id cursor-oracle-500-parallel
```

Check progress:

```powershell
experiments\longmemeval\scripts\cursor\check_progress.cmd --RunDir experiments\longmemeval\runs-cursor\cursor-oracle-500-parallel
```

Progress is tracked in:

- `experiments/longmemeval/runs-cursor/<run-id>/progress.json`
- `experiments/longmemeval/runs-cursor/<run-id>/runner.log`
- `experiments/longmemeval/runs-cursor/<run-id>/failures.json`
- `experiments/longmemeval/runs-cursor/<run-id>/aggregate_metrics.json`

Re-running the same `--run-id` resumes unfinished cases automatically.

## File map

| File | Purpose |
| --- | --- |
| `config.ps1` | Shared Cursor defaults |
| `invoke_agent.ps1` | Run `agent` with prompt file and workspace |
| `qa_stage.cmd` | Cursor QA stage wrapper |
| `run_case.py` | Cursor-specific case runner |
| `run_all.py` | Cursor-specific batch runner |
| `check_agent.cmd` | Verify `agent` is installed |
| `export_results_snapshot.cmd` | Export completed metrics to `results/cursor-oracle-500-qa83/` |
| `*.cmd` delegates | Reuse dataset prep and evaluation scripts |
