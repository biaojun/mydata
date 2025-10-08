"""报告生成：根据聚合 CSV 生成 Markdown 概览。"""

from __future__ import annotations


import csv
import datetime as _dt
import os


def _read_csv_rows(path: str):
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def build_report_markdown(agg_dimension_csv: str, agg_keywords_csv: str, figs_dir: str, out_md_path: str) -> str:
    """根据聚合结果与图表渲染 report.md。

    当前实现：
    - 从 CSV 读取维度统计与关键词；
    - 输出基本概览与两张表格；
    - 图表留作占位，后续由 visualize 模块生成并插入。
    返回生成的 Markdown 路径。
    """
    dim_rows = _read_csv_rows(agg_dimension_csv)
    kw_rows = _read_csv_rows(agg_keywords_csv)

    ts = _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    os.makedirs(os.path.dirname(out_md_path) or ".", exist_ok=True)
    os.makedirs(figs_dir, exist_ok=True)

    def _fmt_dim_table(rows):
        header = (
            "| 维度 | 任务数 | 均值(均差) | 均值(中位差) | 均值(最小差) | 均值(最大差) | 均值(一致性) |\n"
            "|---|---:|---:|---:|---:|---:|---:|\n"
        )
        lines = [header]
        # 排序：按 mean_mean_delta 降序
        rows_sorted = sorted(rows, key=lambda r: float(r.get("mean_mean_delta", 0.0)), reverse=True)
        for r in rows_sorted:
            lines.append(
                f"| {r.get('dimension','')} | {r.get('tasks','0')} | {float(r.get('mean_mean_delta',0.0)):.3f} | "
                f"{float(r.get('mean_median_delta',0.0)):.3f} | {float(r.get('mean_min_delta',0.0)):.3f} | "
                f"{float(r.get('mean_max_delta',0.0)):.3f} | {float(r.get('mean_consistency',0.0)):.3f} |"
            )
        return "\n".join(lines)

    def _fmt_kw_table(rows, topn=50):
        header = "| 关键词 | 维度 | 权重和 | 任务计数 |\n|---|---|---:|---:|\n"
        lines = [header]
        for r in rows[:topn]:
            lines.append(
                f"| {r.get('phrase','')} | {r.get('dimension','')} | {float(r.get('weight_sum',0.0)):.3f} | {r.get('task_count','0')} |"
            )
        return "\n".join(lines)

    md = []
    md.append(f"# 1vN 代码质量分析报告\n\n生成时间：{ts}\n")
    md.append("## 维度差概览\n")
    md.append(_fmt_dim_table(dim_rows))
    md.append("\n\n")
    md.append("## 全局区分性关键词（Top-50）\n")
    md.append(_fmt_kw_table(kw_rows, topn=50))
    md.append("\n\n")
    # 插入全局图表（若存在）
    radar = os.path.join(figs_dir, "global_radar.png")
    heatmap = os.path.join(figs_dir, "global_heatmap.png")
    wc = os.path.join(figs_dir, "global_wordcloud.png")
    base_dir = os.path.dirname(out_md_path) or "."
    if os.path.exists(radar) or os.path.exists(heatmap) or os.path.exists(wc):
        md.append("## 全局图表\n")
    if os.path.exists(radar):
        rel = os.path.relpath(radar, base_dir)
        md.append(f"![global_radar]({rel})\n")
    if os.path.exists(heatmap):
        rel = os.path.relpath(heatmap, base_dir)
        md.append(f"![global_heatmap]({rel})\n")
    if os.path.exists(wc):
        rel = os.path.relpath(wc, base_dir)
        md.append(f"![global_wordcloud]({rel})\n")

    with open(out_md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    return out_md_path
