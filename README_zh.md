# llm-wiki-v2 使用指南

> **English** | [中文](README_zh.md)

把碎片化的信息变成持续积累、互相链接、自我维护的知识库。

[![版本](https://img.shields.io/badge/v4.0.0-v2%E7%89%88-E8A87C?style=flat-square&labelColor=3a3026)](https://github.com/sdyckjq-lab/llm-wiki-skill/releases)
[![协议](https://img.shields.io/badge/MIT-协议-5a6e5c?style=flat-square&labelColor=3a3026)](LICENSE)
[![平台](https://img.shields.io/badge/Claude%E2%9C%A8Codex%E2%9C%A8OpenClaw%E2%9C%A8Hermes-4%E4%B8%AA%E5%B9%B3%E5%8F%B0-7a96a6?style=flat-square&labelColor=3a3026)]

---

## llm-wiki-v2 是什么？

**核心理念：** 知识被编译一次，然后持续维护——不是每次查询都从原始文档重新推导。

llm-wiki-v2 把散落的信息（链接、文件、笔记）变成持久积累、互相链接、自我维护的知识库。它不是传统笔记软件，而是 AI 帮你维护的知识生态系统：

- 你给素材（链接、文件、文本），AI 提取核心知识并整理成互相链接的 wiki 页面
- 知识库随着每次使用变得越来越丰富
- **生命周期管理** — 知识有置信度、来源标注和生命周期状态（active → stale → deprecated → archived）
- **结构化知识图谱** — 实体有类型、关系有语义，支持图遍历查询
- **混合搜索** — BM25 关键词搜索融合知识图谱结构化排序
- **自动化治理** — 隐私过滤、质量评分、自愈 lint、审计日志
- 所有内容都是本地 Markdown，用 Obsidian 或任何编辑器都能查看

---

## v1 和 v2 对比

| 功能 | v1 | v2 |
|------|-----|-----|
| 页面元数据 | `<!-- confidence: 0.8 -->` HTML注释散落 | 统一 frontmatter 块（6个结构化字段） |
| 置信度评分 | 人工注释，容易遗漏和丢失 | 自动计算 + 来源支撑 + 访问强化 |
| 搜索能力 | 纯字符串匹配，无索引 | BM25 全文索引 + jieba 中文分词 |
| 知识关联 | wikilink 文本，无结构化图谱 | graph-data.json（节点+边双向索引） |
| 搜索融合 | 无 | BM25 × 知识图谱 RRF 混合排序 |
| 质量评分 | 无 | 覆盖度/结构/引用/新鲜度四维评分 |
| 矛盾检测 | 无 | 实体共现 bigram + 否定词扫描 |
| 生命周期 | 无 | active → stale → deprecated → archived |
| 自愈修复 | 无 | self-heal.sh 检测并修复断链/孤立/过期 |
| 知识巩固 | 无 | consolidate 强化高频 + 归档低频 |
| 隐私过滤 | 无 | API Key / 手机号 / 银行卡自动检测 |
| 批量消化 | 手动逐个 | batch-ingest 一次性处理整个目录 |
| 知识结晶化 | crystallize | 增强生命周期和置信度评分 |

---

## 触发词对照表

| 中文触发说法 | 英文工作流 | 功能说明 | 产生的结果 |
|---|---|---|---|
| "帮我消化这个链接" / "添加素材" | **ingest** | 抓取 URL/文件内容，提取知识，写入 wiki | `wiki/sources/` + `wiki/entities/` 或 `wiki/topics/` |
| "批量消化这个文件夹" | **batch-ingest** | 批量处理多个文件或整个 raw 目录 | 同上，大批量处理 |
| "关于XX是什么" / "查询XX" | **query** | 快速问答，检索相关页面并总结 | 直接回复问答结果 |
| "给我讲讲XX" / "深度分析XX" / "综述XX" | **digest** | 深度综合，遍历全库关联页面出报告 | `wiki/synthesis/XX-深度报告.md` |
| "对比X和Y" / "比较X和Y" | **digest**（对比格式） | 多主题对比分析 | `wiki/synthesis/` 对比报告 |
| "检查知识库" / "健康检查" / "lint" | **lint**（v2增强） | 自愈健康检查：断链/孤立/质量/过期 | 控制台输出问题列表和修复建议 |
| "自愈lint" / "自动修复" | **lint**（self-heal模式） | 自动修复可修复项 | 文件被原地修改 |
| "巩固知识库" / "整理知识库" | **consolidate** | 强化高频高置信页面 + 归档低频页面 | 访问记录更新，生命周期状态流转 |
| "搜索XX" / "混合搜索XX" | **search** | BM25 关键词搜索（可选图谱加权融合） | 排名结果列表 |
| "画个知识图谱" / "看看关联图" | **graph** | 遍历 graph-data.json，输出节点/边结构 | 文本图谱或关系树 |
| "XX取代YY" / "supersede" | **supersede** | 旧页面标记 deprecated，新页面继承关联 | 旧页面 status 改为 deprecated |
| "检测矛盾" / "矛盾扫描" | **contradict** | 扫描互相引用页面中的矛盾声明 | 矛盾报告（无矛盾则提示一致） |
| "初始化知识库" / "新建wiki" | **init** | 创建目录骨架和 index 文件 | 空的 wiki 目录结构 |
| "知识库升级" / "迁移v2" | **migrate** | v1 → v2 迁移脚本 | 补充 frontmatter + 重建 BM25 + 重建图谱 |
| "同步知识库" / "mesh-sync" | **mesh-sync** | raw → wiki 同步 + 增量更新 | wiki 内容与 raw 目录对齐 |
| "删除XX" / "移除素材" | **delete** | 标记为 deprecated + 更新关联 | 移入 archive 或 status 改为 deprecated |
| "结晶化" / "把这个记进知识库" | **crystallize** | 将对话内容提炼为持久化 wiki 页面 | 新的或更新的 wiki 页面 |
| "知识库状态" / "现在有什么" | **status** | 列出实体数/主题数/素材数/更新时间 | 状态摘要 |

---

## 快速开始

把仓库链接扔给你正在用的 agent，让它自己完成安装：

```bash
# Claude Code
bash install.sh --platform claude

# Codex
bash install.sh --platform codex

# OpenClaw
bash install.sh --platform openclaw

# Hermes
bash install.sh --platform hermes
```

然后说：

> "帮我初始化一个知识库"
> "帮我消化这篇：<链接>"

---

## frontmatter 字段说明

每个 wiki 页面顶部 `---` 块：

```yaml
---
confidence: 0.8            # 置信度 0.0–1.0，自动计算
sources: ["raw/video1.md"] # 来源素材路径列表
created: 2026-06-03       # 首次进入知识库日期
last_accessed: 2026-06-03 # 最近一次被访问的日期
access_count: 5           # 累计被访问次数
status: active             # active | stale | deprecated | archived
---
```

**置信度等级：**

| 范围 | 等级 | 说明 |
|------|------|------|
| ≥ 0.7 | 🟢 高 | 高置信度，访问时自动强化 |
| 0.4–0.7 | 🟡 中 | 待验证，需补充来源或 wikilink |
| < 0.4 | 🔴 低 | 需补充来源、结构或关联 |

**生命周期流转：**

```
active ──(90天未访问)──→ stale ──(90天继续未访问)──→ archived
   │                              │
   └──(supersede)──────────────────→ deprecated ──(90天)──→ archived
```

---

## 目录结构

```
your-knowledge-base/
├── raw/                     # 原始素材（不可变来源）
│   ├── articles/            # 网页文章
│   ├── tweets/             # X/Twitter
│   ├── wechat/             # 微信公众号
│   └── assets/             # 下载的图片
├── wiki/                   # AI 生成的知识库
│   ├── index.md            # 总索引
│   ├── overview.md         # 总览
│   ├── entities/           # 实体页（概念、模型、法则）
│   ├── topics/             # 主题页（课程、模块）
│   ├── sources/            # 素材摘要
│   ├── synthesis/          # 深度综合报告
│   ├── archive/            # 归档页面（stale/deprecated）
│   ├── my/                 # 个人页面
│   └── graph-data.json     # 知识图谱（v2 新增）
├── .wiki-search.db         # BM25 搜索索引（v2 新增）
└── .wiki-cache.json        # 消化记录（raw→wiki 映射）
```

---

## 安装详情

### 默认安装位置

| 平台 | 路径 |
|------|------|
| Claude Code | `~/.claude/skills/llm-wiki` |
| Codex | `~/.codex/skills/llm-wiki` |
| OpenClaw | `~/.openclaw/skills/llm-wiki` |
| Hermes | `~/.hermes/skills/llm-wiki` |

### 升级

```bash
bash install.sh --upgrade --platform openclaw
```

### 前置条件

- 核心：agent 能执行 shell、读写文件；图谱和搜索需要 `jq` + `node`
- 可选：`uv` 公众号提取；`bun`/`npm` 网页抓取；Chrome 调试端口 9222 登录态内容

---

## 平台入口

各平台专属说明：

- [Claude Code](platforms/claude/CLAUDE.md)
- [Codex](platforms/codex/AGENTS.md)
- [OpenClaw](platforms/openclaw/README.md)
- [Hermes](platforms/hermes/README.md)

---

## 常见问题

**Q: 搜索结果不对？**
BM25 基于关键词，试试同义词或不同关键词组合。也可说"混合搜索"。

**Q: 页面置信度很低？**
补充 `sources` 字段（来源素材），增加 wikilink 关联，或检查结构完整性。

**Q: 想删除某个页面？**
直接说"删除XX"，agent 标记为 deprecated 而非物理删除，可恢复。

**Q: 索引或图谱损坏了？**
一键重建（数据不丢，只重建索引）：
```bash
bash scripts/index-bm25.sh <wiki_root>
python lib/entities.py build-graph <wiki_root>
```

**Q: v2 迁移出问题？**
`migrate-v1-to-v2.sh` 是幂等的，可重复运行。

---

## 致谢

- **[Andrej Karpathy](https://karpathy.ai/)** — [llm-wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)，核心方法论来源
- **[baoyu-url-to-markdown](https://github.com/JimLiu/baoyu-skills#baoyu-url-to-markdown)** by [JimLiu](https://github.com/JimLiu) — 网页、X 内容提取
- **youtube-transcript** — YouTube 字幕提取
- **[wechat-article-to-markdown](https://github.com/jackwener/wechat-article-to-markdown)** — 微信公众号文章提取

---

## License

MIT
