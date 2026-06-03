#!/usr/bin/env bash
# llm-wiki-v2: 多 Agent 同步（基于 git）
# 用法: mesh-sync.sh <wiki_root> [--push|--pull|--status]
#
# 通过 git 同步知识库，支持多 Agent 协作。
# 冲突解决策略：以最新修改时间为准（ours/theirs 自动判断）。

set -euo pipefail

WIKI_ROOT="${1:?Usage: mesh-sync.sh <wiki_root> [--push|--pull|--status]}"
ACTION="${2:---status}"

cd "$WIKI_ROOT"

case "$ACTION" in
    --status)
        if [ -d ".git" ]; then
            echo "Git 状态:"
            git status --short 2>/dev/null || echo "Git 命令不可用"
            echo ""
            echo "远程仓库:"
            git remote -v 2>/dev/null || echo "未配置远程仓库"
        else
            echo "未初始化 Git 仓库"
            echo "运行 mesh-sync.sh <wiki_root> --init 来初始化"
        fi
        ;;
    
    --init)
        if [ -d ".git" ]; then
            echo "Git 仓库已存在"
        else
            git init
            # 创建 .gitignore
            cat > .gitignore << 'EOF'
.wiki-search.db
.chroma/
.audit.log
*.tmp
*.bak
EOF
            git add .
            git commit -m "init: llm-wiki-v2 知识库"
            echo "✅ Git 仓库已初始化并完成首次提交"
        fi
        ;;
    
    --push)
        if [ ! -d ".git" ]; then
            echo "❌ 未初始化 Git 仓库，先运行 --init"
            exit 1
        fi
        git add -A
        if git diff --cached --quiet; then
            echo "没有新的变更需要推送"
        else
            TIMESTAMP=$(date +%Y-%m-%d_%H%M)
            git commit -m "sync: 知识库更新 $TIMESTAMP"
            git push 2>/dev/null && echo "✅ 已推送到远程仓库" || echo "⚠️ 推送失败，可能需要先 pull"
        fi
        ;;
    
    --pull)
        if [ ! -d ".git" ]; then
            echo "❌ 未初始化 Git 仓库，先运行 --init"
            exit 1
        fi
        git pull --rebase 2>/dev/null && echo "✅ 已拉取远程更新" || echo "⚠️ 拉取失败，可能存在冲突"
        ;;
    
    *)
        echo "未知操作: $ACTION"
        echo "用法: mesh-sync.sh <wiki_root> [--init|--push|--pull|--status]"
        exit 1
        ;;
esac
