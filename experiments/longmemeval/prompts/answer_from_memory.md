使用 memory-cli skill，回答下面的问题：

{{QUESTION}}

只输出 JSON，不要写文件，不要输出 Markdown，不要输出解释文字。JSON 格式如下：

```json
{
  "answer": "...",
  "search_queries_and_cli_results": [
    {
      "query": "实际传给 memory-cli search 的检索词",
      "cli_result_summary": "CLI 返回结果的简短摘要"
    }
  ],
  "notes": "..."
}
```

约束：
- 只通过当前目录的 memory-cli 记忆项目检索记忆来回答问题，如果多次检索仍获取不到相关信息，请回复不知道。
- 使用当前目录 `.venv` 中的 `memory-cli` 命令。
- 至少调用一次 `memory-cli search`。
- `search_queries_and_cli_results` 必须是对象数组；每个对象必须包含 `query` 和 `cli_result_summary`。
- `query` 必须精确记录你实际传给 `memory-cli search` 的检索词，以供未来查证。
