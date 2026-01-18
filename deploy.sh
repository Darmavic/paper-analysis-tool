#!/bin/bash
# 一键部署脚本 (AutoDL/Linux服务器)

set -e  # 遇到错误立即退出

echo "======================================"
echo "  学术论文分析工具 - 自动部署脚本"
echo "======================================"

# 1. 检测Python版本
echo ""
echo "📌 检查Python版本..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误：未找到Python3，请先安装Python 3.9+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✅ Python版本: $PYTHON_VERSION"

# 2. 创建虚拟环境
echo ""
echo "📦 创建虚拟环境..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "✅ 虚拟环境创建成功"
else
    echo "⚠️  虚拟环境已存在，跳过创建"
fi

# 3. 激活虚拟环境
echo ""
echo "🔓 激活虚拟环境..."
source .venv/bin/activate

# 4. 升级pip
echo ""
echo "⬆️  升级pip..."
pip install --upgrade pip

# 5. 安装依赖
echo ""
echo "📥 安装项目依赖（可能需要几分钟）..."
pip install -r scripts/requirements.txt

# 6. 检查GPU
echo ""
echo "🎮 检测GPU信息..."
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
    echo "✅ 检测到NVIDIA GPU"
else
    echo "⚠️  未检测到NVIDIA GPU，将使用CPU模式（速度较慢）"
fi

# 7. 创建.env文件（如果不存在）
echo ""
echo "🔐 配置环境变量..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✅ 已创建 .env 文件，请编辑该文件并填入您的API密钥"
    echo ""
    echo "⚠️  重要：请执行以下命令编辑 .env 文件："
    echo "    nano .env"
    echo "    或"
    echo "    vim .env"
else
    echo "✅ .env 文件已存在"
fi

# 8. 创建必要的目录
echo ""
echo "📁 创建输出目录..."
mkdir -p obsidian_vault
mkdir -p marker_temp_output
echo "✅ 目录创建完成"

# 9. 完成
echo ""
echo "======================================"
echo "  🎉 部署完成！"
echo "======================================"
echo ""
echo "📝 下一步操作："
echo "  1. 编辑 .env 文件，填入您的 OPENROUTER_API_KEY"
echo "  2. 上传PDF文件到服务器"
echo "  3. 运行分析命令："
echo ""
echo "     python scripts/analyze_paper.py --pdf your_paper.pdf --vault obsidian_vault"
echo ""
echo "💡 提示：如需提升处理速度，可编辑 scripts/analyze_paper.py"
echo "   调整 INFERENCE_RAM 和 VRAM_PER_TASK 参数"
echo ""
