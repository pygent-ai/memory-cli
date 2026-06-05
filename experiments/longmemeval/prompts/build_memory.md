使用 memory-cli skill。

只读取 `input/memory_input.json`。根据其中的 sessions 和 timestamp 构建当前 case 的 memory-cli 记忆项目。

约束：
- 不要读取除 `input/memory_input.json` 外的任何文件。
- 使用当前目录 `.venv` 中的 `memory-cli` 命令。
- 在当前工作目录创建或更新 `.memory` 记忆项目。
- 每条重要记忆都要包含可检索的 `queries` 和 `must_include`。
- 记忆来源要使用通用 memory-cli 字段表达，不要新增实验专属字段：
  - 如果一条记忆完整对应一个 source session，且不会和其他记忆撞 id，可以把记忆 `id` 设为该 `session_id`，例如 `session_0002`。
  - 如果同一个 source session 会拆成多条记忆，或一条记忆融合了多个 source session，使用稳定语义化 `id`，并在 `source` 字段中明确写出所有来源 session id，例如 `LongMemEval case_0001 session_0002 session_0005`。
  - `source` 字段可以用于记录 case id、session id 和时间范围。
- 完成后运行 `memory-cli test` 和 `memory-cli bench`。
