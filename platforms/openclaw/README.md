# OpenClaw 入口

这是 OpenClaw 的薄入口文件。共享说明看 [../../README.md](../../README.md)（英文）和 [../../README_zh.md](../../README_zh.md)（中文），核心能力看 [../../SKILL.md](../../SKILL.md)。

## OpenClaw 安装

执行：

```bash
bash install.sh --platform openclaw
```

如果你还需要网页 / X / 微信公众号 / YouTube / 知乎自动提取，再执行：

```bash
bash install.sh --platform openclaw --with-optional-adapters
```

默认安装位置：`~/.openclaw/skills/llm-wiki`

如果你的 OpenClaw 不是这个目录，改用：

```bash
bash install.sh --platform openclaw --target-dir <你的技能目录>/llm-wiki
```

## 升级

```bash
bash install.sh --upgrade --platform openclaw
```

自定义目录升级：

```bash
bash install.sh --upgrade --platform openclaw --target-dir <你的技能目录>/llm-wiki
```

## 使用顺序

安装完成后，按 [SKILL.md](../../SKILL.md) 中的工作流继续执行：

1. `init` — 初始化知识库
2. `ingest` — 消化单个素材
3. `batch-ingest` — 批量消化
4. `query` — 快速问答
5. `digest` — 深度分析
6. `lint` — 健康检查
7. `consolidate` — 巩固整理（v2 新增）
8. `search` — BM25 搜索（v2 新增）
9. `supersede` — 版本取代（v2 新增）
10. `contradict` — 矛盾检测（v2 新增）
11. `graph` — 知识图谱
12. `status` — 状态查询
