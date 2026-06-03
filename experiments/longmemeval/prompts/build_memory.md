使用 memory-cli skill。

只读取 `input/memory_input.json`。根据其中的 sessions 和 timestamp 构建当前 case 的 memory-cli 记忆项目。

约束：
- 不要读取 `question_input.json`、`private_eval_ref.json`、`datasets/raw` 或任何评测答案文件。
- 使用当前目录 `.venv` 中的 `memory-cli` 命令。
- 在当前工作目录创建或更新 `.memory` 记忆项目。
- 每条重要记忆都要包含可检索的 queries 和 must_include。
- 完成后运行 `memory-cli test` 和 `memory-cli bench`。
