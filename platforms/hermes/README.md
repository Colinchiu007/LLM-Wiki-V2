# Hermes 入口

这是 llm-wiki 在 Hermes 下的入口文件。共享说明看 [../../README.md](../../README.md)（英文）和 [../../README_zh.md](../../README_zh.md)（中文），核心能力看 [../../SKILL.md](../../SKILL.md)。

## Hermes 应该怎么装

执行：

```bash
bash install.sh --platform hermes
```

如果你还需要网页 / X / 微信公众号 / YouTube / 知乎自动提取，再执行：

```bash
bash install.sh --platform hermes --with-optional-adapters
```

默认安装位置：`~/.hermes/skills/llm-wiki`

如果你的 Hermes 配了其他 skill 目录，改用：

```bash
bash install.sh --platform hermes --target-dir <你的技能目录>/llm-wiki
```

之后升级同一个自定义目录时，也传同样的目标目录：

```bash
bash install.sh --upgrade --platform hermes --target-dir <你的技能目录>/llm-wiki
```

## 使用顺序（v1 + v2 全量）

按 [SKILL.md](../../SKILL.md) 执行：

| # | 工作流 | v2新增 | 说明 |
|---|--------|--------|------|
| 1 | init | | 初始化知识库 |
| 2 | ingest | | 消化单个素材 |
| 3 | batch-ingest | | 批量消化 |
| 4 | query | | 快速问答 |
| 5 | digest | | 深度分析 |
| 6 | lint | ✅ | 健康检查 + 自愈 |
| 7 | consolidate | ✅ | 巩固整理 |
| 8 | search | ✅ | BM25 搜索 |
| 9 | supersede | ✅ | 版本取代 |
| 10 | contradict | ✅ | 矛盾检测 |
| 11 | graph | | 知识图谱 |
| 12 | status | | 状态查询 |
