#!/usr/bin/env python3
"""
llm-wiki-v2: v1 → v2 迁移操作

用法:
    python migrate_ops.py frontmatter <wiki_root> [--dry-run]
    python migrate_ops.py detect <wiki_root>     # 检测当前版本
"""

import os
import re
import json
import argparse
from datetime import date
from pathlib import Path

LIB_DIR = os.path.dirname(os.path.abspath(__file__))
if LIB_DIR not in __import__('sys').path:
    __import__('sys').path.insert(0, LIB_DIR)

from confidence import read_page, ensure_v2_frontmatter


def detect_version(wiki_root: str) -> dict:
    """检测知识库版本"""
    wiki_dir = os.path.join(wiki_root, 'wiki')
    if not os.path.isdir(wiki_dir):
        return {'version': 'none', 'reason': 'wiki/ 目录不存在'}

    has_frontmatter_v2 = 0
    has_frontmatter_v1 = 0
    has_only_body = 0

    for root, dirs, files in os.walk(wiki_dir):
        for fname in files:
            if not fname.endswith('.md'):
                continue
            fpath = os.path.join(root, fname)
            try:
                fm, body, _ = read_page(fpath)
                if fm.get('confidence') is not None:
                    has_frontmatter_v2 += 1
                elif fm:
                    has_frontmatter_v1 += 1
                else:
                    has_only_body += 1
            except Exception:
                has_only_body += 1

    total = has_frontmatter_v2 + has_frontmatter_v1 + has_only_body
    if has_frontmatter_v2 > 0:
        return {'version': 'v2', 'v2_pages': has_frontmatter_v2, 'total': total}
    elif has_frontmatter_v1 > 0:
        return {'version': 'v1', 'v1_pages': has_frontmatter_v1, 'plain_pages': has_only_body, 'total': total}
    else:
        return {'version': 'plain', 'plain_pages': total, 'total': total}


def migrate_frontmatter(wiki_root: str, dry_run: bool = False) -> dict:
    """为 v1 页面补充 v2 frontmatter"""
    wiki_dir = os.path.join(wiki_root, 'wiki')

    migrated = []
    skipped = []

    # 加载 .wiki-cache.json 建立 source 映射
    sources_map = {}
    cache_file = os.path.join(wiki_root, '.wiki-cache.json')
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            for entry in cache:
                wiki_path = entry.get('wiki_path', '')
                raw_path = entry.get('raw_path', '')
                if wiki_path and raw_path:
                    sources_map[wiki_path] = raw_path
        except Exception:
            pass

    for root, dirs, files in os.walk(wiki_dir):
        for fname in files:
            if not fname.endswith('.md'):
                continue
            fpath = os.path.join(root, fname)
            rel_path = os.path.relpath(fpath, wiki_root).replace('\\', '/')

            try:
                fm, body, _ = read_page(fpath)

                # 已有 v2 frontmatter(包含 confidence)→ 跳过
                if fm.get('confidence') is not None:
                    skipped.append(rel_path)
                    continue

                # 提取旧置信度注释（如 <!-- confidence: 0.8 -->）
                confidence = 0.5
                content_raw = open(fpath, 'r', encoding='utf-8').read()
                conf_match = re.search(r'<!--\s*confidence:\s*([\d.]+)\s*-->', content_raw)
                if conf_match:
                    try:
                        confidence = float(conf_match.group(1))
                    except ValueError:
                        pass

                # 查找 source
                sources = [sources_map.get(rel_path)] if sources_map.get(rel_path) else []

                # 提取 v1 frontmatter 字段（type/name/category/aliases/tags 等）
                # 它们在第一个 ---...--- 块中，迁移后要合并到 v2 frontmatter
                original_fields = {}
                orig_fm_match = re.search(r'\A\ufeff?---\n(.*?)\n---\n', content_raw, re.DOTALL)
                if orig_fm_match:
                    orig_fm_text = orig_fm_match.group(1)
                    for line in orig_fm_text.split('\n'):
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        if ':' in line:
                            key, val = line.split(':', 1)
                            key = key.strip()
                            if key not in ('confidence', 'sources', 'created', 'last_accessed', 'access_count', 'status'):
                                original_fields[key] = line

                # 构建 v2 frontmatter
                today = date.today().isoformat()
                fm_lines = [
                    "---",
                    f"confidence: {confidence}",
                    f"sources: {json.dumps(sources, ensure_ascii=False)}",
                    f"created: {today}",
                    f"last_accessed: {today}",
                    "access_count: 0",
                    "status: active",
                ]
                # 合并原始字段
                for key in ['type', 'name', 'category', 'aliases', 'tags', 'description']:
                    if key in original_fields:
                        fm_lines.append(original_fields[key])
                # 追加其他未列出的原始字段
                for key, line in original_fields.items():
                    if key not in ('type', 'name', 'category', 'aliases', 'tags', 'description'):
                        fm_lines.append(line)
                fm_lines.append("---")
                fm_lines.append("")

                # 清理旧内容：旧 frontmatter + confidence 注释 + BOM
                new_body = re.sub(r'\A\ufeff?', '', content_raw)
                new_body = re.sub(r'<!--\s*confidence:\s*[\d.]+\s*-->\n?', '', new_body)
                new_body = re.sub(r'^---\n.*?\n---\n?', '', new_body, flags=re.DOTALL).strip()
                new_body = re.sub(r'^\n+', '', new_body)

                new_content = '\n'.join(fm_lines) + new_body + '\n'

                if not dry_run:
                    with open(fpath, 'w', encoding='utf-8') as f:
                        f.write(new_content)

                migrated.append({
                    'path': rel_path,
                    'confidence': confidence,
                    'sources': sources,
                })

            except Exception as e:
                skipped.append(rel_path + f" (error: {e})")

    return {
        'migrated': len(migrated),
        'skipped': len(skipped),
        'total': len(migrated) + len(skipped),
        'dry_run': dry_run,
        'samples': migrated[:5],
    }


def main():
    parser = argparse.ArgumentParser(description='llm-wiki-v2 迁移操作')
    sub = parser.add_subparsers(dest='command')

    p_detect = sub.add_parser('detect', help='检测知识库版本')
    p_detect.add_argument('wiki_root')

    p_fm = sub.add_parser('frontmatter', help='迁移 frontmatter')
    p_fm.add_argument('wiki_root')
    p_fm.add_argument('--dry-run', action='store_true')

    args = parser.parse_args()

    if args.command == 'detect':
        result = detect_version(args.wiki_root)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.command == 'frontmatter':
        result = migrate_frontmatter(args.wiki_root, args.dry_run)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
