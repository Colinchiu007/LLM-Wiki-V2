#!/usr/bin/env bash
# llm-wiki-v2: 自动 ingest 守护进程
# 用法: auto-ingest-daemon.py <wiki_root>
#
# 使用 watchdog 监听 raw/ 目录，新文件进入时自动触发 ingest。
# Windows 下作为后台进程运行。

set -euo pipefail

echo "llm-wiki-v2 自动 ingest 守护进程"
echo "用法: 在 OpenClaw 中配置 cron 任务定期扫描 raw/ 目录"
echo ""
echo "示例 cron 配置："
echo "  openclaw cron add --schedule '*/30 * * * *' --task '检查 raw/ 目录是否有新素材'"
echo ""
echo "由于 OpenClaw 运行在沙箱中，推荐使用 cron 而非 daemon 模式。"
echo "cron 任务会检查 raw/ 目录的新文件，然后调用 ingest 工作流。"
