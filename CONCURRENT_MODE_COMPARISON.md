# 并发模式对比说明

## 📊 两种并发模式对比

### 模式 1: 串行轮询（伪并发）❌

```bash
export USE_MULTI_VLLM=true
export USE_CONCURRENT=false   # 关闭真正并发
```

**工作原理:**
```
时间轴 →
实例1: [任务1========] [任务5========] [任务9========]
实例2:           [任务2========] [任务6========]
实例3:                      [任务3========] [任务7========]
实例4:                                 [任务4========]

一次只处理1个任务，虽然轮流使用4个实例，但大部分时间3个实例闲置！
```

**代码流程:**
```python
for task in tasks:  # 串行循环
    client = multi_vllm.get_next_client()  # 轮询选择
    result = client.call(task)  # 等待响应
    # 在等待时，其他3个实例闲置 ❌
```

**性能:** ~1.2x 速度提升（略快于单实例）

---

### 模式 2: 真正并发（推荐）✅

```bash
export USE_MULTI_VLLM=true
export USE_CONCURRENT=true    # 启用真正并发 ⭐
export MAX_WORKERS=4          # 4个线程
```

**工作原理:**
```
时间轴 →
实例1: [任务1===][任务5===][任务9===][任务13==]
实例2: [任务2===][任务6===][任务10==][任务14==]
实例3: [任务3===][任务7===][任务11==][任务15==]
实例4: [任务4===][任务8===][任务12==][任务16==]

同时处理4个任务，充分利用所有实例！
```

**代码流程:**
```python
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(process, task) for task in tasks]
    # 4个线程同时工作
    # 实例1、2、3、4 同时处理不同任务 ✅
```

**性能:** ~4x 速度提升（接近理论最大值）

---

## 🎯 性能对比（100个任务示例）

| 模式 | 实例数 | 并发方式 | 预计耗时 | 吞吐量 |
|------|--------|----------|----------|--------|
| 单实例串行 | 1 | 无 | 100分钟 | 1x |
| 多实例轮询 | 4 | 伪并发 | ~80分钟 | 1.2x |
| 多实例并发 | 4 | 真并发 | ~25分钟 | 4x ⭐ |

*假设单任务处理时间 1分钟*

---

## 🔧 如何选择？

### 使用串行轮询（USE_CONCURRENT=false）适合：
- ❌ **不推荐** - 性能提升有限

### 使用真正并发（USE_CONCURRENT=true）适合：
- ✅ **强烈推荐** - 大规模批处理任务
- ✅ 有多个 vLLM 实例（2个或以上）
- ✅ 想要最大化 GPU 利用率
- ✅ 追求最快处理速度

---

## 💻 使用示例

### 快速启动（真正并发）
```bash
./run_multi_vllm.sh
```

### 手动配置
```bash
# 真正并发模式（推荐）
export USE_MULTI_VLLM=true
export USE_CONCURRENT=true
export MAX_WORKERS=4
export VLLM_PORTS="8001,8002,8003,8004"
python -m analyze.pipeline
```

```bash
# 串行轮询模式（不推荐）
export USE_MULTI_VLLM=true
export USE_CONCURRENT=false  # 关闭并发
export VLLM_PORTS="8001,8002,8003,8004"
python -m analyze.pipeline
```

---

## 📈 运行时输出对比

### 串行模式输出：
```
🚀 启用多 vLLM 实例并发模式
   使用 4 个 vLLM 实例: 端口 [8001, 8002, 8003, 8004]
   轮询模式: 串行处理（轮流使用实例）

🤖 [步骤 2/6] 调用 LLM 分析任务...
分析任务 [串行]:  25%|█████     | 25/100 [20:00<60:00]
```

### 并发模式输出：
```
🚀 启用多 vLLM 实例并发模式
   使用 4 个 vLLM 实例: 端口 [8001, 8002, 8003, 8004]
   真正并发模式: 4 个线程同时处理

🤖 [步骤 2/6] 调用 LLM 分析任务...
   使用并发模式（4 个线程）
开始并发分析 100 个任务（并发数: 4）...
分析任务 [并发]:  25%|█████     | 25/100 [05:00<15:00, 成功=24, 失败=1]
                                     ↑ 快4倍！
```

---

## ⚙️ 调优建议

### 1. 并发线程数 = vLLM 实例数
```bash
# 4个实例 → 4个线程（最佳）
export MAX_WORKERS=4
export VLLM_PORTS="8001,8002,8003,8004"
```

### 2. 不要设置过大的 MAX_WORKERS
```bash
# ❌ 不好：10个线程但只有4个实例
export MAX_WORKERS=10  # 浪费，多余的线程会等待

# ✅ 好：4个线程匹配4个实例
export MAX_WORKERS=4
```

### 3. 监控资源使用
```bash
# 监控 GPU
watch -n 1 nvidia-smi

# 监控网络连接
watch -n 1 "netstat -an | grep '800[1-4]'"
```

---

## 🔍 技术细节

### ThreadPoolExecutor 工作原理

```python
# 创建线程池
with ThreadPoolExecutor(max_workers=4) as executor:
    # 提交100个任务
    futures = {executor.submit(analyze_task, t): t for t in tasks}
    
    # 线程池自动管理:
    # - 维护4个工作线程
    # - 每个线程从队列取任务
    # - 完成后取下一个任务
    # - 直到所有任务完成
    
    # 同一时刻最多4个任务在处理
    for future in as_completed(futures):
        result = future.result()
```

### MultiVLLMClient 负载均衡

```python
class MultiVLLMClient:
    def get_next_client(self):
        # 线程安全的轮询
        with self.lock:
            client = self.clients[self.index]
            self.index = (self.index + 1) % len(self.clients)
            return client

# 4个线程同时调用时:
# 线程1 → 实例1 (index=0)
# 线程2 → 实例2 (index=1)
# 线程3 → 实例3 (index=2)
# 线程4 → 实例4 (index=3)
# 线程1 → 实例1 (index=0, 循环)
```

---

## 📝 总结

| 特性 | 串行轮询 | 真正并发 |
|------|----------|----------|
| 性能提升 | ~1.2x | ~4x ⭐ |
| GPU利用率 | 低 (~25%) | 高 (~100%) |
| 实现复杂度 | 简单 | 中等 |
| 线程安全 | 天然安全 | 需要处理 ✅已实现 |
| 推荐度 | ⭐ | ⭐⭐⭐⭐⭐ |

**结论**: 使用多 vLLM 实例时，**务必启用 USE_CONCURRENT=true** 以获得最佳性能！
