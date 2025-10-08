#!/bin/bash
# Linux 服务器中文字体安装脚本

echo "========================================"
echo "🎨 安装中文字体（Linux 服务器）"
echo "========================================"

# 检测 Linux 发行版
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo "❌ 无法检测系统类型"
    exit 1
fi

echo "检测到系统: $OS"
echo ""

# 根据不同发行版安装字体
case $OS in
    ubuntu|debian)
        echo "📦 使用 apt 安装字体..."
        sudo apt update
        sudo apt install -y fonts-noto-cjk fonts-wqy-zenhei fonts-wqy-microhei
        ;;
    
    centos|rhel|fedora)
        echo "📦 使用 yum/dnf 安装字体..."
        if command -v dnf &> /dev/null; then
            sudo dnf install -y google-noto-sans-cjk-fonts wqy-zenhei-fonts
        else
            sudo yum install -y google-noto-sans-cjk-fonts wqy-zenhei-fonts
        fi
        ;;
    
    *)
        echo "⚠️  未识别的发行版，尝试手动下载..."
        install_manually=true
        ;;
esac

# 手动下载方式（适用于所有 Linux）
if [ "$install_manually" = true ]; then
    echo ""
    echo "📥 手动下载 Noto Sans CJK 字体..."
    
    FONT_DIR="$HOME/.local/share/fonts"
    mkdir -p "$FONT_DIR"
    cd "$FONT_DIR"
    
    # 下载 Noto Sans CJK SC（简体中文）
    FONT_URL="https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Regular.otf"
    
    if command -v wget &> /dev/null; then
        wget -O NotoSansCJKsc-Regular.otf "$FONT_URL"
    elif command -v curl &> /dev/null; then
        curl -L -o NotoSansCJKsc-Regular.otf "$FONT_URL"
    else
        echo "❌ 需要 wget 或 curl 来下载字体"
        exit 1
    fi
    
    # 刷新字体缓存
    if command -v fc-cache &> /dev/null; then
        fc-cache -fv
    fi
    
    echo "✓ 字体已下载到: $FONT_DIR"
fi

echo ""
echo "========================================"
echo "🔍 查找已安装的中文字体..."
echo "========================================"

# 查找字体文件
FONT_PATHS=(
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc"
    "/usr/share/fonts/google-noto-cjk/NotoSansCJK-Regular.ttc"
    "/usr/share/fonts/wqy-zenhei/wqy-zenhei.ttc"
    "$HOME/.local/share/fonts/NotoSansCJKsc-Regular.otf"
)

FOUND_FONT=""
for font in "${FONT_PATHS[@]}"; do
    if [ -f "$font" ]; then
        echo "✓ 找到字体: $font"
        if [ -z "$FOUND_FONT" ]; then
            FOUND_FONT="$font"
        fi
    fi
done

if [ -z "$FOUND_FONT" ]; then
    echo "❌ 未找到中文字体文件"
    echo ""
    echo "💡 手动搜索字体："
    echo "   find /usr/share/fonts -name '*CJK*' -o -name '*cjk*' -o -name '*zenhei*'"
    exit 1
fi

echo ""
echo "========================================"
echo "✅ 安装完成！"
echo "========================================"
echo ""
echo "推荐使用的字体: $FOUND_FONT"
echo ""
echo "使用方法 1: 在运行脚本时设置环境变量"
echo "  export FONT_PATH=\"$FOUND_FONT\""
echo "  ./run_multi_vllm.sh"
echo ""
echo "使用方法 2: 修改 run_multi_vllm.sh"
echo "  在脚本中添加："
echo "  export FONT_PATH=\"$FOUND_FONT\""
echo ""
echo "测试字体:"
echo "  python test_wordcloud.py"
echo ""
