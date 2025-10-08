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

# 可选：中文字体路径（用于词云）
# export FONT_PATH="/System/Library/Fonts/PingFang.ttc"

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
