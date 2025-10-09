# 代码质量判别训练数据清洗方案

> 目标：从 (prompt, good_code, bad_codes[]) 原始集合中构建高质量判别训练集，使模型能够“给定任务与一段代码，判别其好/坏及维度差异”。

---
## 总览流程（执行顺序）
1. Schema / 结构完整性校验
2. 代码标准化（格式化、换行、编码）
3. 去重与近重复消除（文本 + AST + 相似度）
4. 质量特征抽取（静态度量 + 结构特征）
5. 差距筛选（过滤伪负例）
6. 噪声与异常（语法 / 安全 / 运行）剔除
7. Prompt 净化（去泄漏、裁剪噪声）
8. 任务与长度分布均衡
9. 争议样本再标注（不确定性挖掘）
10. Hard Negative 合成（定向缺陷注入）
11. 防数据泄漏拆分（train/val/test）
12. 特征与标签打包导出

---
## 1. Schema / 结构校验
输入应满足：
```json
{
  "task_id": "T001",
  "language": "python",
  "prompt": "...",
  "good_code": "...",
  "bad_codes": [ {"bad_id": "b1", "code": "..."}, ... ]
}
```
规则：
- task_id / prompt / good_code 不为空；bad_codes 为列表，可为空但需存在字段。
- 语言过滤（仅保留目标语言，如 python）。
- 代码字段长度限制（避免超大样本）：“5 ≤ LOC ≤ P95(LOC)”

---
## 2. 代码标准化
- 统一换行 `\n`，去除 BOM。
- Python: 使用 black + isort；其他语言使用对应格式化器。
- 移除尾随空白、折叠多余空行（>2 连续空行裁成 1）。
- 可记录格式化 diff 长度，异常大（>30%）可标记人工复核。

---
## 3. 去重与近重复
### 3.1 精确去重
- good 与 bad 各自建 MD5 集合；重复的后到样本丢弃。

### 3.2 结构去重（AST Hash）
Python 例：
```python
def ast_struct_hash(code: str) -> str:
    import ast, hashlib
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return ""
    for node in ast.walk(tree):
        for attr in ("lineno","col_offset","end_lineno","end_col_offset"):
            if hasattr(node, attr):
                setattr(node, attr, None)
    raw = ast.dump(tree, annotate_fields=False, include_attributes=False)
    return hashlib.md5(raw.encode()).hexdigest()
```

### 3.3 近重复过滤
- Token Jaccard / SimHash / MinHash；阈值示例：相似度 > 0.9 → 保留权重更高（差距更大、更多注释、复杂度中等）的一份。

---
## 4. 质量特征抽取
为后续“差距计算 / 模型辅助特征”准备：
- LOC、平均行长、注释行数与注释率
- 函数数量 / 最大函数长度 / 最大嵌套深度
- 圈复杂度（e.g. radon）
- import 模块数 / 潜在危险调用（eval/exec、subprocess）
- 异常处理块个数（try-except）
- 测试迹象（assert / pytest / unittest 关键字）
- 安全指标（弱加密 / 硬编码凭据正则）

---
## 5. 差距筛选（去伪负例）
对每个 bad 计算 9 维 delta：Δ_d = good_d - bad_d。
过滤规则示例：
- 若所有维度 |Δ_d| < 1 且 平均 |Δ_d| < 0.5 → 判定非典型坏例（噪声），丢弃此 bad。
- 若 bad 与 good 完全一致（文本/AST）→ 丢弃。

保留统计：记录 Δ 分布用于抽样均衡。

---
## 6. 噪声与异常剔除
- 语法错误：bad 若语法报错，可保留（真实劣质）；good 若语法报错 → 任务整体标记“需人工复核”。
- 安全扫描（bandit / semgrep）：good 出现高危（exec 动态拼接、硬编码密钥）→ 复核或剔除。
- 可选轻量运行：设超时 2s + 沙箱；good 运行致命错误（非输入错误）→ 标记复核。

---
## 7. Prompt 净化
- 去除直接贴出参考答案 / 代码片段的内容（避免信息泄漏）。
- 删除景观性无关描述、噪声日志。
- 控制长度：>95 分位数截断尾部冗余（保留问题、约束、接口说明）。
- 统一结构：问题描述 / 输入 / 输出 / 约束 / 期望特性。

---
## 8. 分布均衡
- 任务层面：按任务类别（若可识别，如“数据处理/网络/算法”）分层抽样。
- 代码长度分桶：短（<30 LOC）/ 中（30–150）/ 长（>150），防止模型过拟合短代码特征。
- 差距分桶：|Δ| 大（≥2）、中（1–2）、小（<1）按比例采样（如 4:3:1）。

---
## 9. 争议样本再标注
使用一个初步判别器或多模型集成：
- 计算每对 (good,bad) 的维度概率分布 / 置信度；
- 选 entropy 高或模型分歧大的样本 → 人工二次标注；
- 形成高质量“困难样本”子集。

---
## 10. Hard Negative 合成
策略：从 good 克隆后注入一个明确缺陷：
- 删除输入校验 / 异常处理
- 引入魔法数字 / 变量命名混乱
- 降低时间/空间效率（O(n) → O(n^2)）
- 去掉测试断言/类型注解
- 打乱结构（长函数、重复代码块）

标注：`defect_tags`（列举1~3个缺陷），并记录注入脚本 ID 以便回溯。

---
## 11. 防数据泄漏拆分
- 按 task_id + AST hash 分组，不跨集合。
- 如果存在 Hard Negative，确保其原始 good 仅出现在训练或验证，不进入测试。
- 规则示例：train 80% / val 10% / test 10%。

---
## 12. 导出最终训练集格式
```json
{
  "task_id": "T123",
  "prompt": "...",
  "good": {
    "code": "...",
    "metrics": {"loc":120, "complexity":8, "comment_ratio":0.18}
  },
  "bads": [
    {
      "bad_id": "T123_b1",
      "code": "...",
      "diff_metrics": {"Δ_correctness": -3, "Δ_robustness": -2},
      "defect_tags": ["缺少异常处理","魔法数字"]
    }
  ]
}
```

---
## 13. 采样与训练策略
- 分桶采样（差距/长度/类别）
- 适度加入“反常样本”（bad 得分部分高于 good）增强泛化
- 多任务学习：主任务=二分类（好/坏），辅任务=九维差分回归/多标签缺陷分类

---
## 14. 监控指标
| 类别 | 指标 | 说明 |
|------|------|------|
| 判别 | Accuracy / F1 | 基本分类性能 |
| 维度 | MAE / R2 | 维度差回归质量 |
| 置信 | ECE / Brier | 概率校准 |
| 鲁棒 | 对抗通过率 | 对合成缺陷的检测成功率 |
| 数据 | 差距分布稳定性 | 监控训练集 vs 新数据漂移 |

---
## 15. 阈值建议（起始，可调优）
| 项 | 默认 | 目的 |
|----|------|------|
| 近重复相似度 | 0.9 | 去掉高度近似代码 |
| 伪负例过滤：平均|Δ| | 0.5 | 保证坏例“真的差” |
| 单维显著差 | 1 | 起码一个维度有明显差距 |
| 大差距阈值 τ | 2 | 计算一致性/稳定度 |
| LOC 下限 | 5 | 去除噪声/碎片 |
| LOC 上限 | P95 | 控制长尾 |

---
## 16. 自动化 Pipeline 草图
```text
load -> schema_check -> format -> deduplicate -> struct_hash -> near_dup_filter \
      -> static_metrics -> delta_scores -> filter_pseudo -> prompt_clean -> stratify \
      -> hard_negative_gen -> split_sets -> export(jsonl)
```

---
## 17. 后续可扩展
- 语义相似度聚类（embedding）进一步去重 / 合并标签
- 缺陷模式挖掘：通过聚类 bad 的 AST 变换路径
- 引入运行时覆盖指标（结合 lightweight instrumentation）
- 增量数据质量评分（Data QA Score）看新样本是否低质

---
## 术语补充
- Δ (delta)：good_score - bad_score
- 一致性(consistency)：|Δ|≥2 的比例，衡量“差距稳定性”
- 伪负例：与 good 几乎无差别的 bad，训练时会干扰判别边界

---
## 快速核对清单
- [ ] 样本结构合法 & 编码统一
- [ ] 语法/安全扫描通过（good）
- [ ] 去除重复与高相似
- [ ] 坏例差距显著（非伪负）
- [ ] 补充 Hard Negatives
- [ ] Stratified 拆分无泄漏
- [ ] 导出含 metrics 与 diff_metrics
- [ ] 指标基线跑通

