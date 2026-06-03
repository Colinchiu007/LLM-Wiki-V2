#!/usr/bin/env bash
# llm-wiki-v2: 知识巩固
# 用法: consolidate.sh <wiki_root> [--dry-run]

set -euo pipefail

WIKI_ROOT="${1:?Usage: consolidate.sh <wiki_root> [--dry-run]}"
DRY_RUN="${2:-}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LIB_DIR="$(cd "$SCRIPT_DIR/../lib" && pwd)"

if [ "$DRY_RUN" = "--dry-run" ]; then
    echo "📋 知识巩固 (dry-run 模式)"
else
    echo "🔄 知识巩固"
fi

# 1. 识别高频访问内容
echo ""
echo "=== 1. 识别高频/高置信度页面 ==="
python "$LIB_DIR/consolidate_ops.py" identify "$WIKI_ROOT"

# 2. 强化高置信度页面
echo ""
echo "=== 2. 强化高置信度页面 ==="
if [ "$DRY_RUN" = "--dry-run" ]; then
    python "$LIB_DIR/consolidate_ops.py" reinforce "$WIKI_ROOT" --dry-run
else
    python "$LIB_DIR/consolidate_ops.py" reinforce "$WIKI_ROOT"
fi

# 3. 归档低频内容
echo ""
echo "=== 3. 归档低频内容 ==="
if [ "$DRY_RUN" = "--dry-run" ]; then
    python "$LIB_DIR/consolidate_ops.py" archive "$WIKI_ROOT" --dry-run
else
    python "$LIB_DIR/consolidate_ops.py" archive "$WIKI_ROOT"
fi

# 4. 更新索引和日志
echo ""
echo "=== 4. 更新索引和日志 ==="
if [ "$DRY_RUN" != "--dry-run" ]; then
    DATE=$(date +%Y-%m-%d)
    LOG_FILE="$WIKI_ROOT/log.md"
    if [ -f "$LOG_FILE" ]; then
        echo "" >> "$LOG_FILE"
        echo "## $DATE consolidate | 知识巩固" >> "$LOG_FILE"
        echo "- 自动巩固完成" >> "$LOG_FILE"
    fi
    bash "$SCRIPT_DIR/audit-logger.sh" "$WIKI_ROOT" consolidate "知识库自动巩固" "系统自动" 2>/dev/null || true
    echo "✅ 索引和日志已更新"
else
    echo "(dry-run) 跳过索引和日志更新"
fi

echo ""
echo "✅ 知识巩固完成"
