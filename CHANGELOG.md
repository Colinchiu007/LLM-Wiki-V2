# Changelog

## v4.0.0 (2026-06-03) — v2 major release

### What's new in v2

v2 is a parallel track to v1 (3.x), not an upgrade. It adds a complete knowledge lifecycle and governance layer on top of the existing core workflows.

**Architecture**

- **Frontmatter instead of HTML comments** — page metadata (confidence, sources, created, last_accessed, access_count, status) lives in a YAML frontmatter block at the top of each page, not scattered HTML comments in the body
- **Structured knowledge graph** — `wiki/graph-data.json` with typed nodes and semantically-labeled edges; replaces plain wikilink traversal
- **BM25 search index** — `.wiki-search.db` SQLite FTS5 index with jieba Chinese tokenization; replaces plain text grep
- **Hybrid search** — BM25 keyword × graph-structured RRF fusion ranking

**New workflows (17 total)**

| Workflow | Trigger keywords (Chinese) | Description |
|---|---|---|
| `consolidate` | "巩固知识库" / "整理知识库" | Reinforce high-confidence pages, archive low-frequency pages, update access records |
| `search` | "搜索XX" / "混合搜索" | BM25 full-text search with optional graph fusion |
| `supersede` | "XX取代YY" / "supersede" | Mark old page deprecated, new page inherits relationships |
| `contradict` | "检测矛盾" / "矛盾扫描" | Scan cross-referencing pages for contradictory claims |
| `migrate` | "迁移v2" / "知识库升级" | v1 → v2 migration: frontmatter + BM25 + graph rebuild |
| `mesh-sync` | "同步知识库" | raw → wiki sync + incremental updates |
| `crystallize` | "结晶化" | Distill conversation into a persistent wiki page |

**New libraries (`lib/`)**

| Module | Purpose |
|--------|---------|
| `confidence.py` | Confidence auto-calculation (sources × freshness × structure) |
| `entities.py` | Knowledge graph operations (build / traverse / query) |
| `privacy_filter.py` | API key / phone / bank card detection |
| `search.py` | BM25 + jieba + RRF fusion hybrid search |
| `quality.py` | 4-dimension quality scoring (coverage / structure / citation / freshness) |
| `contradiction.py` | Bigram Jaccard + negation word contradiction detection |
| `consolidate_ops.py` | Knowledge consolidation logic |
| `migrate_ops.py` | v1 → v2 migration operations (detect / frontmatter) |

**New scripts (`scripts/`)**

| Script | Purpose |
|--------|---------|
| `index-bm25.sh` | Build/rebuild BM25 FTS5 index for a knowledge base |
| `search-bm25.sh` | Query the BM25 index |
| `self-heal.sh` | Auto-fix broken links, orphan pages, stale pages |
| `consolidate.sh` | Knowledge consolidation runner |
| `supersede.sh` | Version supersession runner |
| `audit-logger.sh` | Audit log writer |
| `auto-ingest-daemon.sh` | Event-driven ingest daemon |
| `scan-raw.sh` | Scan raw directory for new content |
| `mesh-sync.sh` | raw → wiki sync |
| `register-cron.sh` | Register OpenClaw cron jobs |
| `migrate-v1-to-v2.sh` | v1 → v2 migration orchestrator |

**Lifecycle states**

```
active ──(90 days inactive)──→ stale ──(90 more days)──→ archived
   │                              │
   └──(supersede)──────────────────→ deprecated ──(90 days)──→ archived
```

**Known issues carried from v1**

- FTS5 `rank` column returns 0 in some SQLite versions (non-blocking, used as weight only)
- `privacy_filter.py` may false-positive on some number sequences matching bank card pattern

### Migration from v1

```bash
bash scripts/migrate-v1-to-v2.sh <wiki_root>
```

The script is idempotent — safe to re-run.

What it does:
1. Adds v2 frontmatter to every page (merging original v1 fields: type/name/category/aliases/tags)
2. Builds BM25 index for all pages
3. Rebuilds knowledge graph from wikilinks
4. Handles BOM characters in migrated files

---

## v3.5.0 (2026-04-24)

### Added

- `.wiki-schema.md` new "alias glossary" section: user maintains synonym groups (e.g., `LLM = 大语言模型 = 大模型`), query and digest automatically expand aliases before searching
- query workflow reads alias glossary before search, expands all synonyms
- digest workflow also supports alias expansion
- ingest recommends adding new synonyms when found

## v3.4.0 (2026-04-24)

### Added

- source template new `image_paths` frontmatter field
- ingest tracks downloaded image count and paths; lint checks for missing files
- `lint-runner.sh` new image asset consistency check

## v3.3.1 (2026-04-24)

### Added

- ingest (full + simplified) detects image references after saving source, reminds user to download
- source template new `images` frontmatter field

## v3.3.0 (2026-04-24)

### Added

- Learning cockpit refactored: 5-section left nav (community, focus, search, queue, recommended start)
- Current topic focus mode
- Learning queue MVP: node bookmarks, study notes, recent entries
- Query/digest/ingest single-page length limits (2000/3000 chars)
- Query results sorted by relevance: exact filename > index entry > body keyword
- Step 1 JSON contract new `evidence` field
- `docs/obsidian.md` Obsidian integration guide
- `scripts/lint-fix.sh` low-risk auto-fix script

## v3.0.0 (2026-04-20)

### Added

- **Watercolor-card interactive knowledge graph** — `wiki/knowledge-graph.html`, d3 + rough.js, offline-capable

### Removed

- classic (vis-network) and paper (hand-drawn notebook) graph styles

---

*For versions 2.6.0 through 3.2.1, see git history.*
