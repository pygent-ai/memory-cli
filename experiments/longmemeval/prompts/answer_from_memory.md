使用 memory-cli skill，回答下面的问题：

{{QUESTION}}

只输出 JSON，不要写文件，不要输出 Markdown，不要输出解释文字。JSON 格式如下：

```json
{
  "answer": "...",
  "search_queries_and_cli_results": ["..."],
  "notes": "..."
}
```

约束：
- 只通过当前目录的 memory-cli 记忆项目检索记忆来回答问题。
- 不要读取 `memory_input.json`、`private_eval_ref.json`、`datasets/raw` 或任何评测答案文件。
- 使用当前目录 `.venv` 中的 `memory-cli` 命令。
- 至少调用一次 `memory-cli search`。
- `search_queries_and_cli_results` 记录你实际执行的检索 query 和 CLI 返回结果摘要。
- 不要添加 `question_id`、`question`、`question_date`、`used_memory_ids` 等字段；这些字段由实验脚本自动补齐。
