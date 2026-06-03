#!/usr/bin/env python3
"""
llm-wiki-v2: 结构化实体提取与知识图谱操作

用法:
    python entities.py extract <content_file> [--output json]
    python entities.py graph-traverse <wiki_root> <entity_name> [--max-depth 2] [--relation-types uses,depends_on]
    python entities.py build-graph <wiki_root>
    python entities.py add-edge <wiki_root> --source <from> --target <to> --type <relation_type>
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path

# ============ 关系类型词汇表 ============

RELATION_TYPES = {
    'uses': {'direction': 'unidirectional', 'label': '使用'},
    'depends_on': {'direction': 'unidirectional', 'label': '依赖'},
    'causes': {'direction': 'unidirectional', 'label': '导致'},
    'contradicts': {'direction': 'bidirectional', 'label': '矛盾'},
    'supersedes': {'direction': 'unidirectional', 'label': '取代'},
    'related_to': {'direction': 'bidirectional', 'label': '相关'},
    'part_of': {'direction': 'unidirectional', 'label': '部分'},
    'implemented_by': {'direction': 'unidirectional', 'label': '实现'},
}


# ============ Wikilink 解析 ============

WIKILINK_RE = re.compile(r'\[\[([^\]]+)\]\]')


def extract_wikilinks(content: str) -> list:
    """提取 Markdown 中的 [[wikilinks]]，返回去重列表"""
    links = WIKILINK_RE.findall(content)
    # 处理别名 [[display|target]]
    targets = []
    for link in links:
        if '|' in link:
            targets.append(link.split('|')[1].strip())
        else:
            targets.append(link.strip())
    return list(dict.fromkeys(targets))  # 去重保序


# ============ 图谱数据读写 ============

def load_graph(wiki_root: str) -> dict:
    """加载 graph-data.json"""
    graph_path = os.path.join(wiki_root, 'wiki', 'graph-data.json')
    if os.path.exists(graph_path):
        with open(graph_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    # 初始化空图谱
    return {'nodes': [], 'edges': []}


def save_graph(wiki_root: str, graph: dict):
    """保存 graph-data.json"""
    graph_path = os.path.join(wiki_root, 'wiki', 'graph-data.json')
    with open(graph_path, 'w', encoding='utf-8') as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)


def find_node(graph: dict, name: str) -> dict | None:
    """按名称查找节点（模糊匹配）"""
    name_lower = name.lower()
    for node in graph.get('nodes', []):
        if node.get('name', '').lower() == name_lower:
            return node
        if name_lower in node.get('name', '').lower():
            return node
        # 也匹配 id（路径）
        if name_lower in node.get('id', '').lower():
            return node
    return None


def find_node_by_id(graph: dict, node_id: str) -> dict | None:
    """按 ID 精确查找节点"""
    for node in graph.get('nodes', []):
        if node.get('id') == node_id:
            return node
    return None


# ============ 图遍历 ============

def graph_traverse(graph: dict, start_name: str, 
                   relation_types: list = None, max_depth: int = 2) -> list:
    """
    从起始节点出发，沿指定关系类型遍历
    返回 [(source_id, edge, target_id), ...]
    """
    start = find_node(graph, start_name)
    if not start:
        return []
    
    if relation_types is None:
        relation_types = list(RELATION_TYPES.keys())
    
    results = []
    visited_nodes = set()
    
    def dfs(node_id, depth):
        if depth > max_depth or node_id in visited_nodes:
            return
        visited_nodes.add(node_id)
        
        for edge in graph.get('edges', []):
            source_id = edge.get('source', '')
            target_id = edge.get('target', '')
            edge_type = edge.get('type', 'related_to')
            
            if edge_type not in relation_types:
                continue
            
            # 出边
            if source_id == node_id:
                results.append({
                    'source': source_id,
                    'target': target_id,
                    'type': edge_type,
                    'weight': edge.get('weight', 1.0),
                    'depth': depth + 1,
                })
                dfs(target_id, depth + 1)
            
            # 反向边（对双向关系和反向遍历）
            elif target_id == node_id:
                results.append({
                    'source': target_id,
                    'target': source_id,
                    'type': edge_type,
                    'weight': edge.get('weight', 1.0),
                    'depth': depth + 1,
                    'reversed': True,
                })
                dfs(source_id, depth + 1)
    
    dfs(start.get('id', start_name), 0)
    return results


# ============ 图谱构建 ============

def build_graph_from_wiki(wiki_root: str) -> dict:
    """
    扫描 wiki/ 目录下所有 .md 文件的 [[wikilinks]]，
    构建知识图谱的 nodes 和 edges
    """
    wiki_dir = os.path.join(wiki_root, 'wiki')
    graph = {'nodes': [], 'edges': []}
    
    # 收集所有页面
    pages = {}  # name -> {id, path, type}
    for root, dirs, files in os.walk(wiki_dir):
        for fname in files:
            if not fname.endswith('.md'):
                continue
            fpath = os.path.join(root, fname)
            rel_path = os.path.relpath(fpath, wiki_dir)
            name = os.path.splitext(fname)[0]
            
            # 确定类型
            subpath = os.path.relpath(fpath, wiki_dir)
            page_type = 'unknown'
            if subpath.startswith('entities'):
                page_type = 'entity'
            elif subpath.startswith('topics'):
                page_type = 'topic'
            elif subpath.startswith('sources'):
                page_type = 'source'
            elif subpath.startswith('synthesis'):
                page_type = 'synthesis'
            
            pages[name.lower()] = {
                'id': rel_path.replace('\\', '/'),
                'name': name,
                'type': page_type,
                'path': fpath,
            }
    
    # 构建节点
    for name, info in pages.items():
        # 读取页面内容，提取 wikilinks
        try:
            with open(info['path'], 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            continue
        
        links = extract_wikilinks(content)
        
        graph['nodes'].append({
            'id': info['id'],
            'name': info['name'],
            'type': info['type'],
            'degree': len(links),
        })
        
        # 构建边
        for link in links:
            link_lower = link.lower()
            # 查找目标页面
            target = pages.get(link_lower)
            if target:
                graph['edges'].append({
                    'source': info['id'],
                    'target': target['id'],
                    'type': 'related_to',  # 默认类型，后续由 LLM 细化
                    'weight': 1.0,
                })
    
    # 去重边（同源同目标只保留一条）
    seen_edges = set()
    unique_edges = []
    for edge in graph['edges']:
        key = (edge['source'], edge['target'])
        if key not in seen_edges:
            seen_edges.add(key)
            unique_edges.append(edge)
    graph['edges'] = unique_edges
    
    return graph


def add_edge(wiki_root: str, source: str, target: str, 
             edge_type: str = 'related_to', weight: float = 1.0,
             confidence: str = 'EXTRACTED') -> dict:
    """添加一条边到图谱"""
    graph = load_graph(wiki_root)
    
    edge = {
        'source': source,
        'target': target,
        'type': edge_type,
        'weight': weight,
        'confidence': confidence,
    }
    
    # 检查是否已存在
    for existing in graph.get('edges', []):
        if (existing.get('source') == source and 
            existing.get('target') == target and
            existing.get('type') == edge_type):
            return {'status': 'exists', 'edge': existing}
    
    graph.setdefault('edges', []).append(edge)
    save_graph(wiki_root, graph)
    
    return {'status': 'added', 'edge': edge}


# ============ CLI ============

def main():
    parser = argparse.ArgumentParser(description='llm-wiki-v2 结构化实体与图谱操作')
    sub = parser.add_subparsers(dest='command')
    
    # extract
    p_extract = sub.add_parser('extract', help='提取页面中的实体和关系')
    p_extract.add_argument('content_file')
    p_extract.add_argument('--output', choices=['json', 'text'], default='json')
    
    # graph-traverse
    p_traverse = sub.add_parser('graph-traverse', help='图遍历查询')
    p_traverse.add_argument('wiki_root')
    p_traverse.add_argument('entity_name')
    p_traverse.add_argument('--max-depth', type=int, default=2)
    p_traverse.add_argument('--relation-types', default='uses,depends_on,causes,related_to')
    
    # build-graph
    p_build = sub.add_parser('build-graph', help='从 wiki 目录构建图谱')
    p_build.add_argument('wiki_root')
    
    # add-edge
    p_add = sub.add_parser('add-edge', help='添加边')
    p_add.add_argument('wiki_root')
    p_add.add_argument('--source', required=True)
    p_add.add_argument('--target', required=True)
    p_add.add_argument('--type', default='related_to')
    p_add.add_argument('--weight', type=float, default=1.0)
    
    args = parser.parse_args()
    
    if args.command == 'extract':
        with open(args.content_file, 'r', encoding='utf-8') as f:
            content = f.read()
        links = extract_wikilinks(content)
        result = {'wikilinks': links, 'count': len(links)}
        if args.output == 'json':
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            for link in links:
                print(f'- [[{link}]]')
    
    elif args.command == 'graph-traverse':
        graph = load_graph(args.wiki_root)
        relation_types = [t.strip() for t in args.relation_types.split(',')]
        results = graph_traverse(graph, args.entity_name, relation_types, args.max_depth)
        print(json.dumps({
            'entity': args.entity_name,
            'max_depth': args.max_depth,
            'results': results,
            'total': len(results),
        }, ensure_ascii=False, indent=2))
    
    elif args.command == 'build-graph':
        graph = build_graph_from_wiki(args.wiki_root)
        save_graph(args.wiki_root, graph)
        print(json.dumps({
            'status': 'built',
            'nodes': len(graph['nodes']),
            'edges': len(graph['edges']),
        }, ensure_ascii=False, indent=2))
    
    elif args.command == 'add-edge':
        result = add_edge(args.wiki_root, args.source, args.target, args.type, args.weight)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
