#!/bin/bash
# setup.sh — 一键安装脚本依赖（使用虚拟环境）
# 用法: bash setup.sh

set -e

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║    B站自动点赞脚本 — 环境初始化           ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# 检查 Python 版本（需要 3.8+）
PYTHON=$(command -v python3 || command -v python)
if [ -z "$PYTHON" ]; then
    echo "❌ 未找到 Python，请先安装 Python 3.8+"
    exit 1
fi

PY_VER=$($PYTHON -c "import sys; print(sys.version_info.major * 10 + sys.version_info.minor)")
if [ "$PY_VER" -lt 38 ]; then
    echo "❌ Python 版本过低，需要 3.8+，当前: $($PYTHON --version)"
    exit 1
fi

echo "✅ Python 版本: $($PYTHON --version)"

# 创建虚拟环境（解决 Homebrew Python 的 externally-managed 限制）
VENV_DIR=".venv"
if [ ! -d "$VENV_DIR" ]; then
    echo ""
    echo "🔧 创建虚拟环境 ($VENV_DIR)..."
    $PYTHON -m venv "$VENV_DIR"
fi

# 激活虚拟环境
source "$VENV_DIR/bin/activate"
echo "✅ 虚拟环境已激活"

# 安装 pip 依赖
echo ""
echo "📦 安装 Python 依赖..."
pip install --upgrade pip -q
pip install -r requirements.txt

# 安装 Playwright Chromium 浏览器（只装 Chromium，体积最小）
echo ""
echo "🌐 安装 Playwright Chromium 浏览器..."
playwright install chromium

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║  ✅ 安装完成！运行脚本请执行：             ║"
echo "║     source .venv/bin/activate             ║"
echo "║     python main.py                        ║"
echo "╚══════════════════════════════════════════╝"
echo ""
