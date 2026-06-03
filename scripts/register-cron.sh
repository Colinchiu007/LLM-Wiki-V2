#!/usr/bin/env bash
# llm-wiki-v2: 注册 OpenClaw 定时任务
# 用法: register-cron.sh <wiki_root>
#
# 注册以下定时任务：
#   1. 每周日凌晨 2:00 — 知识巩固 + 自愈 lint
#   2. 每 30 分钟 — 检查 raw/ 目录新文件
#   3. 每天凌晨 3:00 — 矛盾检测

set -euo pipefail

WIKI_ROOT="${1:?Usage: register-cron.sh <wiki_root>}"

echo "📅 注册 llm-wiki-v2 定时任务"
echo "知识库路径: $WIKI_ROOT"
echo ""

# 1. 每周知识巩固 + 自愈 lint
echo "=== 1. 每周知识巩固 ==="
echo "建议手动注册（需要 openclaw cron 命令）："
echo "  openclaw cron add --schedule '0 2 * * 0' --task '对知识库执行巩固和自愈 lint'"
echo ""

# 2. raw/ 目录扫描
echo "=== 2. raw/ 目录定期扫描 ==="
echo "建议手动注册："
echo "  openclaw cron add --schedule '*/30 * * * *' --task '检查 raw/ 目录是否有新素材'"
echo ""

# 3. 每天矛盾检测
echo "=== 3. 每天矛盾检测 ==="
echo "建议手动注册："
echo "  openclaw cron add --schedule '0 3 * * *' --task '运行矛盾检测扫描'"
echo ""

echo "⚠️  以上命令需要在 OpenClaw CLI 中手动执行，因为 cron 任务需要用户确认。"
echo ""
echo "或者，将这些任务添加到 HEARTBEAT.md 中，由 agent 在心跳检查时轮询执行。"
