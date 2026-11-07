#!/bin/sh
# 克隆仓库后运行一次，启用随仓库分发的提交前密钥扫描钩子
# 用法：sh scripts/setup-hooks.sh
git config core.hooksPath .githooks
echo "已启用提交前密钥扫描钩子（.githooks/pre-commit）"
echo "验证：git config --get core.hooksPath  应输出 .githooks"
