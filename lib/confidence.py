#!/usr/bin/env python3
"""
llm-wiki-v2: 置信度计算与知识生命周期管理

用法:
    python confidence.py calculate <page_path> [--date YYYY-MM-DD]
    python confidence.py reinforce <page_path>
    python confidence.py decay-check <wiki_root> [--dry-run]
    python confidence.py access <page_path>
"""

import os
import re
import sys
import json
import argparse
from datetime import datetime, date
from pathlib import Path

# ============ Frontmatter 解析 ============

FRONTMATTER_RE = re.compile(r'^---\n(.*?)\n---', re.DOTALL)


def parse_frontmatter(content: str) -> dict:
    """解析 YAML frontmatter，返回字典。无 frontmatter 时返回空字典。"""
    m = FRONTMATTER_RE.match(content)
    if not m:
        return {}
    fm_text = m.group(1)
    result = {}
    current_key = None
    current_list = None
    
    for line in fm_text.split('\n'):
        # 列表项
        if line.strip().startswith('- ') and current_list is not None:
            current_list.append(line.strip()[2:].strip('"\''))
            continue
        # 键值对
        m2 = re.match(r'^(\w+)\s*:\s*(.*)', line)
        if m2:
            key, val = m2.group(1), m2.group(2).strip()
            if val == '':
                result[key] = []
                current_list = result[key]
            else:
                # 尝试类型转换
                try:
                    result[key] = float(val) if '.' in val else int(val)
                except ValueError:
                    if val.lower() == 'true':
                        result[key] = True
                    elif val.lower() == 'false':
                        result[key] = False
                    elif val.startswith('[') and val.endswith(']'):
                        result[key] = [x.strip().strip('"\'') for x in val[1:-1].split(',') if x.strip()]
                    else:
                        result[key] = val.strip('"\'')
                current_list = None
    return result


def extract_frontmatter_and_body(content: str) -> tuple:
    """返回 (frontmatter_dict, body_text)"""
    m = FRONTMATTER_RE.match(content)
    if not m:
        return {}, content
    return parse_frontmatter(content), content[m.end():]


def serialize_frontmatter(fm: dict) -> str:
    """将字典序列化为 YAML frontmatter 文本"""
    lines = ['---']
    for key, val in fm.items():
        if isinstance(val, list):
            lines.append(f'{key}:')
            for item in val:
                lines.append(f'  - {item}')
        elif isinstance(val, bool):
            lines.append(f'{key}: {str(val).lower()}')
        else:
            lines.append(f'{key}: {val}')
    lines.append('---')
    return '\n'.join(lines)


def read_page(page_path: str) -> tuple:
    """读取页面文件，返回 (frontmatter_dict, body_text, raw_content)"""
    with open(page_path, 'r', encoding='utf-8') as f:
        content = f.read()
    fm, body = extract_frontmatter_and_body(content)
    return fm, body, content


def write_page(page_path: str, fm: dict, body: str):
    """写入页面文件（frontmatter + body）"""
    output = serialize_frontmatter(fm) + '\n' + body
    with open(page_path, 'w', encoding='utf-8') as f:
        f.write(output)


def ensure_v2_frontmatter(fm: dict) -> dict:
    """确保 frontmatter 包含 v2 必需字段，缺失则填充默认值"""
    defaults = {
        'confidence': 0.5,
        'sources': [],
        'created': date.today().isoformat(),
        'last_accessed': date.today().isoformat(),
        'access_count': 0,
        'status': 'active',
    }
    for key, default_val in defaults.items():
        if key not in fm:
            fm[key] = default_val
    return fm


# ============ 置信度计算 ============

def calculate_confidence(fm: dict, current_date: date = None) -> float:
    """
    基于 Ebbinghaus 遗忘曲线计算置信度
    
    公式:
        base = 0.5
        source_bonus = min(len(sources), 3) × 0.1
        authority_bonus = authority × 0.2
        access_bonus = min(access_count, 10) × 0.02
        decay = 0.5 ** (days_since_last_access / 30)   # 30 天半衰期
        confidence = (base + source_bonus + authority_bonus + access_bonus) × decay
    """
    if current_date is None:
        current_date = date.today()
    
    base = 0.5
    
    # 来源数量加分
    sources = fm.get('sources', [])
    if isinstance(sources, str):
        sources = [sources]
    source_bonus = min(len(sources), 3) * 0.1
    
    # 来源权威度
    authority = float(fm.get('authority', 0.5))
    authority_bonus = authority * 0.2
    
    # 访问次数加分（强化）
    access_count = int(fm.get('access_count', 0))
    access_bonus = min(access_count, 10) * 0.02
    
    # 时间衰减（Ebbinghaus 遗忘曲线）
    last_accessed_str = fm.get('last_accessed', fm.get('created', date.today().isoformat()))
    try:
        last_accessed = date.fromisoformat(str(last_accessed_str))
        days_since = (current_date - last_accessed).days
    except (ValueError, TypeError):
        days_since = 0
    
    decay = 0.5 ** (max(days_since, 0) / 30)
    
    confidence = (base + source_bonus + authority_bonus + access_bonus) * decay
    return round(min(confidence, 0.99), 2)


def get_retrieval_priority(fm: dict, current_date: date = None) -> float:
    """返回检索优先级分数（越高越优先）"""
    import math
    confidence = calculate_confidence(fm, current_date)
    access_count = int(fm.get('access_count', 0))
    
    # 基础优先级 = 置信度 × log(访问次数 + 1)
    priority = confidence * math.log1p(access_count)
    
    # 状态降级
    status = fm.get('status', 'active')
    if status == 'stale':
        priority *= 0.5
    elif status == 'deprecated':
        priority *= 0.1
    elif status == 'superseded':
        priority *= 0.01
    
    return round(priority, 4)


# ============ 生命周期操作 ============

def record_access(page_path: str) -> dict:
    """记录页面被访问：更新 last_accessed 和 access_count"""
    fm, body, _ = read_page(page_path)
    fm = ensure_v2_frontmatter(fm)
    
    fm['last_accessed'] = date.today().isoformat()
    fm['access_count'] = int(fm.get('access_count', 0)) + 1
    fm['confidence'] = calculate_confidence(fm)
    
    write_page(page_path, fm, body)
    return fm


def reinforce(page_path: str) -> dict:
    """强化页面置信度（巩固时调用）"""
    fm, body, _ = read_page(page_path)
    fm = ensure_v2_frontmatter(fm)
    
    fm['last_accessed'] = date.today().isoformat()
    fm['access_count'] = int(fm.get('access_count', 0)) + 1
    fm['confidence'] = calculate_confidence(fm)
    
    # 质量评分（如果有的话）也强化
    if 'quality' in fm:
        fm['quality'] = min(float(fm['quality']) + 0.05, 0.99)
    
    write_page(page_path, fm, body)
    return fm


def check_lifecycle(wiki_root: str, dry_run: bool = False) -> list:
    """
    检查所有页面的生命周期状态
    返回需要变更的页面列表 [{path, old_status, new_status, reason}]
    """
    changes = []
    wiki_dir = os.path.join(wiki_root, 'wiki')
    today = date.today()
    
    for root, dirs, files in os.walk(wiki_dir):
        for fname in files:
            if not fname.endswith('.md'):
                continue
            fpath = os.path.join(root, fname)
            
            try:
                fm, body, _ = read_page(fpath)
            except Exception:
                continue
            
            if not fm:
                continue
            
            current_status = fm.get('status', 'active')
            last_accessed_str = fm.get('last_accessed', fm.get('created'))
            
            if not last_accessed_str:
                continue
            
            try:
                last_accessed = date.fromisoformat(str(last_accessed_str))
                days_since = (today - last_accessed).days
            except (ValueError, TypeError):
                continue
            
            new_status = current_status
            reason = ''
            
            if current_status == 'active' and days_since > 90:
                new_status = 'stale'
                reason = f'{days_since} 天未访问（>90 天阈值）'
            elif current_status == 'stale' and days_since > 180:
                new_status = 'deprecated'
                reason = f'{days_since} 天未访问（>180 天阈值）'
            
            if new_status != current_status:
                changes.append({
                    'path': fpath,
                    'old_status': current_status,
                    'new_status': new_status,
                    'reason': reason,
                    'days_since': days_since,
                })
                
                if not dry_run:
                    fm['status'] = new_status
                    write_page(fpath, fm, body)
    
    return changes


# ============ CLI ============

def main():
    parser = argparse.ArgumentParser(description='llm-wiki-v2 置信度与生命周期管理')
    sub = parser.add_subparsers(dest='command')
    
    # calculate
    p_calc = sub.add_parser('calculate', help='计算页面置信度')
    p_calc.add_argument('page_path')
    p_calc.add_argument('--date', help='当前日期 (YYYY-MM-DD)')
    
    # reinforce
    p_reinf = sub.add_parser('reinforce', help='强化页面置信度')
    p_reinf.add_argument('page_path')
    
    # access
    p_access = sub.add_parser('access', help='记录页面访问')
    p_access.add_argument('page_path')
    
    # decay-check
    p_decay = sub.add_parser('decay-check', help='检查生命周期状态')
    p_decay.add_argument('wiki_root')
    p_decay.add_argument('--dry-run', action='store_true')
    
    args = parser.parse_args()
    
    if args.command == 'calculate':
        fm, body, _ = read_page(args.page_path)
        fm = ensure_v2_frontmatter(fm)
        current_date = date.fromisoformat(args.date) if args.date else None
        conf = calculate_confidence(fm, current_date)
        priority = get_retrieval_priority(fm, current_date)
        print(json.dumps({
            'confidence': conf,
            'priority': priority,
            'frontmatter': fm,
        }, ensure_ascii=False, indent=2))
    
    elif args.command == 'reinforce':
        fm = reinforce(args.page_path)
        print(json.dumps({
            'status': 'reinforced',
            'confidence': fm['confidence'],
            'access_count': fm['access_count'],
        }, ensure_ascii=False, indent=2))
    
    elif args.command == 'access':
        fm = record_access(args.page_path)
        print(json.dumps({
            'status': 'accessed',
            'confidence': fm['confidence'],
            'access_count': fm['access_count'],
            'last_accessed': fm['last_accessed'],
        }, ensure_ascii=False, indent=2))
    
    elif args.command == 'decay-check':
        changes = check_lifecycle(args.wiki_root, args.dry_run)
        print(json.dumps({
            'dry_run': args.dry_run,
            'changes': changes,
            'total': len(changes),
        }, ensure_ascii=False, indent=2))
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
