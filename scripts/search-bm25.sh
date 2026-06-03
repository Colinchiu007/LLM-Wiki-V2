#!/usr/bin/env bash
# llm-wiki-v2: BM25 搜索
# 用法: search-bm25.sh <wiki_root> "<query>" [--top-k 20]

set -euo pipefail

WIKI_ROOT="${1:?Usage: search-bm25.sh <wiki_root> <query> [top_k]}"
QUERY="${2:?Missing query}"
TOP_K="${3:-20}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LIB_DIR="$SCRIPT_DIR/../lib"

python "$LIB_DIR/search.py" bm25-search "$WIKI_ROOT" "$QUERY" --top-k "$TOP_K"
