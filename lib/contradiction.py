#!/usr/bin/env python3
"""
llm-wiki-v2: 矛盾检测

扫描同一实体的不同声明，检测矛盾信息。

用法:
    python contradiction.py scan <wiki_root> [--threshold 0.7]
    python contradiction.py check <wiki_root> <page1> <page2>
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path
from confidence import read_page, ensure_v2_frontmatter


def extract_claims(content: str) -> list:
    """
    从页面正文中提取声明（claim）。
    简化版：提取每个以 "- " 开头的列表项，或每个独立段落的第一句话。
    """
    # 去除 frontmatter
    body = re.sub(r'^---\n.*?\n---', '', content, flags=re.DOTALL).strip()
    
    claims = []
    
    # 提取列表项
    for line in body.split('\n'):
        line = line.strip()
        if line.startswith('- ') or line.startswith('* '):
            claim = line[2:].strip()
            # 清理 markdown 格式
            claim = re.sub(r'\*\*(.*?)\*\*', r'\1', claim)
            claim = re.sub(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', r'\1', claim)
            if len(claim) > 10:  # 过短的不算声明
                claims.append(claim)
    
    # 提取段落首句（段落以连续两个换行分隔）
    paragraphs = [p.strip() for p in body.split('\n\n') if p.strip()]
    for para in paragraphs:
        # 跳过标题、列表、引用
        if para.startswith('#') or para.startswith('-') or para.startswith('>'):
            continue
        # 取第一句
        sentences = re.split(r'[。！？\.!?]', para)
        if sentences:
            first = sentences[0].strip()
            first = re.sub(r'\*\*(.*?)\*\*', r'\1', first)
            first = re.sub(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', r'\1', first)
            if 10 < len(first) < 200:
                claims.append(first)
    
    return claims


def text_similarity(text1: str, text2: str) -> float:
    """
    简化的文本相似度（基于字符级 Jaccard 相似度 + 关键词重叠）
    返回 0-1 之间的相似度分数
    """
    # 提取关键词（简单的字符级 n-gram）
    def ngrams(text, n=2):
        return set(text[i:i+n] for i in range(len(text)-n+1))
    
    ng1 = ngrams(text1)
    ng2 = ngrams(text2)
    
    if not ng1 or not ng2:
        return 0.0
    
    intersection = ng1 & ng2
    union = ng1 | ng2
    
    return len(intersection) / len(union)


def find_same_entity_pages(wiki_root: str) -> dict:
    """
    找出同一实体的不同页面（名称相似或互相引用同一实体）
    返回 {entity_name: [page_paths]}
    """
    wiki_dir = os.path.join(wiki_root, 'wiki')
    entity_pages = {}
    
    entities_dir = os.path.join(wiki_dir, 'entities')
    if os.path.isdir(entities_dir):
        for fname in os.listdir(entities_dir):
            if fname.endswith('.md'):
                name = fname.replace('.md', '')
                fpath = os.path.join(entities_dir, fname)
                entity_pages.setdefault(name, []).append(fpath)
    
    return entity_pages


def scan_contradictions(wiki_root: str, threshold: float = 0.7) -> list:
    """
    扫描知识库中的矛盾声明
    
    策略：
    1. 找出互相引用的实体对（A 引用 B，B 引用 A）
    2. 比较它们的声明，如果相似度高但观点不同，标记为潜在矛盾
    3. 检查同一实体的多个来源是否有冲突
    """
    wiki_dir = os.path.join(wiki_root, 'wiki')
    contradictions = []
    
    # 收集所有页面及其声明
    pages_claims = {}
    for root, dirs, files in os.walk(wiki_dir):
        for fname in files:
            if not fname.endswith('.md'):
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    content = f.read()
                claims = extract_claims(content)
                if claims:
                    rel_path = os.path.relpath(fpath, wiki_root).replace('\\', '/')
                    pages_claims[rel_path] = claims
            except Exception:
                continue
    
    # 比较相关页面之间的声明
    # 优化：只比较有共同 wikilink 引用的页面对（而非全量 O(n²)）
    page_list = list(pages_claims.keys())
    
    # 构建引用图：找出互相引用或有共同引用的页面对
    link_pairs = set()
    page_links = {}  # path -> set of wikilink targets
    
    for path in page_list:
        fpath = os.path.join(wiki_dir, path)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
            links = set(re.findall(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', content))
            page_links[path] = links
        except Exception:
            page_links[path] = set()
    
    
    # 只比较有共同引用的页面对
    for i in range(len(page_list)):
        for j in range(i + 1, len(page_list)):
            p1, p2 = page_list[i], page_list[j]
            links1 = page_links.get(p1, set())
            links2 = page_links.get(p2, set())
            # 有共同引用，或互相引用
            if links1 & links2 or p2.replace('.md', '') in links1 or p1.replace('.md', '') in links2:
                link_pairs.add((p1, p2))
    
    
    for path1, path2 in link_pairs:
            claims1 = pages_claims[path1]
            claims2 = pages_claims[path2]
            
            # 找相似但可能矛盾的声明对
            for c1 in claims1:
                for c2 in claims2:
                    sim = text_similarity(c1, c2)
                    if sim > threshold:
                        # 高相似度 = 讨论同一话题
                        # 但如果措辞不同，可能存在矛盾
                        if c1 != c2:
                            # 检测否定词（简化版）
                            negation_words = ['不', '非', '无', '未', '别', '反', '不是', '并非', '并非如此']
                            has_negation_1 = any(w in c1 for w in negation_words)
                            has_negation_2 = any(w in c2 for w in negation_words)
                            
                            # 一个有否定，一个没有 = 潜在矛盾
                            if has_negation_1 != has_negation_2:
                                contradictions.append({
                                    'type': 'negation_conflict',
                                    'page1': path1,
                                    'page2': path2,
                                    'claim1': c1[:100],
                                    'claim2': c2[:100],
                                    'similarity': round(sim, 3),
                                })
    
    return contradictions


def check_pair(wiki_root: str, page1: str, page2: str) -> dict:
    """检查两个页面之间的矛盾"""
    wiki_dir = os.path.join(wiki_root, 'wiki')
    
    path1 = os.path.join(wiki_dir, page1) if not os.path.isabs(page1) else page1
    path2 = os.path.join(wiki_dir, page2) if not os.path.isabs(page2) else page2
    
    try:
        with open(path1, 'r', encoding='utf-8') as f:
            claims1 = extract_claims(f.read())
        with open(path2, 'r', encoding='utf-8') as f:
            claims2 = extract_claims(f.read())
    except FileNotFoundError as e:
        return {'error': str(e)}
    
    # 比较所有声明对
    comparisons = []
    for c1 in claims1:
        for c2 in claims2:
            sim = text_similarity(c1, c2)
            if sim > 0.3:  # 只比较有相关性的
                comparisons.append({
                    'claim1': c1[:100],
                    'claim2': c2[:100],
                    'similarity': round(sim, 3),
                })
    
    return {
        'page1': page1,
        'page2': page2,
        'claims1': len(claims1),
        'claims2': len(claims2),
        'comparisons': sorted(comparisons, key=lambda x: x['similarity'], reverse=True)[:10],
    }


# ============ CLI ============

def main():
    parser = argparse.ArgumentParser(description='llm-wiki-v2 矛盾检测')
    sub = parser.add_subparsers(dest='command')
    
    # scan
    p_scan = sub.add_parser('scan', help='扫描知识库矛盾')
    p_scan.add_argument('wiki_root')
    p_scan.add_argument('--threshold', type=float, default=0.7)
    
    # check
    p_check = sub.add_parser('check', help='检查两个页面的矛盾')
    p_check.add_argument('wiki_root')
    p_check.add_argument('page1')
    p_check.add_argument('page2')
    
    args = parser.parse_args()
    
    if args.command == 'scan':
        contradictions = scan_contradictions(args.wiki_root, args.threshold)
        print(json.dumps({
            'threshold': args.threshold,
            'contradictions': contradictions,
            'total': len(contradictions),
        }, ensure_ascii=False, indent=2))
    
    elif args.command == 'check':
        result = check_pair(args.wiki_root, args.page1, args.page2)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
