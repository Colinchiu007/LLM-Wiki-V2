#!/usr/bin/env bash
# llm-wiki-v2: BM25 索引构建
# 用法: index-bm25.sh <wiki_root>

set -euo pipefail

WIKI_ROOT="${1:?Usage: index-bm25.sh <wiki_root>}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LIB_DIR="$SCRIPT_DIR/../lib"

echo "🔍 构建 BM25 搜索索引..."

python "$LIB_DIR/search.py" index-bm25 "$WIKI_ROOT"

echo "✅ BM25 索引构建完成"
