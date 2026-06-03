#!/usr/bin/env bash
# llm-wiki-v2: 版本取代
# 用法: supersede.sh <wiki_root> <old_page_rel> <new_page_rel>
# 例如: supersede.sh /path/to/wiki "wiki/entities/Old.md" "wiki/entities/New.md"

set -euo pipefail

WIKI_ROOT="${1:?Usage: supersede.sh <wiki_root> <old_page> <new_page>}"
OLD_PAGE="${2:?Missing old_page}"
NEW_PAGE="${3:?Missing new_page}"

OLD_PATH="$WIKI_ROOT/$OLD_PAGE"
NEW_PATH="$WIKI_ROOT/$NEW_PAGE"
ARCHIVE_DIR="$WIKI_ROOT/wiki/archive"

# 检查文件存在
if [ ! -f "$OLD_PATH" ]; then
    echo "❌ 旧页面不存在: $OLD_PATH"
    exit 1
fi

if [ ! -f "$NEW_PATH" ]; then
    echo "❌ 新页面不存在: $NEW_PATH"
    exit 1
fi

# 创建归档目录
mkdir -p "$ARCHIVE_DIR"

# 1. 更新旧页面 frontmatter: status=superseded, superseded_by=[new_page]
python3 "$(dirname "$0")/../lib/confidence.py" access "$OLD_PATH" 2>/dev/null || \
python "$(dirname "$0")/../lib/confidence.py" access "$OLD_PATH" 2>/dev/null || true

# 使用 Python 直接修改 frontmatter
python -c "
import sys
sys.path.insert(0, '$(dirname "$0")/../lib')
from confidence import read_page, write_page, ensure_v2_frontmatter
from datetime import date

fm, body, _ = read_page('$OLD_PATH')
fm = ensure_v2_frontmatter(fm)
fm['status'] = 'superseded'
fm['superseded_by'] = ['$NEW_PAGE']
write_page('$OLD_PATH', fm, body)
print('✅ 旧页面已标记为 superseded')
"

# 2. 在新页面正文顶部添加更新说明
UPDATE_NOTE="
> **更新说明**：本页取代了 [[$(basename "$OLD_PAGE" .md)]]（$(date +%Y-%m-%d)），旧版内容已归档至 archive/。
"

python -c "
import sys, re
sys.path.insert(0, '$(dirname "$0")/../lib')
from confidence import read_page, write_page, ensure_v2_frontmatter

fm, body, content = read_page('$NEW_PATH')
fm = ensure_v2_frontmatter(fm)

# 在正文顶部（frontmatter 之后）插入更新说明
if '取代了' not in body:
    body = '''
$UPDATE_NOTE
''' + body

write_page('$NEW_PATH', fm, body)
print('✅ 新页面已添加更新说明')
"

# 3. 移动旧页面到 archive/
OLD_FILENAME=$(basename "$OLD_PATH")
ARCHIVE_PATH="$ARCHIVE_DIR/$OLD_FILENAME"

if [ ! -f "$ARCHIVE_PATH" ]; then
    cp "$OLD_PATH" "$ARCHIVE_PATH"
    echo "✅ 旧页面已复制到 archive/"
fi

# 在原位置保留引用
cat > "$OLD_PATH" << EOF
---
status: superseded
superseded_by:
  - $NEW_PAGE
confidence: 0.0
redirect: true
---

> 本页已归档至 [[archive/$(basename "$OLD_FILENAME" .md)]]，被 [[$(basename "$NEW_PAGE" .md)]] 取代。
> 请访问新页面获取最新信息。
EOF

echo "✅ 原位置已替换为重定向引用"

# 4. 更新图谱
GRAPH_FILE="$WIKI_ROOT/wiki/graph-data.json"
if [ -f "$GRAPH_FILE" ]; then
    python -c "
import json
with open('$GRAPH_FILE', 'r', encoding='utf-8') as f:
    graph = json.load(f)

# 将指向旧节点的边迁移到新节点
for edge in graph.get('edges', []):
    if edge.get('source') == '$OLD_PAGE':
        edge['source'] = '$NEW_PAGE'
    if edge.get('target') == '$OLD_PAGE':
        edge['target'] = '$NEW_PAGE'

# 标记旧节点为 deprecated
for node in graph.get('nodes', []):
    if node.get('id') == '$OLD_PAGE':
        node['status'] = 'deprecated'

with open('$GRAPH_FILE', 'w', encoding='utf-8') as f:
    json.dump(graph, f, ensure_ascii=False, indent=2)

print('✅ 知识图谱已更新')
"
fi

# 5. 审计日志
bash "$(dirname "$0")/audit-logger.sh" "$WIKI_ROOT" supersede "$OLD_PAGE → $NEW_PAGE" "用户确认" 2>/dev/null || true

echo ""
echo "版本取代完成："
echo "  旧页面: $OLD_PAGE → status: superseded"
echo "  新页面: $NEW_PAGE"
echo "  归档位置: archive/$OLD_FILENAME"
