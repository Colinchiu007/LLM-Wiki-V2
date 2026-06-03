#!/usr/bin/env bash
# llm-wiki-v2: 审计日志
# 用法: audit-logger.sh <wiki_root> <operation> <target> <reason>

set -euo pipefail

WIKI_ROOT="${1:?Usage: audit-logger.sh <wiki_root> <operation> <target> <reason>}"
OPERATION="${2:?Missing operation}"
TARGET="${3:?Missing target}"
REASON="${4:-}"

AUDIT_LOG="$WIKI_ROOT/wiki/.audit.log"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
AGENT_ID="${AGENT_ID:-local}"

# 确保目录存在
mkdir -p "$(dirname "$AUDIT_LOG")"

# 追加审计日志
echo "$TIMESTAMP | $OPERATION | $TARGET | $REASON | agent:$AGENT_ID" >> "$AUDIT_LOG"

echo "📝 审计日志已记录: $OPERATION | $TARGET"
