#!/usr/bin/env python3
"""
llm-wiki-v2: 隐私信息扫描与过滤

用法:
    python privacy_filter.py scan <content_file>
    python privacy_filter.py filter <content_file> [--output <output_file>]
    python privacy_filter.py scan-text "<text>"
"""

import os
import re
import sys
import json
import argparse

# ============ 敏感信息模式 ============

SENSITIVE_PATTERNS = [
    # API Keys
    (r'(sk-|pk-|pk_live_|pk_test_)[a-zA-Z0-9_\-]{20,}', 'API Key'),
    (r'AIzaSy[0-9A-Za-z_-]{33}', 'Google API Key'),
    (r'OPENAI_API_KEY\s*[=:]\s*["\']?[a-zA-Z0-9_\-]{20,}["\']?', 'OpenAI API Key'),
    (r'ANTHROPIC_API_KEY\s*[=:]\s*["\']?[a-zA-Z0-9_\-]{20,}["\']?', 'Anthropic API Key'),
    (r'ghp_[a-zA-Z0-9]{36}', 'GitHub Token'),
    (r'gho_[a-zA-Z0-9]{36}', 'GitHub OAuth Token'),
    
    # 密码
    (r'(?:password|passwd|pwd)\s*[=:]\s*["\']?[^\s"\'{}]{8,}["\']?', 'Password'),
    
    # 手机号（中国大陆）
    (r'1[3-9]\d{9}', 'Phone Number (CN)'),
    
    # 身份证号
    (r'[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx]', 'ID Card (CN)'),
    
    # 银行卡号
    (r'(?:62|4\d|5[1-5])\d{14,17}', 'Bank Card Number'),
    
    # 邮箱（可选，可能误报）
    # (r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', 'Email Address'),
    
    # JWT Token
    (r'eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+', 'JWT Token'),
    
    # AWS Key
    (r'AKIA[0-9A-Z]{16}', 'AWS Access Key'),
    
    # 私钥标记
    (r'-----BEGIN (?:RSA |EC )?PRIVATE KEY-----', 'Private Key'),
]


def scan_content(content: str) -> list:
    """
    扫描内容中的敏感信息
    返回 [{type, match, position, line, line_number}, ...]
    """
    findings = []
    lines = content.split('\n')
    
    for pattern, label in SENSITIVE_PATTERNS:
        for i, line in enumerate(lines, 1):
            for m in re.finditer(pattern, line):
                findings.append({
                    'type': label,
                    'match': m.group(),
                    'position': m.start(),
                    'line_number': i,
                    'line_preview': line[:80] + ('...' if len(line) > 80 else ''),
                })
    
    return findings


def filter_content(content: str) -> tuple:
    """
    过滤敏感信息（替换为 [REDACTED:TYPE]）
    返回 (filtered_content, findings)
    """
    findings = scan_content(content)
    filtered = content
    
    # 从后往前替换，避免偏移
    for pattern, label in SENSITIVE_PATTERNS:
        filtered = re.sub(pattern, f'[REDACTED:{label}]', filtered)
    
    return filtered, findings


# ============ CLI ============

def main():
    parser = argparse.ArgumentParser(description='llm-wiki-v2 隐私信息扫描与过滤')
    sub = parser.add_subparsers(dest='command')
    
    # scan
    p_scan = sub.add_parser('scan', help='扫描文件中的敏感信息')
    p_scan.add_argument('content_file')
    
    # scan-text
    p_text = sub.add_parser('scan-text', help='扫描文本中的敏感信息')
    p_text.add_argument('text')
    
    # filter
    p_filter = sub.add_parser('filter', help='过滤文件中的敏感信息')
    p_filter.add_argument('content_file')
    p_filter.add_argument('--output', help='输出文件路径（默认覆盖原文件）')
    
    args = parser.parse_args()
    
    if args.command == 'scan':
        with open(args.content_file, 'r', encoding='utf-8') as f:
            content = f.read()
        findings = scan_content(content)
        print(json.dumps({
            'file': args.content_file,
            'findings': findings,
            'total': len(findings),
            'has_sensitive': len(findings) > 0,
        }, ensure_ascii=False, indent=2))
    
    elif args.command == 'scan-text':
        findings = scan_content(args.text)
        print(json.dumps({
            'findings': findings,
            'total': len(findings),
            'has_sensitive': len(findings) > 0,
        }, ensure_ascii=False, indent=2))
    
    elif args.command == 'filter':
        with open(args.content_file, 'r', encoding='utf-8') as f:
            content = f.read()
        filtered, findings = filter_content(content)
        
        output_path = args.output or args.content_file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(filtered)
        
        print(json.dumps({
            'file': args.content_file,
            'output': output_path,
            'findings': findings,
            'total_redacted': len(findings),
        }, ensure_ascii=False, indent=2))
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
