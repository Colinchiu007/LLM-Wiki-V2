#!/usr/bin/env bash
# llm-wiki-v2: v1 → v2 迁移脚本
# 用法: migrate-v1-to-v2.sh <wiki_root> [--dry-run]
#
# 步骤：
#   1. 备份知识库
#   2. 补充 v2 frontmatter
#   3. 构建 BM25 搜索索引
#   4. 重建知识图谱
#   5. 运行自愈 lint

set -euo pipefail

WIKI_ROOT="${1:?Usage: migrate-v1-to-v2.sh <wiki_root> [--dry-run]}"
DRY_RUN="${2:-}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LIB_DIR="$(cd "$SCRIPT_DIR/../lib" && pwd)"

if [ "$DRY_RUN" = "--dry-run" ]; then
    echo "📋 llm-wiki v1 → v2 迁移 (dry-run 模式)"
else
    echo "🔄 llm-wiki v1 → v2 迁移"
fi
echo "目标: $WIKI_ROOT"
echo ""

# 前置检查：确认是 v1 知识库
if [ ! -d "$WIKI_ROOT/wiki" ]; then
    echo "❌ 错误：未找到 wiki/ 目录，不是有效的知识库"
    exit 1
fi

# 1. 备份
if [ "$DRY_RUN" = "--dry-run" ]; then
    echo ""
    echo "=== 1. 备份 ==="
    echo "(dry-run) 会备份到 $WIKI_ROOT-v1-backup-$(date +%Y%m%d)"
elif [ -d "${WIKI_ROOT}-v1-backup-$(date +%Y%m%d)" ]; then
    echo ""
    echo "=== 1. 备份 ==="
    echo "⚠️  今日备份已存在，跳过"
else
    echo ""
    echo "=== 1. 备份 ==="
    cp -r "$WIKI_ROOT" "${WIKI_ROOT}-v1-backup-$(date +%Y%m%d)"
    echo "✅ 备份完成: ${WIKI_ROOT}-v1-backup-$(date +%Y%m%d)"
fi

# 2. 补充 v2 frontmatter（使用独立 Python 脚本避免路径问题）
echo ""
echo "=== 2. 补充 v2 frontmatter ==="
python "$LIB_DIR/migrate_ops.py" frontmatter "$WIKI_ROOT" ${DRY_RUN:+"--dry-run"}

# 3. 构建 BM25 搜索索引
echo ""
echo "=== 3. 构建 BM25 搜索索引 ==="
if [ "$DRY_RUN" != "--dry-run" ]; then
    bash "$SCRIPT_DIR/index-bm25.sh" "$WIKI_ROOT"
else
    echo "(dry-run) 跳过 BM25 索引构建"
fi

# 4. 重建知识图谱
echo ""
echo "=== 4. 重建知识图谱 ==="
if [ "$DRY_RUN" != "--dry-run" ]; then
    python "$LIB_DIR/entities.py" build-graph "$WIKI_ROOT"
else
    echo "(dry-run) 跳过知识图谱重建"
fi

# 5. 运行自愈 lint
echo ""
echo "=== 5. 运行自愈 lint ==="
bash "$SCRIPT_DIR/self-heal.sh" "$WIKI_ROOT" --dry-run

echo ""
if [ "$DRY_RUN" = "--dry-run" ]; then
    echo "📋 dry-run 完成。请确认上述报告后，重新运行去掉 --dry-run 执行实际迁移。"
else
    echo "✅ v1 → v2 迁移完成！"
    echo ""
    echo "下一步："
    echo "  1. 切换 llm-wiki skill 为 v2 版本（如果还没切换）"
    echo "  2. 说'巩固知识库'初始化访问记录"
    echo "  3. 说'检查知识库'验证迁移效果"
fi
