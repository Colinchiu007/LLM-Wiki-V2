# llm-wiki-v2

> Build a self-maintaining, growing knowledge base — one piece of content at a time.

**English** | [中文](README_zh.md)

[![version](https://img.shields.io/badge/v4.0.0-v2%E7%89%88-4A90D9?style=flat-square&labelColor=3a3026)](https://github.com/Colinchiu007/LLM-Wiki-V2/releases)
[![license](https://img.shields.io/badge/MIT-license-5a6e5c?style=flat-square&labelColor=3a3026)](LICENSE)
[![platforms](https://img.shields.io/badge/Claude%E2%9C%A8Codex%E2%9C%A8OpenClaw%E2%9C%A8Hermes-4--platforms-7a96a6?style=flat-square&labelColor=3a3026)]

---

## What is llm-wiki-v2?

**Core principle:** Knowledge should be compiled once and continuously maintained — not re-derived from raw documents on every query.

llm-wiki-v2 transforms scattered information (links, files, notes) into a persistent, interconnected, self-maintaining knowledge base. It is not a traditional note-taking app — it is an AI-maintained knowledge ecosystem:

- You feed in content (URLs, PDFs, pasted text); AI extracts core knowledge and organizes it into linked wiki pages
- The knowledge base grows richer with every interaction
- **Lifecycle management** — knowledge has confidence scores, source attribution, and lifecycle states (active → stale → deprecated → archived)
- **Structured knowledge graph** — entities have types, relationships have semantics, graph traversal for queries
- **Hybrid search** — BM25 keyword search fused with graph-structured ranking
- **Automated governance** — privacy filtering, quality scoring, self-healing lint, audit logging

All content is plain Markdown. Works with Obsidian, VS Code, or any text editor. No server required.

---

## v1 vs v2

| Feature | v1 | v2 |
|---------|----|----|
| Page metadata | `<!-- confidence: 0.8 -->` HTML comments scattered in body | Structured frontmatter block (6 fields) |
| Confidence scoring | Manual annotation, easily lost | Auto-calculated + source-backed + access-reinforced |
| Search | Plain text grep, no index | BM25 full-text index + jieba Chinese tokenization |
| Knowledge relationships | Wikilinks in plain text | graph-data.json bidirectional index (nodes + edges) |
| Search fusion | None | BM25 × knowledge graph RRF hybrid ranking |
| Quality scoring | None | 4-dimension: coverage / structure / citation / freshness |
| Contradiction detection | None | Bigram Jaccard + negation word scanning |
| Lifecycle management | None | active → stale → deprecated → archived |
| Self-healing | None | self-heal.sh detects & fixes broken links, orphans, stale pages |
| Knowledge consolidation | None | consolidate reinforces high-confidence + archives low-frequency |
| Privacy filtering | None | API keys, phone numbers, bank cards detected automatically |
| Batch ingest | Manual | batch-ingest processes entire directories at once |
| Knowledge distillation | crystallize | Enhanced with lifecycle and confidence scoring |

---

## Workflow Reference

Trigger by natural language — the agent routes automatically.

| What you say | Workflow | What it does | Output |
|---|---|---|---|
| "帮我消化这篇" / "帮我消化这个链接" | **ingest** | Fetch URL/file, extract knowledge, write wiki pages | `wiki/sources/` + `wiki/entities/` or `wiki/topics/` |
| "批量消化这个文件夹" | **batch-ingest** | Process multiple files or entire raw directory | Same as above, batch |
| "关于XX是什么" / "查询XX" | **query** | Quick Q&A, retrieve and summarize relevant pages | Direct answer |
| "给我讲讲XX" / "深度分析XX" / "综述XX" | **digest** | Deep synthesis across all linked pages | `wiki/synthesis/XX-深度报告.md` |
| "对比X和Y" / "比较X和Y" | **digest** (compare mode) | Multi-topic comparative analysis | `wiki/synthesis/` comparison report |
| "检查知识库" / "健康检查" / "lint" | **lint** (enhanced) | Self-healing health check: broken links / orphans / quality / stale | Console output + auto-fixes |
| "自愈lint" / "自动修复" | **lint** (self-heal mode) | Auto-repair detectable issues | Files modified in place |
| "巩固知识库" / "整理知识库" | **consolidate** | Reinforce high-frequency pages, archive low-frequency | Access records updated, lifecycle state transitions |
| "搜索XX" / "混合搜索XX" | **search** | BM25 keyword search (optionally graph-boosted) | Ranked result list |
| "画个知识图谱" / "看看关联图" | **graph** | Traverse graph-data.json, output node/edge structure | Text graph or relationship tree |
| "XX取代YY" / "supersede" | **supersede** | Mark old page deprecated, new page inherits relationships | Old page status → deprecated |
| "检测矛盾" / "矛盾扫描" | **contradict** | Scan cross-referencing pages for contradictory claims | Contradiction report |
| "初始化知识库" / "新建wiki" | **init** | Create directory skeleton and index files | Empty wiki structure |
| "知识库升级" / "迁移v2" | **migrate** | v1 → v2 migration script | Frontmatter added + BM25 + graph rebuilt |
| "同步知识库" / "mesh-sync" | **mesh-sync** | raw → wiki sync + incremental updates | wiki aligned with raw |
| "删除XX" / "移除素材" | **delete** | Mark deprecated + update relationships | Moved to archive or status → deprecated |
| "结晶化" / "把这个记进知识库" | **crystallize** | Distill conversation into a persistent wiki page | New or updated wiki page |
| "知识库状态" / "现在有什么" | **status** | List entity/topic/source counts + last update | Status summary |

---

## Quick Start

Give the repo URL to your agent and let it install itself:

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

Then just say:

> "Initialize a knowledge base for me."
> "Ingest this: https://..."

---

## Frontmatter

Every wiki page has a v2 frontmatter block:

```yaml
---
confidence: 0.8           # 0.0–1.0, auto-calculated
sources: ["raw/video1.md"]  # source material paths
created: 2026-06-03       # first entry date
last_accessed: 2026-06-03 # last query/access date
access_count: 5           # cumulative access count
status: active             # active | stale | deprecated | archived
---
```

**Confidence levels:**

| Range | Level | Action |
|-------|-------|--------|
| ≥ 0.7 | 🟢 High | Access reinforces; auto-boosted |
| 0.4–0.7 | 🟡 Medium | Needs source or wikilink supplementation |
| < 0.4 | 🔴 Low | Needs source attribution, structure, or linking |

**Lifecycle:**

```
active ──(90 days inactive)──→ stale ──(90 more days)──→ archived
   │                              │
   └──(supersede)──────────────────→ deprecated ──(90 days)──→ archived
```

---

## Directory Structure

```
your-knowledge-base/
├── raw/                     # Raw materials (immutable source)
│   ├── articles/            # Web articles
│   ├── tweets/             # X/Twitter
│   ├── wechat/             # WeChat public accounts
│   └── assets/             # Downloaded images
├── wiki/                   # AI-generated knowledge base
│   ├── index.md            # Master index
│   ├── overview.md         # Overview
│   ├── entities/           # Entity pages (concepts, models, rules)
│   ├── topics/             # Topic pages (courses, modules)
│   ├── sources/            # Source summaries
│   ├── synthesis/          # Deep synthesis reports
│   ├── archive/            # Archived (stale/deprecated) pages
│   ├── my/                # Personal pages
│   └── graph-data.json     # Knowledge graph (v2 new)
├── .wiki-search.db         # BM25 search index (v2 new)
└── .wiki-cache.json        # Ingest cache (source → wiki mapping)
```

---

## Installation Details

### Default locations

| Platform | Path |
|----------|------|
| Claude Code | `~/.claude/skills/llm-wiki` |
| Codex | `~/.codex/skills/llm-wiki` |
| OpenClaw | `~/.openclaw/skills/llm-wiki` |
| Hermes | `~/.hermes/skills/llm-wiki` |

### Upgrade

```bash
bash install.sh --upgrade --platform openclaw
```

### Prerequisites

- Core: agent can run shell commands and read/write files; graph and search need `jq` + `node`
- Optional: `uv` for WeChat extraction; `bun` or `npm` for web scraping; Chrome debug port 9222 for login-gated content

---

## Platform Entrypoints

Each platform has a dedicated guide:

- [Claude Code](platforms/claude/CLAUDE.md)
- [Codex](platforms/codex/AGENTS.md)
- [OpenClaw](platforms/openclaw/README.md)
- [Hermes](platforms/hermes/README.md)

---

## Credits

- **[Andrej Karpathy](https://karpathy.ai/)** — [llm-wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f), core methodology
- **[baoyu-url-to-markdown](https://github.com/JimLiu/baoyu-skills#baoyu-url-to-markdown)** by [JimLiu](https://github.com/JimLiu) — Web & X content extraction
- **youtube-transcript** — YouTube subtitle extraction
- **[wechat-article-to-markdown](https://github.com/jackwener/wechat-article-to-markdown)** — WeChat article extraction

---

## License

MIT
