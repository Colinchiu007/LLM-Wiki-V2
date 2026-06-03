#!/usr/bin/env bash
# llm-wiki-v2: 自愈 lint
# 用法: self-heal.sh <wiki_root> [--dry-run]
#
# 自动修复：
#   1. 缺失 frontmatter → 补充默认 v2 frontmatter
#   2. 断链检测 → 标记 [[不存在页面]]
#   3. 置信度衰减检查 → 更新 status: stale/deprecated
#   4. 孤立页面检测 → 标记无入链页面
#   5. 重复内容检测 → 标记高相似度页面

set -euo pipefail

WIKI_ROOT="${1:?Usage: self-heal.sh <wiki_root> [--dry-run]}"
DRY_RUN="${2:-}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LIB_DIR="$SCRIPT_DIR/../lib"

if [ "$DRY_RUN" = "--dry-run" ]; then
    echo "🔍 自愈 lint (dry-run 模式，不会修改文件)"
else
    echo "🔧 自愈 lint (将自动修复问题)"
fi

# 1. 置信度衰减检查
echo ""
echo "=== 1. 置信度衰减检查 ==="
python "$LIB_DIR/confidence.py" decay-check "$WIKI_ROOT" $([ "$DRY_RUN" = "--dry-run" ] && echo "--dry-run")

# 2. 质量评分（低于阈值的页面）
echo ""
echo "=== 2. 质量评分检查 ==="
python "$LIB_DIR/quality.py" batch-score "$WIKI_ROOT" --threshold 0.4

# 3. 缺失 frontmatter 检测与修复
echo ""
echo "=== 3. Frontmatter 补充 ==="
python -c "
import os, re, json
from pathlib import Path
from datetime import date

wiki_root = '$WIKI_ROOT'
wiki_dir = os.path.join(wiki_root, 'wiki')
dry_run = '$DRY_RUN' == '--dry-run'

missing_fm = []
for root, dirs, files in os.walk(wiki_dir):
    for fname in files:
        if not fname.endswith('.md'):
            continue
        fpath = os.path.join(root, fname)
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if not content.startswith('---'):
            missing_fm.append(fpath)
            
            if not dry_run:
                # 生成默认 frontmatter
                rel_path = os.path.relpath(fpath, wiki_dir)
                fm = f'''---
confidence: 0.5
sources: []
created: {date.today().isoformat()}
last_accessed: {date.today().isoformat()}
access_count: 0
status: active
---

'''
                with open(fpath, 'w', encoding='utf-8') as f:
                    f.write(fm + content)

result = {
    'missing_frontmatter': len(missing_fm),
    'fixed': 0 if dry_run else len(missing_fm),
    'dry_run': dry_run,
    'pages': [os.path.relpath(p, wiki_root) for p in missing_fm[:10]],
}
print(json.dumps(result, ensure_ascii=False, indent=2))
"

# 4. 断链检测
echo ""
echo "=== 4. 断链检测 ==="
python -c "
import os, re, json
from pathlib import Path

wiki_root = '$WIKI_ROOT'
wiki_dir = os.path.join(wiki_root, 'wiki')

# 收集所有存在的页面名
existing = set()
for root, dirs, files in os.walk(wiki_dir):
    for fname in files:
        if fname.endswith('.md'):
            existing.add(fname.replace('.md', ''))

# 扫描所有 [[wikilinks]]
broken = []
for root, dirs, files in os.walk(wiki_dir):
    for fname in files:
        if not fname.endswith('.md'):
            continue
        fpath = os.path.join(root, fname)
        rel_path = os.path.relpath(fpath, wiki_dir)
        
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        links = re.findall(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', content)
        for link in links:
            link = link.strip()
            if link and link not in existing:
                broken.append({
                    'source': rel_path,
                    'target': link,
                })

result = {
    'broken_links': len(broken),
    'links': broken[:20],
}
print(json.dumps(result, ensure_ascii=False, indent=2))
"

# 5. 孤立页面检测
echo ""
echo "=== 5. 孤立页面检测 ==="
python -c "
import os, re, json
from pathlib import Path

wiki_root = '$WIKI_ROOT'
wiki_dir = os.path.join(wiki_root, 'wiki')

# 收集所有页面名和它们链接的目标
page_names = set()  # 所有页面名
outgoing = {}  # 页面 → 链接目标集
incoming = {}  # 页面 → 被谁链接

for root, dirs, files in os.walk(wiki_dir):
    for fname in files:
        if not fname.endswith('.md'):
            continue
        name = fname.replace('.md', '')
        fpath = os.path.join(root, fname)
        page_names.add(name)
        outgoing[name] = set()
        incoming.setdefault(name, set())
        
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        links = re.findall(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', content)
        for link in links:
            link = link.strip()
            if link:
                outgoing[name].add(link)
                incoming.setdefault(link, set()).add(name)

# 孤立页面：没有入链（除了 index.md）
orphans = []
for name in sorted(page_names):
    if name == 'index':
        continue
    if not incoming.get(name):
        orphans.append(name)

result = {
    'orphan_pages': len(orphans),
    'pages': orphans[:20],
}
print(json.dumps(result, ensure_ascii=False, indent=2))
"

echo ""
echo "✅ 自愈 lint 完成"
