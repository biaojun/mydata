"""用于单次调用的 1vN 分析 Prompt 构造。

本模块提供与 task.md 规范一致的构造器：
- 一次响应同时产出 1vN 对照与任务级聚合结果；
- 在 Prompt 中内置中文说明模板。
"""

from __future__ import annotations

from typing import List

from .schemas import TaskInput, BadCode


def _format_bad_codes(bads: List[BadCode]) -> str:
    parts = []
    for b in bads:
        parts.append(f"{{\n  \"bad_id\": \"{b.bad_id}\",\n  \"code\": \"" + str(b.code).replace("\\", "\\\\").replace("\"", "\\\"") + "\"\n}}")
    return "[\n" + ",\n".join(parts) + "\n]"


def build_1vN_prompt(task: TaskInput) -> str:
    """构造单次调用的 1vN Prompt 字符串。

    说明：将任务说明和数据序列化为近似 JSON 文本嵌入，以提示模型输出结构化结果。
    当前实现保持简洁，格式化细节可后续再优化。
    """
    bads = _format_bad_codes(task.bad_codes)
    # 对 JSON 片段做最小转义，避免引号与反斜杠冲突
    prompt_text = task.prompt.replace("\\", "\\\\").replace("\"", "\\\"")
    good_text = task.good_code.replace("\\", "\\\\").replace("\"", "\\\"")

    instruction = f"""
你是一名资深代码质量分析师。
我将提供 同一任务 的：任务说明（prompt）、一份 good_code，以及多份 bad_code。
你的目标是：

1. 对 good_code vs 每个 bad_code 逐一比较，覆盖以下 9 个维度（0–5 分）：correctness、robustness、readability、maintainability、complexity、performance、testing、security_dependency、style_consistency。对每维给出（good、bad、delta、evidence）。当 |delta|≥2 必须给关键证据。
2. 针对每个 bad，抽取区分性的关键词（phrase、dimension、weight），并总结 2–5 条 positive_patterns 与 2–5 条 anti_patterns，给出 2–5 条 actionable_rules_local。
3. 不要做任何任务级聚合统计；仅返回逐个 bad 的详细比较结果，让后续程序自行汇总。
4. 仅输出严格符合 JSON Schema 的结构化结果，不要额外文本。

输入：
{{
  "task_id": "{task.task_id}",
  "prompt": "{prompt_text}",
  "good_code": "{good_text}",
  "bad_codes": {bads}
}}

输出 JSON Schema：请与如下字段对齐：
{{
  "task_id": "...",
  "prompt_brief": "...",
  "per_bad_comparisons": [
    {{
      "bad_id": "...",
      "dimension_scores": {{
        "correctness": {{"good": 0-5, "bad": 0-5, "delta": -5..5, "evidence": "?"}},
        "robustness":  {{"good": 0-5, "bad": 0-5, "delta": -5..5, "evidence": "?"}},
        "readability": {{"good": 0-5, "bad": 0-5, "delta": -5..5, "evidence": "?"}},
        "maintainability": {{"good": 0-5, "bad": 0-5, "delta": -5..5, "evidence": "?"}},
        "complexity": {{"good": 0-5, "bad": 0-5, "delta": -5..5, "evidence": "?"}},
        "performance": {{"good": 0-5, "bad": 0-5, "delta": -5..5, "evidence": "?"}},
        "testing": {{"good": 0-5, "bad": 0-5, "delta": -5..5, "evidence": "?"}},
        "security_dependency": {{"good": 0-5, "bad": 0-5, "delta": -5..5, "evidence": "?"}},
        "style_consistency": {{"good": 0-5, "bad": 0-5, "delta": -5..5, "evidence": "?"}}
      }},
      "discriminative_keywords": [{{"phrase": "...", "dimension": "...", "weight": 0.0}}],
      "positive_patterns": ["..."],
      "anti_patterns": ["..."],
      "actionable_rules_local": ["..."]
    }}
  ],
  "task_level_agg": null  // 保持字段占位即可，后续程序会忽略
}}
"""
    return instruction.strip()
