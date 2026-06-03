#!/usr/bin/env python3
"""
llm-wiki-v2: 混合搜索引擎

用法:
    python search.py index-bm25 <wiki_root>
    python search.py bm25-search <wiki_root> "<query>" [--top-k 20]
    python search.py vector-search <wiki_root> "<query>" [--top-k 20]
    python search.py graph-search <wiki_root> "<entity>" [--max-depth 2]
    python search.py fuse --bm25-results <file> [--vector-results <file>] [--graph-results <file>] [--top-k 10]
"""

import os
import re
import sys
import json
import math
import argparse
import sqlite3
from pathlib import Path
from datetime import date

# ============ 中文分词 ============

_jieba_initialized = False

def _ensure_jieba():
    global _jieba_initialized
    if _jieba_initialized:
        return
    try:
        import jieba
        jieba.setLogLevel(20)  # WARNING only
        _jieba_initialized = True
    except ImportError:
        pass


def tokenize(text: str) -> str:
    """
    对文本做中英文混合分词，返回空格分隔的 token 字符串。
    中文用 jieba 分词，英文保持原样。
    """
    _ensure_jieba()
    
    # 去除 Markdown 标记符号，避免它们被当作 token
    text = re.sub(r'[#*`>\[\]|{}~\-]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    try:
        import jieba
        tokens = list(jieba.cut_for_search(text))
    except ImportError:
        # 无 jieba 时直接按空格分
        tokens = text.split()
    
    return ' '.join(tokens)


# ============ BM25 搜索 (SQLite FTS5 + jieba) ============

def init_bm25_db(wiki_root: str):
    """初始化 BM25 搜索数据库"""
    db_path = os.path.join(wiki_root, '.wiki-search.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS pages (
            path TEXT PRIMARY KEY,
            title TEXT,
            content TEXT,
            title_tokenized TEXT,
            content_tokenized TEXT,
            tags TEXT
        )
    ''')
    
    # 删除旧的 FTS5 表（如果格式不对）
    for table_name in ['pages_fts']:
        try:
            c.execute(f'DROP TABLE IF EXISTS {table_name}')
        except sqlite3.OperationalError:
            pass
    
    # 创建 FTS5 虚拟表（用简单分词，因为我们自己做 jieba 分词后写入）
    try:
        c.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS pages_fts USING fts5(
                path,
                title_tokenized,
                content_tokenized,
                tags,
                tokenize='porter unicode61'
            )
        ''')
    except sqlite3.OperationalError as e:
        print(json.dumps({
            'warning': f'FTS5 not available: {e}, falling back to LIKE search',
            'db_path': db_path,
        }, ensure_ascii=False))
    
    conn.commit()
    return conn


def index_bm25(wiki_root: str):
    """构建 BM25 索引（jieba 分词后写入 FTS5）"""
    conn = init_bm25_db(wiki_root)
    c = conn.cursor()
    
    # 清空旧索引
    c.execute('DELETE FROM pages')
    try:
        c.execute('DELETE FROM pages_fts')
    except sqlite3.OperationalError:
        pass
    
    wiki_dir = os.path.join(wiki_root, 'wiki')
    indexed = 0
    
    for root, dirs, files in os.walk(wiki_dir):
        for fname in files:
            if not fname.endswith('.md'):
                continue
            fpath = os.path.join(root, fname)
            rel_path = os.path.relpath(fpath, wiki_root).replace('\\', '/')
            
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception:
                continue
            
            # 提取标题
            title = fname.replace('.md', '')
            for line in content.split('\n'):
                if line.startswith('# '):
                    title = line[2:].strip()
                    break
            
            # 去除 frontmatter
            body = re.sub(r'^---\n.*?\n---', '', content, flags=re.DOTALL).strip()
            
            # jieba 分词
            title_tokens = tokenize(title)
            content_tokens = tokenize(body)
            
            # 提取标签
            tags = ' '.join(re.findall(r'#(\w+)', body))
            
            c.execute('''INSERT OR REPLACE INTO pages 
                         (path, title, content, title_tokenized, content_tokenized, tags) 
                         VALUES (?, ?, ?, ?, ?, ?)''',
                      (rel_path, title, body, title_tokens, content_tokens, tags))
            
            try:
                c.execute('''INSERT INTO pages_fts 
                             (path, title_tokenized, content_tokenized, tags) 
                             VALUES (?, ?, ?, ?)''',
                          (rel_path, title_tokens, content_tokens, tags))
            except sqlite3.OperationalError:
                pass
            
            indexed += 1
    
    conn.commit()
    conn.close()
    
    print(json.dumps({
        'status': 'indexed',
        'pages': indexed,
        'tokenizer': 'jieba',
        'db_path': os.path.join(wiki_root, '.wiki-search.db'),
    }, ensure_ascii=False, indent=2))


def bm25_search(wiki_root: str, query: str, top_k: int = 20) -> list:
    """BM25 搜索（jieba 分词后查询 FTS5）"""
    db_path = os.path.join(wiki_root, '.wiki-search.db')
    
    if not os.path.exists(db_path):
        index_bm25(wiki_root)
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    results = []
    
    # 对查询做分词
    query_tokens = tokenize(query)
    
    # 构建 FTS5 安全的 MATCH 表达式
    # FTS5 不支持某些字符，需要转义；多词用 OR 连接
    safe_tokens = []
    for t in query_tokens.split():
        # 去除 FTS5 特殊字符
        t = re.sub(r'["*:^+-]', '', t)
        if t:
            safe_tokens.append(f'"{t}"')  # 用引号包裹每个 token
    
    if not safe_tokens:
        conn.close()
        return results
    
    # 用 OR 连接（宽松匹配），FTS5 会自动按 BM25 排序
    fts_query = ' OR '.join(safe_tokens)
    
    # 尝试 FTS5 搜索
    try:
        c.execute('''
            SELECT p.path, p.title, f.rank
            FROM pages_fts f
            JOIN pages p ON f.path = p.path
            WHERE pages_fts MATCH ?
            ORDER BY f.rank
            LIMIT ?
        ''', (fts_query, top_k))
        for row in c.fetchall():
            results.append({
                'path': row[0],
                'title': row[1],
                'score': round(-row[2], 4) if row[2] else 0,
                'source': 'bm25',
            })
    except sqlite3.OperationalError as fts_err:
        # FTS5 查询失败，回退到 LIKE
        pass
    if not results:
        terms = query.split()
        like_clauses = ' AND '.join(['content LIKE ?' for _ in terms])
        params = [f'%{t}%' for t in terms]
        
        c.execute(f'''
            SELECT path, title
            FROM pages
            WHERE {like_clauses}
            LIMIT ?
        ''', params + [top_k])
        
        for row in c.fetchall():
            results.append({
                'path': row[0],
                'title': row[1],
                'score': 1.0,
                'source': 'like',
            })
    
    conn.close()
    return results


# ============ RRF 融合 ============

def reciprocal_rank_fusion(result_sets: list, k: int = 60, top_k: int = 10) -> list:
    """
    Reciprocal Rank Fusion: 融合多路搜索结果
    
    score(doc) = sum(1 / (k + rank_i) for each result set i)
    """
    scores = {}
    
    for results in result_sets:
        for rank, item in enumerate(results, 1):
            doc_id = item.get('path', item.get('id', ''))
            if not doc_id:
                continue
            
            rrf_score = 1.0 / (k + rank)
            
            if doc_id not in scores:
                scores[doc_id] = {
                    'path': doc_id,
                    'score': 0,
                    'sources': [],
                    'title': item.get('title', item.get('name', '')),
                }
            
            scores[doc_id]['score'] += rrf_score
            scores[doc_id]['sources'].append({
                'engine': item.get('source', 'unknown'),
                'rank': rank,
            })
    
    ranked = sorted(scores.values(), key=lambda x: x['score'], reverse=True)
    return ranked[:top_k]


# ============ CLI ============

def main():
    parser = argparse.ArgumentParser(description='llm-wiki-v2 混合搜索')
    sub = parser.add_subparsers(dest='command')
    
    # index-bm25
    p_idx = sub.add_parser('index-bm25', help='构建 BM25 索引')
    p_idx.add_argument('wiki_root')
    
    # bm25-search
    p_bm25 = sub.add_parser('bm25-search', help='BM25 搜索')
    p_bm25.add_argument('wiki_root')
    p_bm25.add_argument('query')
    p_bm25.add_argument('--top-k', type=int, default=20)
    
    # fuse
    p_fuse = sub.add_parser('fuse', help='RRF 融合')
    p_fuse.add_argument('--bm25-results', help='BM25 结果 JSON 文件')
    p_fuse.add_argument('--vector-results', help='Vector 结果 JSON 文件')
    p_fuse.add_argument('--graph-results', help='Graph 结果 JSON 文件')
    p_fuse.add_argument('--top-k', type=int, default=10)
    
    # graph-search
    p_graph = sub.add_parser('graph-search', help='图遍历搜索')
    p_graph.add_argument('wiki_root')
    p_graph.add_argument('entity')
    p_graph.add_argument('--max-depth', type=int, default=2)
    p_graph.add_argument('--relation-types', default='uses,depends_on,causes,related_to')
    
    args = parser.parse_args()
    
    if args.command == 'index-bm25':
        index_bm25(args.wiki_root)
    
    elif args.command == 'bm25-search':
        results = bm25_search(args.wiki_root, args.query, args.top_k)
        print(json.dumps({
            'query': args.query,
            'results': results,
            'total': len(results),
        }, ensure_ascii=False, indent=2))
    
    elif args.command == 'fuse':
        result_sets = []
        
        if args.bm25_results and os.path.exists(args.bm25_results):
            with open(args.bm25_results, 'r', encoding='utf-8') as f:
                data = json.load(f)
                result_sets.append(data.get('results', data if isinstance(data, list) else []))
        
        if args.vector_results and os.path.exists(args.vector_results):
            with open(args.vector_results, 'r', encoding='utf-8') as f:
                data = json.load(f)
                result_sets.append(data.get('results', data if isinstance(data, list) else []))
        
        if args.graph_results and os.path.exists(args.graph_results):
            with open(args.graph_results, 'r', encoding='utf-8') as f:
                data = json.load(f)
                result_sets.append(data.get('results', data if isinstance(data, list) else []))
        
        fused = reciprocal_rank_fusion(result_sets, top_k=args.top_k)
        print(json.dumps({
            'total_result_sets': len(result_sets),
            'fused_results': fused,
            'total': len(fused),
        }, ensure_ascii=False, indent=2))
    
    elif args.command == 'graph-search':
        from entities import load_graph, graph_traverse
        graph = load_graph(args.wiki_root)
        relation_types = [t.strip() for t in args.relation_types.split(',')]
        results = graph_traverse(graph, args.entity, relation_types, args.max_depth)
        print(json.dumps({
            'entity': args.entity,
            'results': results,
            'total': len(results),
        }, ensure_ascii=False, indent=2))
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
