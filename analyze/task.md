

# 项目方案：基于 LLM 的 1vN 代码质量对照评与范式挖掘

## 1) 任务背景

你有大量任务样本，每条样本包含：**prompt + good_code + 多个 bad_code**。希望借助 LLM 对**同一任务**下的**好代码与多个坏代码**进行**一次性（1vN）对照评估**，输出结构化结果，并在**跨任务聚合**后形成：

* **好代码范式（positive patterns）**
* **坏代码反模式（anti-patterns）**
* **区分性关键词词云与关键图表**
* **可执行的团队规范（actionable rules）**

## 2) 项目目标

1. 对每条任务执行**1vN 对照评**，输出统一 JSON（维度打分、差异、关键词、规则）。
2. 进行**任务级聚合**（对所有 bad 的比较结果做 mean/median/min/max/consistency）。
3. 做**跨任务全局聚合**，产出图表与“好/坏范式清单”。

---

## 3) 数据输入与输出 Schema

### 输入（每条任务）

```json
{
  "task_id": "T001",
  "language": "python",
  "prompt": "任务说明/输入输出/约束…",
  "good_code": "....",
  "bad_codes": [
    {"bad_id": "b1", "code": "..."},
    {"bad_id": "b2", "code": "..."}
  ]
}
```

### 直接 1vN 模型输出（每条任务的一次响应）

```json
{
  "task_id": "T001",
  "prompt_brief": "（模型对任务的一句话摘要）",
  "per_bad_comparisons": [
    {
      "bad_id": "b1",
      "dimension_scores": {
        "correctness": {"good": 5, "bad": 2, "delta": 3, "evidence": "…"},
        "robustness":  {"good": 4, "bad": 1, "delta": 3, "evidence": "…"},
        "readability": {"good": 5, "bad": 3, "delta": 2, "evidence": "…"},
        "maintainability": {"good": 4, "bad": 2, "delta": 2, "evidence": "…"},
        "complexity": {"good": 5, "bad": 4, "delta": 1, "evidence": "…"},
        "performance": {"good": 4, "bad": 3, "delta": 1, "evidence": "…"},
        "testing": {"good": 3, "bad": 1, "delta": 2, "evidence": "…"},
        "security_dependency": {"good": 4, "bad": 1, "delta": 3, "evidence": "…"},
        "style_consistency": {"good": 5, "bad": 2, "delta": 3, "evidence": "…"}
      },
      "discriminative_keywords": [
        {"phrase": "输入校验", "dimension": "robustness", "weight": 0.72},
        {"phrase": "try-except", "dimension": "robustness", "weight": 0.61}
      ],
      "positive_patterns": ["…短句…", "…"],
      "anti_patterns": ["…短句…", "…"],
      "actionable_rules_local": ["…短句…", "…"]
    }
  ],
  "task_level_agg": {
    "dimension_agg": {
      "correctness": {"mean_delta": 2.1, "median_delta": 2, "min_delta": 1, "max_delta": 3, "consistency": 0.67},
      "robustness":  {"mean_delta": 2.6, "median_delta": 3, "min_delta": 1, "max_delta": 4, "consistency": 0.83}
      // 其余维度同样结构
    },
    "top_positive_patterns": ["…按频次/投票保留…"],
    "top_anti_patterns": ["…"],
    "aggregated_keywords": [
      {"phrase": "类型注解", "weight": 1.84, "dimension": "readability"},
      {"phrase": "模块化",   "weight": 1.63, "dimension": "maintainability"}
    ],
    "task_actionable_rules": ["…合并去重后 5–10 条…"]
  }
}
```

> 说明：让模型**一次性**对每个 bad_i 形成 1v1 结论，**并在同一次回应里完成任务级聚合**（mean/median/min/max/consistency 与合并关键词/模式/规则），减少二次调用与上下文丢失。

---

## 4) 评价维度（固定 9 维，0–5 分）

* correctness / robustness / readability / maintainability / complexity / performance / testing / security_dependency / style_consistency
  **差异值**：`delta = good - bad`。当 `|delta| ≥ 2`，要求提供`evidence`。

---

## 5) 指标与聚合（1vN 的关键计算）

对每个维度 d，在同一任务内收集所有 bad 的 `delta_i(d)`：

* `mean_delta(d)`: 平均区分度
* `median_delta(d)`: 稳健区分度
* `min_delta(d)`: **硬负例边界**（最难的 bad）
* `max_delta(d)`: 容易对手
* `consistency(d)`: `#(delta_i(d) ≥ τ) / N`（如 τ=2）

**关键词权重（任务级）**：
从每个对比 `discriminative_keywords` 聚合：
`local_weight_i(phrase) = base_weight_i × norm(Σ_d max(0, delta_i(d)))`
任务级：`aggregated_weight(phrase) = Σ_i local_weight_i(phrase)`
全局（跨任务）：`global_weight(phrase) = Σ_tasks aggregated_weight(phrase)`

---

## 6) 详细 Prompt（一次性 1vN，对照评+聚合）＋ One-shot

### 中文 Prompt（直接可用）

> 你是一名资深代码质量分析师。
> 我将提供 **同一任务** 的：任务说明（prompt）、一份 good_code，以及多份 bad_code。
> 你的目标是：
>
> 1. 对 **good_code vs 每个 bad_code** 逐一比较，覆盖以下 9 个维度（0–5 分）：correctness、robustness、readability、maintainability、complexity、performance、testing、security_dependency、style_consistency。对每维给出（good、bad、delta、evidence）。当 |delta|≥2 必须给关键证据。
> 2. 针对每个 bad，抽取区分性的关键词（phrase、dimension、weight），并总结 2–5 条 positive_patterns（好代码体现的实践）与 2–5 条 anti_patterns（坏代码常见问题），给出 2–5 条可执行的局部规则（actionable_rules_local）。
> 3. **请在同一次输出中完成任务级聚合**：对 9 维计算 mean_delta、median_delta、min_delta、max_delta、consistency(阈值 τ=2)；合并关键词权重（按 delta 强度加权）；合并并去重 positive/anti patterns，输出最终的 task_actionable_rules（5–10 条）。
> 4. 仅输出严格符合下列 JSON Schema 的结构化结果，不要额外文本。
>
> **输入：**
>
> * `task_id`: <string>
> * `language`: <string>
> * `prompt`: <string>
> * `good_code`: <string>
> * `bad_codes`: [{"bad_id": <string>, "code": <string>}, ...]
>
> **输出 JSON Schema：**（同“模型输出”一节所示）

### One-shot（精简示例）

**输入（示意）**

* prompt: “实现阶乘函数，非法或负数抛异常…”
* good_code:（含类型检查、负数检查、for 2..n、docstring）
* bad_codes:

  * b1: 缺少负数检查，循环边界错误
  * b2: 命名差、无注释、未处理类型、深层嵌套

**期望输出要点（片段）**

* per_bad_comparisons[b1].dimension_scores.correctness.delta = 3，evidence: “好代码覆盖 n 自身与负数异常，坏代码少一轮乘法且未检查负数”
* task_level_agg.dimension_agg.correctness.mean_delta ≈ 2–3；robustness.consistency 高
* aggregated_keywords: “输入校验/类型注解/try-except/单一职责/魔法数字（负向）” 等
* task_actionable_rules: “所有外部输入强制类型与范围校验；函数职责单一且 ≤50 行；异常路径必须含日志与测试”等

---

## 7) 可视化与报告产出

### 任务级（per task）

* **维度棒棒糖/误差线图**：每维显示 min/median/mean/max
* **关键词 Top-K 条形图**（来自 `aggregated_keywords`）
* **小型词云**：任务级区分性词云
* **对手分布图**：显示各 bad 的综合 delta（便于识别“最强对手”bad）

### 全局（跨任务）

* **雷达图**：9 维 Good vs Bad 均值
* **条形图（排序）**：各维 `mean(mean_delta)` + 标注 `consistency`
* **热力图**：任务 × 维度 的 `mean_delta` 与 `min_delta`
* **三类词云**：好/坏/区分性（全局）
* **共现网络（两张）**：好代码关键短语网络 vs 坏代码关键短语网络
* **火山图**（维度/关键词）：x=全局区分度，y=出现率/一致性 → 右上角=硬范式

### 报告结构（Markdown→PDF）

1. 摘要与数据规模
2. 维度差概览（雷达/条形/热力）
3. 关键词与模式（词云/共现网络/火山图）
4. “好代码范式”与“坏代码反模式”（Top-10）
5. 团队可执行规则清单（10–12 条）
6. 典型案例（1–2 个任务的可视化与解读）
7. 限制与后续工作

---

## 8) 落地实现（快速框架）

**目录建议**

```
src/
  数据处理/（从prompt中区分task，good code和badcode）
  调用llm进行好坏代码分析并保存
  数据分析画图
data/
  tasks.jsonl            # 多条 1vN 任务
outputs/
  per_task.jsonl         # 每条任务的 1vN 模型输出（直接 Schema）
  agg_dimension.csv      # 跨任务维度统计
  agg_keywords.csv       # 全局关键词
  figs/                  # 所有图表
  report.md              # 报告
```

**流程**

1. 读取 `tasks.jsonl` → 对每条任务构造一次 1vN Prompt → 调 LLM → 写入 `per_task.jsonl`
2. 聚合脚本：

   * 解析 `per_task.jsonl` 的 `task_level_agg` 与 `per_bad_comparisons`
   * 计算跨任务指标与表格
   * 产出图表与词云

> 若上下文过长：对 `bad_codes` 做**分批 1vK**（K≈2），对同一任务的多次响应在本地再聚合一次（结果与单次 1vN 等效）。
