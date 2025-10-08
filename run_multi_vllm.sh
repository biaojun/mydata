#!/bin/bash
# 使用多 vLLM 实例运行 Pipeline（真正并发模式）

# 配置环境变量
export USE_MULTI_VLLM=true        # 启用多实例
export USE_CONCURRENT=true        # 启用真正的并发处理 ⭐
export VLLM_PORTS="8001,8002,8003,8004"
export VLLM_HOST="localhost"
export MAX_WORKERS=4              # 并发线程数（建议=实例数）

# 输入输出配置
export INPUT_JSONL="${INPUT_JSONL:-data/tasks.jsonl}"
export OUTPUT_DIR="${OUTPUT_DIR:-outputs}"

# 自动检测中文字体（用于词云）
if [ -z "$FONT_PATH" ]; then
    # Linux 常见字体路径
    FONT_CANDIDATES=(
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc"
        "/usr/share/fonts/google-noto-cjk/NotoSansCJK-Regular.ttc"
        "/usr/share/fonts/wqy-zenhei/wqy-zenhei.ttc"
        "$HOME/.local/share/fonts/NotoSansCJKsc-Regular.otf"
        # macOS 路径（兼容）
        "/System/Library/Fonts/PingFang.ttc"
        "/System/Library/Fonts/STHeiti Light.ttc"
    )
    
    for font in "${FONT_CANDIDATES[@]}"; do
        if [ -f "$font" ]; then
            export FONT_PATH="$font"
            break
        fi
    done
fi

echo "========================================"
echo "🚀 运行多 vLLM 并发推理 Pipeline"
echo "========================================"
echo "配置信息:"
echo "  vLLM 实例数: 4"
echo "  端口: $VLLM_PORTS"
echo "  并发模式: ✅ 真正并发（线程池）"
echo "  并发线程数: $MAX_WORKERS"
echo "  输入文件: $INPUT_JSONL"
echo "  输出目录: $OUTPUT_DIR"
if [ -n "$FONT_PATH" ]; then
    echo "  中文字体: $FONT_PATH"
else
    echo "  中文字体: ⚠️  未找到（词云将使用英文）"
fi
echo "========================================"
echo ""
echo "💡 性能模式说明:"
echo "  - 真正并发: 同时向 4 个 vLLM 实例发送请求（最快）"
echo "  - 串行模式: 一次一个任务，轮流使用实例（慢）"
echo ""

# 运行 Pipeline
python -m analyze.pipeline

echo ""
echo "✅ Pipeline 执行完成！"
