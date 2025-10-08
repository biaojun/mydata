# 快速参考 - 多 vLLM 并发推理

## 🚀 一键启动（推荐）

```bash
# 1. 启动 4 个 vLLM 实例
./start_vllm.sh

# 2. 等待 30-60 秒，然后检查状态
./check_vllm.sh

# 3. 运行并发推理
./run_multi_vllm.sh

# 4. 完成后停止
./stop_vllm.sh
```

## 📋 文件说明

| 文件 | 用途 |
|------|------|
| `start_vllm.sh` | 启动 4 个 vLLM 实例 |
| `stop_vllm.sh` | 停止所有 vLLM 实例 |
| `check_vllm.sh` | 检查实例状态 |
| `run_multi_vllm.sh` | 运行并发推理 Pipeline |
| `analyze/multi_vllm.py` | 多实例客户端实现 |
| `MULTI_VLLM_GUIDE.md` | 详细使用指南 |

## ⚙️ 实例配置

| 实例 | GPU | 端口 | 日志文件 |
|------|-----|------|----------|
| 1 | 0,1 | 8001 | `vllm_logs/vllm_01.log` |
| 2 | 2,3 | 8002 | `vllm_logs/vllm_23.log` |
| 3 | 4,5 | 8003 | `vllm_logs/vllm_45.log` |
| 4 | 6,7 | 8004 | `vllm_logs/vllm_67.log` |

## 🔧 常用命令

```bash
# 查看运行中的实例
ps aux | grep vllm

# 查看端口监听
lsof -i :8001,:8002,:8003,:8004

# 监控 GPU
watch -n 1 nvidia-smi

# 查看日志
tail -f vllm_logs/vllm_*.log

# 单独启动一个实例（测试）
CUDA_VISIBLE_DEVICES=0,1 python -m vllm.entrypoints.openai.api_server \
  --model /var/shared/models/Qwen3-30B-A3B-Instruct-2507 \
  --tensor-parallel-size 2 \
  --port 8001
```

## 🎯 环境变量

```bash
# 启用多实例模式
export USE_MULTI_VLLM=true

# 配置端口
export VLLM_PORTS="8001,8002,8003,8004"

# 配置输入输出
export INPUT_JSONL="data/tasks.jsonl"
export OUTPUT_DIR="outputs"

# 运行
python -m analyze.pipeline
```

## 📊 性能提升

- 单实例: ~1x 吞吐量
- 四实例: ~4x 吞吐量 ⭐

## ⚠️ 注意事项

1. 确保有足够的 GPU 显存（每个实例需要 ~24GB）
2. 启动后等待模型加载完成（30-60秒）
3. 使用完毕后记得停止实例释放资源
4. 监控日志文件排查问题

## 🐛 故障排查

```bash
# 端口被占用
lsof -i :8001 | grep LISTEN
kill -9 <PID>

# 查看错误日志
tail -100 vllm_logs/vllm_01.log

# 重启所有实例
./stop_vllm.sh && ./start_vllm.sh

# 测试单个实例
curl http://localhost:8001/v1/models
```

## 📖 完整文档

详见 `MULTI_VLLM_GUIDE.md`
