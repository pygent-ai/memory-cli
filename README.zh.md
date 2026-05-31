# Memory CLI Skill

[English README](README.md)

![Memory CLI overview](docs/assets/memory-cli-overview.svg)

这个仓库提供了一套面向 agent 的记忆系统技能：它不是替 agent 写一份静态笔记，也不是预设某个固定数据库，而是教 agent 在自己的工作区里搭建、使用、测试并持续改进一套可成长的长期记忆系统。

核心思想是：记忆不是“存下来的文本”，而是“未来能被正确找回的行为”。一条重要记忆必须带着检索测试进入系统；只有当真实查询能把它找回来，它才算真正被记住。

## 这个项目解决什么

很多 agent 的“记忆”容易停留在两种状态：要么是不可验证的聊天摘要，要么是某个外部黑盒存储。`memory-cli` 选择了另一条路线：让 agent 自己维护一套本地记忆工程，用稳定的 CLI 命令读写记忆，用测试定义记忆是否可靠，用性能基准推动检索实现逐步升级。

这意味着记忆系统会随着使用而成长：

- 新记忆会先变成可测试的检索样例，再进入长期存储。
- 旧记忆可以被更新、降权或退休，但不会被随意删除。
- 检索变慢或不准时，agent 会在不破坏命令契约的前提下优化内部实现。
- 未来的 agent 接手同一个项目时，可以通过测试和文档理解这套记忆为什么存在、怎样继续维护。

## Skill 内容梳理

`skills/memory-cli` 是这个仓库的核心技能包。它包含一个主技能说明、三套默认项目模板、三份操作参考和一个 agent 配置示例。

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
tests/
  test_skill_templates.py
```

### `SKILL.md`

主技能文件定义了 agent 使用这套记忆系统的工作方式：

- 先在当前工作区寻找已有的 `memory-cli`、`.memory` 或 `memory` 项目。
- 如果没有现成项目，就从默认模板中复制一套最合适的实现。
- 在处理依赖长期上下文的任务前，先通过 `memory-cli search` 查询记忆。
- 添加记忆前，先编写候选记忆 JSON，并用 `check-conflicts` 检查冲突。
- 改动记忆或检索逻辑后，运行 `memory-cli test` 和 `memory-cli bench`。
- 当测试或性能出问题时，修复记忆样例或检索实现，而不是削弱高价值记忆。

### 默认模板

仓库提供三种可复制的起点：

- `assets/default-memory-cli-py/`：Python + `uv`，适合快速落地和最小依赖。
- `assets/default-memory-cli-js/`：Node.js JavaScript，适合轻量脚本环境。
- `assets/default-memory-cli-ts/`：Node.js TypeScript，适合需要类型约束的项目。

这些模板都从 JSON 文件和简单关键词匹配开始。早期系统不需要复杂架构，先保证 agent 有一套能运行、能测试、能被未来维护者读懂的记忆工程。

### 参考文档

`references/memory-test-contract.md` 定义记忆记录的 JSON 结构、命令语义、冲突处理和测试通过规则。它把“记住了什么”变成可审查、可回归的契约。

`references/memory-extraction-guide.md` 指导 agent 从对话、文档、项目历史或外部资料中提取可回答问题的事实。它强调实体、别名、时间、位置、关系和状态变化，而不是只保存宽泛摘要。

`references/retrieval-optimization-guide.md` 给出检索实现的升级阶梯：从文本规范化、关键词权重、倒排索引，到 SQLite FTS、向量检索和混合排序。优化必须服务于测试和性能证据，而不是为了技术复杂度本身。

## 记忆如何成长

![Memory lifecycle](docs/assets/memory-lifecycle.svg)

一套健康的 agent 记忆系统会经历这样的循环：

1. **提取**：从任务、对话、文档或代码历史中识别值得长期保留的事实。
2. **建模**：把事实写成带 `queries` 和 `must_include` 的记忆记录。
3. **验冲突**：用候选查询检查已有记忆，发现矛盾时先让用户或维护者决策。
4. **入库**：无冲突后添加记忆，或合并到更合适的已有记忆里。
5. **检索**：任务开始前主动查询相关记忆，把长期上下文重新带回工作现场。
6. **回归**：运行测试，确认重要记忆仍然能被未来的自然语言查询找回。
7. **优化**：当测试噪声、检索速度或召回质量变差时，升级内部实现。

这里的关键不是“保存更多”，而是让每条记忆都能参与未来行为。记忆系统越用越大，测试套件也越用越完整；测试套件越完整，agent 越能放心地改进检索实现。

## 命令契约

所有模板都围绕同一组命令工作：

```bash
memory-cli init [--path <dir>]
memory-cli search <query>
memory-cli check-conflicts --file <candidate.json>
memory-cli add --file <memory.json> [--force]
memory-cli list
memory-cli show <id>
memory-cli update <id> --file <updates.json>
memory-cli retire <id> [--reason <text>]
memory-cli test
memory-cli bench
```

这个命令表面应该保持稳定。agent 可以把 JSON 扫描替换成倒排索引、SQLite FTS、向量检索或混合排序，但外部工作流仍然依赖同一套命令和 JSON 输出形状。

## 记忆记录

一条记忆至少包含这些字段：

```json
{
  "id": "mem-stable-id",
  "priority": 80,
  "content": "The durable memory text.",
  "queries": ["query one", "query two"],
  "must_include": ["required phrase"]
}
```

推荐继续补充：

```json
{
  "status": "active",
  "tags": ["project", "preference"],
  "source": "user conversation",
  "created_at": "2026-05-30",
  "updated_at": "2026-05-30"
}
```

`priority` 不是装饰字段。它影响排序、失败严重度和优化优先级：

```text
100 = 身份、硬约束、长期用户偏好
80  = 重要项目决策
60  = 常见习惯和工作流偏好
40  = 临时但仍有价值的上下文
20  = 低价值历史记录
```

## Agent 的日常工作流

![Skill package architecture](docs/assets/skill-architecture.svg)

典型用法如下：

```bash
# 复制一个模板项目后，在模板目录内安装或直接运行
uv tool install -e .

# 开始任务前找回相关长期上下文
memory-cli search "memory skill"

# 添加前先检查候选记忆是否与已有记忆冲突
memory-cli check-conflicts --file candidate.json

# 无冲突后添加
memory-cli add --file memory.json

# 修改记忆或检索代码后验证正确性和性能
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
npm run build
```

## 为什么用测试来定义记忆

测试化记忆让 agent 具备三种能力。

第一，**自我检查**。agent 不必相信某条记忆“应该能搜到”，它可以运行查询并看到结果。

第二，**可维护成长**。当记忆数量增加时，agent 可以优化检索系统，同时用旧测试保护既有能力。

第三，**跨会话延续**。未来的 agent 不需要猜测前任为什么这样设计，只要读记录、跑测试、看基准，就能继续扩展这套系统。

这也是本项目最重要的定位：它不是一个记忆数据库成品，而是一套让 agent 自己构建记忆能力的技能。记忆系统的所有权在 agent 手里，成长路径也在 agent 的日常使用、验证和优化中自然展开。

## 开发验证

仓库当前的测试主要检查技能包和默认模板的契约是否保持一致：

```bash
python -m unittest
```

当你修改模板路径、README 中的模板说明、`package.json` 的 bin 配置或测试脚本时，应该同时更新测试和文档。
