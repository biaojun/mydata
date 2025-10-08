#!/bin/bash
# 安装可视化所需的依赖包

echo "🔧 安装可视化依赖..."
echo "========================================"

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 Python3"
    exit 1
fi

echo "Python 版本:"
python3 --version
echo ""

# 安装依赖
echo "📦 安装 matplotlib（图表绘制）..."
pip install matplotlib

echo ""
echo "📦 安装 wordcloud（词云生成）..."
pip install wordcloud pillow

echo ""
echo "📦 安装 tqdm（进度条）..."
pip install tqdm

echo ""
echo "✅ 所有依赖安装完成！"
echo ""
echo "现在可以运行:"
echo "  ./run_multi_vllm.sh"
