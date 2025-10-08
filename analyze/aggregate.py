"""跨任务聚合与导出。

职责包括：
- 解析 per_task 输出（JSONL）；
- 计算跨任务维度统计；
- 聚合关键词权重；
- 导出 CSV 结果。
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Tuple
import csv
import json
import os

from .schemas import Dimension
from .io_utils import ensure_dir


def _iter_jsonl(path: str):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def aggregate_dimension_stats(per_task: Iterable[dict]) -> List[dict]:
    """计算所有任务在各维度上的全局统计。

    输入为 per_task 的 JSON dict 序列；输出为每维一行的统计 dict：
    {dimension, tasks, avg_of_means, avg_of_medians, avg_of_mins, avg_of_maxes, avg_consistency,
     avg_good_score, avg_bad_score}
    """
    # 维度 -> 各项列表
    acc: Dict[str, Dict[str, List[float]]] = {
        d.value: {
            "mean_delta": [],
            "median_delta": [],
            "min_delta": [],
            "max_delta": [],
            "consistency": [],
            "good_scores": [],
            "bad_scores": [],
        }
        for d in Dimension
    }

    for item in per_task:
        per_bad = item.get("per_bad_comparisons") or []
        # 先为每个维度收集当前任务的 delta 列表
        per_dim_deltas: Dict[str, List[float]] = {d.value: [] for d in Dimension}
        for cmp in per_bad:
            dim_scores = (cmp.get("dimension_scores") or {})
            for d in Dimension:
                name = d.value
                detail = dim_scores.get(name)
                if not detail:
                    continue
                try:
                    delta_val = float(detail.get("delta", 0.0))
                    per_dim_deltas[name].append(delta_val)
                except Exception:
                    continue

        for name, deltas in per_dim_deltas.items():
            if not deltas:
                continue
            deltas_sorted = sorted(deltas)
            n = len(deltas_sorted)
            mean_delta = sum(deltas_sorted) / n
            if n % 2 == 1:
                median_delta = deltas_sorted[n // 2]
            else:
                median_delta = (deltas_sorted[n // 2 - 1] + deltas_sorted[n // 2]) / 2.0
            min_delta = deltas_sorted[0]
            max_delta = deltas_sorted[-1]
            consistency = sum(1 for v in deltas_sorted if abs(v) >= 2.0) / n

            acc[name]["mean_delta"].append(round(mean_delta, 6))
            acc[name]["median_delta"].append(round(median_delta, 6))
            acc[name]["min_delta"].append(round(min_delta, 6))
            acc[name]["max_delta"].append(round(max_delta, 6))
            acc[name]["consistency"].append(round(consistency, 6))

        # 额外：统计原始 good/bad 分数用于雷达图
        per_bad = item.get("per_bad_comparisons") or []
        for cmp in per_bad:
            dim_scores = (cmp.get("dimension_scores") or {})
            for d in Dimension:
                name = d.value
                detail = dim_scores.get(name)
                if not detail:
                    continue
                try:
                    good_val = detail.get("good")
                    bad_val = detail.get("bad")
                    if good_val is not None:
                        acc[name]["good_scores"].append(float(good_val))
                    if bad_val is not None:
                        acc[name]["bad_scores"].append(float(bad_val))
                except Exception:
                    continue

    rows: List[dict] = []
    for name, lists in acc.items():
        def _avg(xs: List[float]) -> float:
            return round(sum(xs) / len(xs), 6) if xs else 0.0

        rows.append(
            {
                "dimension": name,
                "tasks": max(
                    len(lists["mean_delta"]),
                    len(lists["median_delta"]),
                    len(lists["min_delta"]),
                    len(lists["max_delta"]),
                    len(lists["consistency"]),
                ),
                "avg_of_means": _avg(lists["mean_delta"]),
                "avg_of_medians": _avg(lists["median_delta"]),
                "avg_of_mins": _avg(lists["min_delta"]),
                "avg_of_maxes": _avg(lists["max_delta"]),
                "avg_consistency": _avg(lists["consistency"]),
                "avg_good_score": _avg(lists["good_scores"]),
                "avg_bad_score": _avg(lists["bad_scores"]),
            }
        )
    return rows


def aggregate_keywords(per_task: Iterable[dict]) -> List[dict]:
    """跨任务聚合关键词并计算权重。

    输出为每个 (phrase, dimension) 的一行：
    {phrase, dimension, weight_sum, task_count}
    """
    kw_weight: Dict[Tuple[str, str], float] = {}
    kw_tasks: Dict[Tuple[str, str], set] = {}

    for item in per_task:
        task_id = item.get("task_id", "")
        per_bad = item.get("per_bad_comparisons") or []
        for cmp in per_bad:
            kws = cmp.get("discriminative_keywords") or []
            for kw in kws:
                phrase = str(kw.get("phrase", "")).strip()
                dim = str(kw.get("dimension", ""))
                if hasattr(dim, "value"):
                    dim = str(dim.value)
                if not phrase:
                    continue
                try:
                    w = float(kw.get("weight", kw.get("weight_sum", 0.0)) or 0.0)
                except Exception:
                    continue
                key = (phrase, dim)
                kw_weight[key] = kw_weight.get(key, 0.0) + w
                kw_tasks.setdefault(key, set()).add(task_id)

    rows: List[dict] = []
    for (phrase, dim), wsum in kw_weight.items():
        rows.append(
            {
                "phrase": phrase,
                "dimension": dim,
                "weight_sum": round(wsum, 6),
                "task_count": len(kw_tasks.get((phrase, dim), set())),
            }
        )
    # 按权重降序
    rows.sort(key=lambda r: (-r["weight_sum"], r["phrase"]))
    return rows


def aggregate_patterns(per_task: Iterable[dict]) -> Tuple[List[dict], List[dict]]:
    """聚合正向与反向模式，并统计出现频次。"""

    items = list(per_task)

    def _collect_from_per_bad(key: str):
        counts: Dict[str, float] = {}
        tasks: Dict[str, set] = {}
        for item in items:
            task_id = item.get("task_id", "")
            per_bad = item.get("per_bad_comparisons") or []
            seen_in_task = set()
            for cmp in per_bad:
                patterns = cmp.get(key) or []
                for pat in patterns:
                    phrase = str(pat).strip()
                    if not phrase:
                        continue
                    counts[phrase] = counts.get(phrase, 0.0) + 1.0
                    seen_in_task.add(phrase)
            for phrase in seen_in_task:
                tasks.setdefault(phrase, set()).add(task_id)

        rows = []
        for phrase, cnt in counts.items():
            rows.append(
                {
                    "pattern": phrase,
                    "count": int(cnt),
                    "task_count": len(tasks.get(phrase, set())),
                }
            )
        rows.sort(key=lambda r: (-r["count"], r["pattern"]))
        return rows

    positives = _collect_from_per_bad("positive_patterns")
    antis = _collect_from_per_bad("anti_patterns")
    return positives, antis


def export_aggregates(per_task_path: str, out_dimension_csv: str, out_keywords_csv: str) -> Tuple[str, str, str, str]:
    """读取 per_task JSONL 并导出跨任务 CSV 聚合结果。

    返回写入的文件路径。
    """
    items = list(_iter_jsonl(per_task_path))

    dim_rows = aggregate_dimension_stats(items)
    kw_rows = aggregate_keywords(items)
    pos_rows, anti_rows = aggregate_patterns(items)

    ensure_dir(os.path.dirname(out_dimension_csv) or ".")
    ensure_dir(os.path.dirname(out_keywords_csv) or ".")
    pos_patterns_csv = os.path.join(os.path.dirname(out_dimension_csv) or ".", "agg_positive_patterns.csv")
    anti_patterns_csv = os.path.join(os.path.dirname(out_dimension_csv) or ".", "agg_anti_patterns.csv")

    with open(out_dimension_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "dimension",
                "tasks",
                "avg_of_means",
                "avg_of_medians",
                "avg_of_mins",
                "avg_of_maxes",
                "avg_consistency",
                "avg_good_score",
                "avg_bad_score",
            ],
        )
        writer.writeheader()
        writer.writerows(dim_rows)

    with open(out_keywords_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["phrase", "dimension", "weight_sum", "task_count"],
        )
        writer.writeheader()
        writer.writerows(kw_rows)

    with open(pos_patterns_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["pattern", "count", "task_count"],
        )
        writer.writeheader()
        writer.writerows(pos_rows)

    with open(anti_patterns_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["pattern", "count", "task_count"],
        )
        writer.writeheader()
        writer.writerows(anti_rows)

    return out_dimension_csv, out_keywords_csv, pos_patterns_csv, anti_patterns_csv
