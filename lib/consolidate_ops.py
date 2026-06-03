#!/usr/bin/env python3
"""
llm-wiki-v2: 知识巩固操作

用法:
    python consolidate_ops.py identify <wiki_root>
    python consolidate_ops.py reinforce <wiki_root> [--dry-run]
    python consolidate_ops.py archive <wiki_root> [--dry-run]
"""

import os
import re
import sys
import json
import shutil
import argparse
from datetime import date
from pathlib import Path

# 自动添加 lib 目录到 sys.path
LIB_DIR = os.path.dirname(os.path.abspath(__file__))
if LIB_DIR not in sys.path:
    sys.path.insert(0, LIB_DIR)

from confidence import read_page, ensure_v2_frontmatter, calculate_confidence, reinforce as reinforce_page


def identify(wiki_root: str):
    """识别高频/高置信度页面"""
    wiki_dir = os.path.join(wiki_root, 'wiki')
    
    pages = []
    for root, dirs, files in os.walk(wiki_dir):
        for fname in files:
            if not fname.endswith('.md'):
                continue
            fpath = os.path.join(root, fname)
            try:
                fm, body, _ = read_page(fpath)
                fm = ensure_v2_frontmatter(fm)
                conf = calculate_confidence(fm)
                pages.append({
                    'path': os.path.relpath(fpath, wiki_root).replace('\\', '/'),
                    'confidence': conf,
                    'access_count': fm.get('access_count', 0),
                    'status': fm.get('status', 'active'),
                })
            except Exception:
                continue
    
    by_conf = sorted(pages, key=lambda x: x['confidence'], reverse=True)[:10]
    by_access = sorted(pages, key=lambda x: x['access_count'], reverse=True)[:10]
    
    seen = set()
    candidates = []
    for p in by_conf + by_access:
        if p['path'] not in seen:
            seen.add(p['path'])
            candidates.append(p)
    
    print(json.dumps({
        'high_confidence': len(by_conf),
        'high_access': len(by_access),
        'total_candidates': len(candidates),
        'candidates': candidates[:10],
    }, ensure_ascii=False, indent=2))


def do_reinforce(wiki_root: str, dry_run: bool = False):
    """强化高置信度页面"""
    wiki_dir = os.path.join(wiki_root, 'wiki')
    reinforced = []
    
    for root, dirs, files in os.walk(wiki_dir):
        for fname in files:
            if not fname.endswith('.md'):
                continue
            fpath = os.path.join(root, fname)
            try:
                fm, _, _ = read_page(fpath)
                fm = ensure_v2_frontmatter(fm)
                conf = calculate_confidence(fm)
                if conf >= 0.7:
                    if not dry_run:
                        reinforce_page(fpath)
                    reinforced.append(os.path.relpath(fpath, wiki_root).replace('\\', '/') + (' (dry-run)' if dry_run else ''))
            except Exception:
                continue
    
    print(json.dumps({
        'reinforced': len(reinforced),
        'pages': reinforced[:10],
    }, ensure_ascii=False, indent=2))


def do_archive(wiki_root: str, dry_run: bool = False):
    """归档低频内容"""
    wiki_dir = os.path.join(wiki_root, 'wiki')
    archive_dir = os.path.join(wiki_dir, 'archive')
    archived = []
    
    for root, dirs, files in os.walk(wiki_dir):
        if 'archive' in root:
            continue
        for fname in files:
            if not fname.endswith('.md'):
                continue
            fpath = os.path.join(root, fname)
            try:
                fm, _, _ = read_page(fpath)
                fm = ensure_v2_frontmatter(fm)
                access_count = int(fm.get('access_count', 0))
                last_accessed_str = fm.get('last_accessed', fm.get('created', ''))
                
                try:
                    last_accessed = date.fromisoformat(str(last_accessed_str))
                    days_since = (date.today() - last_accessed).days
                except (ValueError, TypeError):
                    continue
                
                if access_count < 3 and days_since > 180:
                    rel_path = os.path.relpath(fpath, wiki_root).replace('\\', '/')
                    archived.append({
                        'path': rel_path,
                        'access_count': access_count,
                        'days_since': days_since,
                    })
                    
                    if not dry_run:
                        os.makedirs(archive_dir, exist_ok=True)
                        archive_path = os.path.join(archive_dir, fname)
                        shutil.copy2(fpath, archive_path)
                        
                        with open(fpath, 'w', encoding='utf-8') as f:
                            f.write(f'''---
status: archived
confidence: 0.0
access_count: {access_count}
---

> 本页已归档至 [[archive/{fname.replace('.md', '')}]]，因为超过 {days_since} 天未被访问且访问次数仅 {access_count} 次。
> 如需恢复，请从 archive/ 目录中找回。
''')
            except Exception:
                continue
    
    print(json.dumps({
        'archived': len(archived),
        'dry_run': dry_run,
        'pages': archived[:10],
    }, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description='llm-wiki-v2 知识巩固操作')
    sub = parser.add_subparsers(dest='command')
    
    p_id = sub.add_parser('identify', help='识别高频/高置信度页面')
    p_id.add_argument('wiki_root')
    
    p_re = sub.add_parser('reinforce', help='强化高置信度页面')
    p_re.add_argument('wiki_root')
    p_re.add_argument('--dry-run', action='store_true')
    
    p_ar = sub.add_parser('archive', help='归档低频内容')
    p_ar.add_argument('wiki_root')
    p_ar.add_argument('--dry-run', action='store_true')
    
    args = parser.parse_args()
    
    if args.command == 'identify':
        identify(args.wiki_root)
    elif args.command == 'reinforce':
        do_reinforce(args.wiki_root, args.dry_run)
    elif args.command == 'archive':
        do_archive(args.wiki_root, args.dry_run)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
