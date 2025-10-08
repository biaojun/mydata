# 多 vLLM 实例并发推理指南

本指南介绍如何使用 4 个 vLLM 实例进行并发推理，充分利用 8 张 GPU（0-7）。

## 架构说明

```
GPU 分配:
├── vLLM 实例 1 (端口 8001): GPU 0, 1
├── vLLM 实例 2 (端口 8002): GPU 2, 3
├── vLLM 实例 3 (端口 8003): GPU 4, 5
└── vLLM 实例 4 (端口 8004): GPU 6, 7

任务分发:
Pipeline → MultiVLLMClient → 轮询分发到 4 个实例
           (负载均衡)
```

## 快速开始

### 步骤 1: 启动 4 个 vLLM 实例

```bash
cd /Users/orangezhi/Desktop/mydata
chmod +x start_vllm.sh stop_vllm.sh check_vllm.sh run_multi_vllm.sh
./start_vllm.sh
```

等待约 30-60 秒让所有实例完成模型加载。

### 步骤 2: 检查实例状态

```bash
./check_vllm.sh
```

应该看到所有 4 个端口都在监听，且 API 可访问。

### 步骤 3: 运行并发推理

```bash
./run_multi_vllm.sh
```

或手动设置环境变量：

```bash
export USE_MULTI_VLLM=true
export VLLM_PORTS="8001,8002,8003,8004"
export INPUT_JSONL="data/tasks.jsonl"
export OUTPUT_DIR="outputs"

python -m analyze.pipeline
```

### 步骤 4: 查看日志

```bash
# 查看所有实例日志
tail -f vllm_logs/vllm_*.log

# 查看单个实例日志
tail -f vllm_logs/vllm_01.log
```

### 步骤 5: 停止实例

```bash
./stop_vllm.sh
```

## 工作原理

### 1. 多实例客户端 (`MultiVLLMClient`)

`analyze/multi_vllm.py` 实现了一个智能客户端：

- **轮询负载均衡**: 任务轮流分配到 4 个实例
- **兼容接口**: 与 `OpenAI` client 接口一致
- **线程安全**: 使用锁保护并发访问

### 2. 并发推理流程

```python
# 100 个任务并发处理示例
任务  1 → vLLM 实例 1 (8001)  ┐
任务  2 → vLLM 实例 2 (8002)  │ 并发
任务  3 → vLLM 实例 3 (8003)  │ 处理
任务  4 → vLLM 实例 4 (8004)  ┘
任务  5 → vLLM 实例 1 (8001)  ← 轮询
任务  6 → vLLM 实例 2 (8002)
...
```

### 3. 进度显示

运行时会看到：

```
============================================================
🚀 开始运行 1vN 代码质量分析 Pipeline
============================================================
🚀 启用多 vLLM 实例并发模式
   使用 4 个 vLLM 实例: 端口 [8001, 8002, 8003, 8004]

📖 [步骤 1/6] 读取任务数据...
   ✓ 成功读取 100 个任务

🤖 [步骤 2/6] 调用 LLM 分析任务...
分析任务:  25%|██████        | 25/100 [01:15<03:45, 成功=24, 失败=1]
```

## 性能优化建议

### 1. 调整并发数

默认情况下，任务是顺序处理的（一个接一个）。虽然 4 个 vLLM 实例在后台并发，但前端仍是串行。

如果想要更高吞吐量，可以修改 `per_task.py` 使用真正的并发：

```python
from concurrent.futures import ThreadPoolExecutor

def analyze_tasks_concurrent(tasks, model, max_workers=4):
    """使用线程池并发分析任务。"""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(
            lambda t: analyze_task(t, model),
            tasks
        ))
    return [r for r in results if r is not None]
```

### 2. 调整 vLLM 参数

根据您的需求调整 `start_vllm.sh` 中的参数：

- `--max-num-seqs`: 单实例并发请求数（当前 6）
- `--gpu-memory-utilization`: GPU 显存利用率（当前 0.96）
- `--max-model-len`: 最大序列长度（当前 8192）

### 3. 监控 GPU 使用

```bash
# 实时监控 GPU
watch -n 1 nvidia-smi

# 查看特定 GPU
nvidia-smi -i 0,1,2,3,4,5,6,7
```

## 环境变量参考

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `USE_MULTI_VLLM` | `true` | 是否启用多实例模式 |
| `VLLM_PORTS` | `8001,8002,8003,8004` | vLLM 实例端口列表 |
| `VLLM_HOST` | `localhost` | vLLM 实例主机地址 |
| `INPUT_JSONL` | `data/tasks.jsonl` | 输入任务文件 |
| `OUTPUT_DIR` | `outputs` | 输出目录 |
| `FONT_PATH` | - | 中文字体路径（词云） |

## 故障排查

### 问题 1: 端口被占用

```bash
# 查看端口占用
lsof -i :8001
lsof -i :8002
lsof -i :8003
lsof -i :8004

# 杀死占用进程
kill -9 <PID>
```

### 问题 2: GPU 内存不足

```bash
# 查看 GPU 显存
nvidia-smi

# 如果显存不足，减少实例数量或降低 gpu-memory-utilization
# 编辑 start_vllm.sh，将 0.96 改为 0.90
```

### 问题 3: 实例无响应

```bash
# 查看日志
tail -100 vllm_logs/vllm_01.log

# 重启所有实例
./stop_vllm.sh
./start_vllm.sh
```

### 问题 4: 连接超时

检查防火墙设置，确保端口 8001-8004 可访问。

## 代码示例

### 在 Python 中使用

```python
from analyze import create_multi_vllm_client, run_pipeline

# 创建多实例客户端
client = create_multi_vllm_client(
    ports=[8001, 8002, 8003, 8004],
    host="localhost"
)

# 运行 Pipeline
paths = run_pipeline(
    input_jsonl="data/tasks.jsonl",
    output_dir="outputs",
    client=client
)

print(f"结果: {paths}")
```

### 单独使用 MultiVLLMClient

```python
from analyze import MultiVLLMClient

# 初始化
client = MultiVLLMClient([
    "http://localhost:8001/v1",
    "http://localhost:8002/v1",
    "http://localhost:8003/v1",
    "http://localhost:8004/v1",
])

# 调用（自动负载均衡）
response = client.chat.completions.create(
    model="/var/shared/models/Qwen3-30B-A3B-Instruct-2507",
    messages=[{"role": "user", "content": "Hello!"}],
    temperature=0.7
)

print(response.choices[0].message.content)
```

## 性能对比

| 模式 | 实例数 | GPU 数 | 理论吞吐量 | 推荐场景 |
|------|--------|--------|------------|----------|
| 单实例 | 1 | 2 | 1x | 小规模任务 |
| 双实例 | 2 | 4 | ~2x | 中等规模 |
| 四实例 | 4 | 8 | ~4x | 大规模批处理 ⭐ |

实际吞吐量取决于：
- 模型推理速度
- 网络延迟
- 任务复杂度
- GPU 性能

## 最佳实践

1. ✅ **启动前检查**: 确保所有 GPU 可用且显存充足
2. ✅ **逐步测试**: 先启动 1 个实例测试，再扩展到 4 个
3. ✅ **监控资源**: 运行时监控 GPU 和内存使用
4. ✅ **定期清理**: 完成后及时停止实例释放资源
5. ✅ **保存日志**: 保留日志文件用于调试和性能分析

## 进阶：真正的并发处理

如果想要同时向 4 个实例发送请求（而不是轮询），可以使用线程池：

```python
from concurrent.futures import ThreadPoolExecutor
from analyze import analyze_task

def analyze_tasks_parallel(tasks, model, max_workers=4):
    """真正并发地分析任务。"""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(analyze_task, task, model): task
            for task in tasks
        }
        
        results = []
        for future in as_completed(futures):
            result = future.result()
            if result is not None:
                results.append(result)
        
        return results
```

这样可以同时处理 4 个任务，充分利用 4 个 vLLM 实例的并发能力！
