# Memory CLI Skill

[English README](README.md)

![Memory CLI overview](docs/assets/memory-cli-overview.svg)

这个仓库提供一套面向 agent 的记忆系统技能。它不要求 agent 维护一份静态笔记，也不预设某个固定数据库；它教 agent 在自己的工作区里搭建、使用、测试并持续改进一套长期记忆系统。

核心思想是：记忆不只是“存下来的文本”，而是“未来能被正确找回的行为”。重要记忆进入系统时要带检索测试；只有关键词和短语查询能再次找回它，才算真正被记住。

## Skill 包

`skills/memory-cli` 是这个仓库的核心技能包，包含主技能说明、三套默认项目模板、参考文档和一个 agent 配置示例。

```text
docs/
  memory-system-design.md
  assets/
skills/
  memory-cli/
    SKILL.md
    agents/openai.yaml
    references/
      memory-test-contract.md
      memory-extraction-guide.md
      retrieval-optimization-guide.md
    assets/
      default-memory-cli-py/
      default-memory-cli-js/
      default-memory-cli-ts/
        memories/
        test-cases/
tests/
  test_skill_templates.py
```

主技能文件定义了 agent 的工作方式：

- 先在当前工作区寻找已有的 `memory-cli`、`.memory` 或 `memory` 项目。
- 如果没有现成项目，就复制最合适的默认模板。
- 在处理依赖长期上下文的任务前，先通过 `memory-cli search` 查询记忆。
- 添加记忆前，先编写候选记忆 JSON，并用 `check-conflicts` 检查冲突。
- 改动记忆或检索逻辑后，运行 `memory-cli test` 和 `memory-cli bench`。
- 如果正确性或性能出问题，修复记忆用例或检索实现，而不是削弱高价值记忆。

## 默认模板

仓库包含三种可复制的起点：

- `assets/default-memory-cli-py/`：Python + `uv`，适合快速落地和最小依赖。
- `assets/default-memory-cli-js/`：Node.js JavaScript，适合轻量脚本环境。
- `assets/default-memory-cli-ts/`：Node.js TypeScript，适合需要类型约束的项目。

三套模板都从 runtime JSON 记忆文件、独立 JSON 检索测试用例和简单关键词匹配开始。早期记忆系统不需要复杂架构；它首先需要能运行、能测试，并且未来维护者能读懂。

## 记忆如何增长

![Memory lifecycle](docs/assets/memory-lifecycle.svg)

一套健康的 agent 记忆系统通常这样循环：

1. **提取**：从任务、对话、文档或代码历史中识别值得长期保留的事实。
2. **建模**：把事实写成候选记忆记录，包含 runtime 内容以及 `queries` / `must_include` 断言。
3. **检查冲突**：用候选查询检查已有记忆；发现矛盾时先让用户或维护者决策。
4. **添加**：冲突检查通过后添加记忆。默认模板会把 runtime 字段写入 `memories/`，把检索断言写入 `test-cases/`。
5. **检索**：任务开始前主动查询相关记忆，把长期上下文带回工作现场。
6. **回归**：运行测试，确认重要记忆仍能被未来的关键词和短语查询找回。
7. **优化**：当测试质量、检索速度或召回效果下降时，升级内部实现。

重点不是“保存更多”，而是让每条记忆都参与未来行为。记忆系统越用越大，测试套件也随之增长。

## 命令契约

所有模板都围绕同一组命令工作：

```bash
memory-cli init [--path <dir>]
memory-cli search <keyword-or-key-phrase> [keyword-or-key-phrase...]
memory-cli check-conflicts --file <candidate.json>
memory-cli add --file <memory.json> [--force]
memory-cli list
memory-cli show <id>
memory-cli update <id> --file <updates.json>
memory-cli retire <id> [--reason <text>]
memory-cli test
memory-cli bench
```

这组命令表面应保持稳定。agent 可以把 JSON 扫描替换成倒排索引、SQLite FTS、向量检索或混合排序，但外部工作流仍应依赖同一套命令和 JSON 输出形状。

## 候选记忆文件

传给 `check-conflicts` 或 `add` 的候选记忆文件至少包含这些字段：

```json
{
  "id": "mem-stable-id",
  "priority": 80,
  "content": "The durable memory text.",
  "queries": ["keyword one", "key phrase two"],
  "must_include": ["required phrase"],
  "keywords": ["keyword one", "key phrase two"]
}
```

执行 `memory-cli add` 后，默认模板会把 runtime 记忆写到 `memories/`，其中不包含 `queries` 或 `must_include`；检索断言会写到 `test-cases/`：

```json
{
  "memory_id": "mem-stable-id",
  "priority": 80,
  "queries": ["keyword one", "key phrase two"],
  "must_include": ["required phrase"]
}
```

`memory-cli search` 只能读取 runtime 记忆和 runtime 索引。`memory-cli test` 和 `memory-cli bench` 读取 `test-cases/`，再调用公开的 search 路径验证行为。

`priority` 不是装饰字段。它影响排序、失败严重度和优化优先级：

```text
100 = 身份、硬约束、长期用户偏好
80  = 重要项目决策
60  = 常见习惯和工作流偏好
40  = 临时但仍有价值的上下文
20  = 低价值历史记录
```

## 日常工作流

![Skill package architecture](docs/assets/skill-architecture.svg)

```bash
# 复制模板项目后，在模板目录内安装或运行。
uv tool install -e .

# 开始任务前找回相关长期上下文。
memory-cli search "memory skill" "retrieval tests"

# 添加前检查候选记忆是否与已有记忆冲突。
memory-cli check-conflicts --file candidate.json

# 无冲突后添加；add 会拆分 runtime 数据和测试断言。
memory-cli add --file memory.json

# 修改记忆或检索代码后验证正确性和性能。
memory-cli test
memory-cli bench
```

模板开发时也可以不全局安装：

```bash
# Python
uv run memory-cli search "test driven memory"

# JavaScript
node src/cli.js search "test driven memory"

# TypeScript
npm install
npm test
```

## 开发验证

仓库当前测试主要检查 skill 包和默认模板的契约是否保持一致：

```bash
python -m unittest discover -s tests
```

修改模板路径、README 中的模板说明、`package.json` 的 bin 配置或测试脚本时，应同步更新测试和文档。
