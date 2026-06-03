#!/usr/bin/env python3
"""
llm-wiki-v2: 质量评分

用法:
    python quality.py score <page_path>
    python quality.py batch-score <wiki_root> [--threshold 0.4]
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path
from confidence import parse_frontmatter, extract_frontmatter_and_body, ensure_v2_frontmatter


def check_structure(content: str) -> float:
    """结构完整性评分（0-1）"""
    score = 0.0
    
    # 有标题
    if re.search(r'^# ', content, re.MULTILINE):
        score += 0.3
    
    # 有段落（非单行）
    paragraphs = [p for p in content.split('\n\n') if p.strip() and not p.strip().startswith('#')]
    if len(paragraphs) >= 2:
        score += 0.3
    elif len(paragraphs) >= 1:
        score += 0.15
    
    # 有列表
    if re.search(r'^[-*] ', content, re.MULTILINE):
        score += 0.2
    
    # 有引用/代码块
    if re.search(r'^> ', content, re.MULTILINE) or re.search(r'```', content):
        score += 0.2
    
    return min(score, 1.0)


def check_citation_coverage(content: str, fm: dict) -> float:
    """引用覆盖率评分（0-1）"""
    sources = fm.get('sources', [])
    if isinstance(sources, str):
        sources = [sources]
    
    # 有来源
    if len(sources) >= 3:
        return 1.0
    elif len(sources) >= 2:
        return 0.7
    elif len(sources) >= 1:
        return 0.4
    
    # 检查正文中的引用标记
    citations = re.findall(r'\[\[([^\]]+)\]\]', content)
    if len(citations) >= 3:
        return 0.5
    elif len(citations) >= 1:
        return 0.3
    
    return 0.1


def check_readability(content: str) -> float:
    """可读性评分（简化版，0-1）"""
    # 去除 frontmatter
    body = re.sub(r'^---\n.*?\n---', '', content, flags=re.DOTALL).strip()
    
    if not body:
        return 0.0
    
    # 平均段落长度
    paragraphs = [p for p in body.split('\n\n') if p.strip()]
    if not paragraphs:
        return 0.2
    
    avg_len = sum(len(p) for p in paragraphs) / len(paragraphs)
    
    # 100-300 字最佳
    if 100 <= avg_len <= 300:
        return 0.9
    elif 50 <= avg_len <= 500:
        return 0.6
    else:
        return 0.3


def calculate_quality(page_path: str) -> dict:
    """计算页面质量分数"""
    with open(page_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    fm, body = extract_frontmatter_and_body(content)
    fm = ensure_v2_frontmatter(fm)
    
    scores = {
        'structure': round(check_structure(body), 2),
        'citation': round(check_citation_coverage(body, fm), 2),
        'readability': round(check_readability(body), 2),
    }
    
    # 加权平均
    weights = {'structure': 0.3, 'citation': 0.4, 'readability': 0.3}
    quality = sum(scores[k] * weights[k] for k in scores)
    quality = round(quality, 2)
    
    return {
        'path': page_path,
        'quality': quality,
        'scores': scores,
        'label': (
            'good' if quality >= 0.7 else
            'needs_review' if quality >= 0.4 else
            'low_quality'
        ),
    }


def batch_score(wiki_root: str, threshold: float = 0.4) -> list:
    """批量评分"""
    results = []
    wiki_dir = os.path.join(wiki_root, 'wiki')
    
    for root, dirs, files in os.walk(wiki_dir):
        for fname in files:
            if not fname.endswith('.md'):
                continue
            fpath = os.path.join(root, fname)
            
            try:
                result = calculate_quality(fpath)
                if result['quality'] < threshold:
                    results.append(result)
            except Exception as e:
                results.append({
                    'path': fpath,
                    'quality': 0.0,
                    'error': str(e),
                    'label': 'error',
                })
    
    return results


# ============ CLI ============

def main():
    parser = argparse.ArgumentParser(description='llm-wiki-v2 质量评分')
    sub = parser.add_subparsers(dest='command')
    
    # score
    p_score = sub.add_parser('score', help='评分单个页面')
    p_score.add_argument('page_path')
    
    # batch-score
    p_batch = sub.add_parser('batch-score', help='批量评分')
    p_batch.add_argument('wiki_root')
    p_batch.add_argument('--threshold', type=float, default=0.4)
    
    args = parser.parse_args()
    
    if args.command == 'score':
        result = calculate_quality(args.page_path)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.command == 'batch-score':
        results = batch_score(args.wiki_root, args.threshold)
        print(json.dumps({
            'threshold': args.threshold,
            'below_threshold': len(results),
            'results': results,
        }, ensure_ascii=False, indent=2))
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
