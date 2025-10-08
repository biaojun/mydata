#!/bin/bash
# 启动 4 个 vLLM 实例用于并发推理
# GPU 分配: 实例1(0,1), 实例2(2,3), 实例3(4,5), 实例4(6,7)

set -e

MODEL_PATH="/var/shared/models/Qwen3-30B-A3B-Instruct-2507"
LOG_DIR="./vllm_logs"

# 创建日志目录
mkdir -p ${LOG_DIR}

echo "🚀 启动 4 个 vLLM 实例..."
echo "========================================"

# 实例 1: GPU 0,1 - 端口 8001
echo "启动实例 1 (GPU 0,1, 端口 8001)..."
CUDA_VISIBLE_DEVICES=0,1 OMP_NUM_THREADS=1 \
nohup python -m vllm.entrypoints.openai.api_server \
  --model ${MODEL_PATH} \
  --tensor-parallel-size 2 \
  --dtype bfloat16 \
  --gpu-memory-utilization 0.96 \
  --max-model-len 8192 \
  --max-num-seqs 6 \
  --max-num-batched-tokens 32768 \
  --enable-chunked-prefill \
  --enable-prefix-caching \
  --scheduler-policy lpm \
  --port 8001 > ${LOG_DIR}/vllm_01.log 2>&1 &

sleep 2

# 实例 2: GPU 2,3 - 端口 8002
echo "启动实例 2 (GPU 2,3, 端口 8002)..."
CUDA_VISIBLE_DEVICES=2,3 OMP_NUM_THREADS=1 \
nohup python -m vllm.entrypoints.openai.api_server \
  --model ${MODEL_PATH} \
  --tensor-parallel-size 2 \
  --dtype bfloat16 \
  --gpu-memory-utilization 0.96 \
  --max-model-len 8192 \
  --max-num-seqs 6 \
  --max-num-batched-tokens 32768 \
  --enable-chunked-prefill \
  --enable-prefix-caching \
  --scheduler-policy lpm \
  --port 8002 > ${LOG_DIR}/vllm_23.log 2>&1 &

sleep 2

# 实例 3: GPU 4,5 - 端口 8003
echo "启动实例 3 (GPU 4,5, 端口 8003)..."
CUDA_VISIBLE_DEVICES=4,5 OMP_NUM_THREADS=1 \
nohup python -m vllm.entrypoints.openai.api_server \
  --model ${MODEL_PATH} \
  --tensor-parallel-size 2 \
  --dtype bfloat16 \
  --gpu-memory-utilization 0.96 \
  --max-model-len 8192 \
  --max-num-seqs 6 \
  --max-num-batched-tokens 32768 \
  --enable-chunked-prefill \
  --enable-prefix-caching \
  --scheduler-policy lpm \
  --port 8003 > ${LOG_DIR}/vllm_45.log 2>&1 &

sleep 2

# 实例 4: GPU 6,7 - 端口 8004
echo "启动实例 4 (GPU 6,7, 端口 8004)..."
CUDA_VISIBLE_DEVICES=6,7 OMP_NUM_THREADS=1 \
nohup python -m vllm.entrypoints.openai.api_server \
  --model ${MODEL_PATH} \
  --tensor-parallel-size 2 \
  --dtype bfloat16 \
  --gpu-memory-utilization 0.96 \
  --max-model-len 8192 \
  --max-num-seqs 6 \
  --max-num-batched-tokens 32768 \
  --enable-chunked-prefill \
  --enable-prefix-caching \
  --scheduler-policy lpm \
  --port 8004 > ${LOG_DIR}/vllm_67.log 2>&1 &

echo ""
echo "========================================"
echo "✅ 4 个 vLLM 实例已在后台启动"
echo "========================================"
echo ""
echo "实例信息:"
echo "  实例 1: GPU 0,1 → http://localhost:8001"
echo "  实例 2: GPU 2,3 → http://localhost:8002"
echo "  实例 3: GPU 4,5 → http://localhost:8003"
echo "  实例 4: GPU 6,7 → http://localhost:8004"
echo ""
echo "日志文件:"
echo "  ${LOG_DIR}/vllm_01.log"
echo "  ${LOG_DIR}/vllm_23.log"
echo "  ${LOG_DIR}/vllm_45.log"
echo "  ${LOG_DIR}/vllm_67.log"
echo ""
echo "查看进程: ps aux | grep vllm"
echo "停止所有实例: ./stop_vllm.sh"
echo "查看日志: tail -f ${LOG_DIR}/vllm_*.log"
echo ""
echo "⏳ 等待约 30-60 秒让所有实例完成初始化..."
