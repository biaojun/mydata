#!/bin/bash
# 检查 vLLM 实例状态

echo "📊 检查 vLLM 实例状态..."
echo "========================================"

# 检查进程
RUNNING=$(ps aux | grep "vllm.entrypoints.openai.api_server" | grep -v grep | wc -l)
echo "运行中的实例数: $RUNNING"
echo ""

if [ $RUNNING -gt 0 ]; then
    echo "进程详情:"
    ps aux | grep "vllm.entrypoints.openai.api_server" | grep -v grep
    echo ""
fi

# 检查端口
echo "端口监听状态:"
for PORT in 8001 8002 8003 8004; do
    if lsof -i :$PORT > /dev/null 2>&1; then
        echo "  ✓ 端口 $PORT: 监听中"
    else
        echo "  ✗ 端口 $PORT: 未监听"
    fi
done

echo ""
echo "========================================"

# 测试连接
echo ""
echo "测试 API 连接..."
for PORT in 8001 8002 8003 8004; do
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$PORT/v1/models --max-time 2)
    if [ "$RESPONSE" == "200" ]; then
        echo "  ✓ http://localhost:$PORT/v1 - 可访问"
    else
        echo "  ✗ http://localhost:$PORT/v1 - 不可访问 (HTTP $RESPONSE)"
    fi
done

echo ""
echo "日志文件:"
if [ -d "vllm_logs" ]; then
    ls -lh vllm_logs/
fi
