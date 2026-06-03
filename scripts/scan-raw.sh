#!/usr/bin/env bash
# llm-wiki-v2: raw/ 目录扫描（用于 cron 定时触发）
# 用法: scan-raw.sh <wiki_root>
#
# 检查 raw/ 目录是否有未消化的新文件（不在 .wiki-cache.json 中的）
# 输出 JSON 列表，供 LLM 决定是否触发 ingest

set -euo pipefail

WIKI_ROOT="${1:?Usage: scan-raw.sh <wiki_root>}"
RAW_DIR="$WIKI_ROOT/raw"
CACHE_FILE="$WIKI_ROOT/.wiki-cache.json"

if [ ! -d "$RAW_DIR" ]; then
    echo '{"status":"no_raw_dir","new_files":[]}'
    exit 0
fi

python -c "
import os, json

wiki_root = '$WIKI_ROOT'
raw_dir = os.path.join(wiki_root, 'raw')
cache_file = os.path.join(wiki_root, '.wiki-cache.json')

# 加载已消化的文件列表
digested = set()
if os.path.exists(cache_file):
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache = json.load(f)
        for entry in cache:
            raw_path = entry.get('raw_path', '')
            if raw_path:
                digested.add(raw_path.replace('\\\\', '/'))
    except Exception:
        pass

# 扫描 raw/ 目录
new_files = []
for root, dirs, files in os.walk(raw_dir):
    for fname in files:
        # 跳过隐藏文件和临时文件
        if fname.startswith('.') or fname.endswith('.tmp') or fname.endswith('.bak'):
            continue
        fpath = os.path.join(root, fname)
        rel_path = os.path.relpath(fpath, wiki_root).replace('\\\\', '/')
        
        if rel_path not in digested:
            # 获取文件大小和修改时间
            stat = os.stat(fpath)
            new_files.append({
                'path': rel_path,
                'size_kb': round(stat.st_size / 1024, 1),
                'modified': __import__('datetime').datetime.fromtimestamp(stat.st_mtime).isoformat()[:10],
            })

print(json.dumps({
    'status': 'ok',
    'new_files': new_files,
    'total': len(new_files),
}, ensure_ascii=False, indent=2))
"
