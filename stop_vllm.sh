#!/bin/bash
# 停止所有 vLLM 实例

echo "🛑 停止所有 vLLM 实例..."

# 查找所有 vLLM 进程
PIDS=$(ps aux | grep "vllm.entrypoints.openai.api_server" | grep -v grep | awk '{print $2}')

if [ -z "$PIDS" ]; then
    echo "没有找到运行中的 vLLM 实例"
    exit 0
fi

echo "找到以下 vLLM 进程:"
ps aux | grep "vllm.entrypoints.openai.api_server" | grep -v grep

echo ""
echo "正在停止进程..."
for PID in $PIDS; do
    echo "  终止进程 $PID"
    kill $PID
done

sleep 2

# 检查是否还有残留进程
REMAINING=$(ps aux | grep "vllm.entrypoints.openai.api_server" | grep -v grep | wc -l)
if [ $REMAINING -gt 0 ]; then
    echo "⚠️  仍有进程未停止，使用 kill -9 强制终止..."
    for PID in $(ps aux | grep "vllm.entrypoints.openai.api_server" | grep -v grep | awk '{print $2}'); do
        kill -9 $PID
    done
fi

echo "✅ 所有 vLLM 实例已停止"
