"""一键运行 1vN 代码质量分析的 Pipeline。

流程：
1) 读取 JSONL（每行含 task, good_code[list], bad_code[list]，可选 task_id/language）
2) 构造 1vN Prompt，调用 LLM（send_vllm）并解析输出 → per_task.jsonl
3) 聚合导出：agg_dimension.csv 与 agg_keywords.csv
4) 生成全局图表（雷达/热力图）并生成 report.md

使用：
  直接执行：python -m analyze.pipeline
  可用环境变量覆盖路径：
    INPUT_JSONL=data/tasks.jsonl OUTPUT_DIR=outputs python -m analyze.pipeline

注意：你需要在 analyze/llm_runner.py 中实现 send_vllm(prompt) 才能真正调用模型。
"""

from __future__ import annotations

import os
from typing import List

from .io_utils import read_tasks_jsonl, write_jsonl, ensure_dir
from .per_task import analyze_tasks
from .aggregate import export_aggregates
from .visualize import plot_global_radar, plot_global_heatmaps, plot_global_wordcloud
from .report import build_report_markdown


def run_pipeline(
    input_jsonl: str = "data/tasks.jsonl",
    output_dir: str = "outputs",
    client = None,
    show_progress: bool = True
) -> dict:
    """运行完整的 1vN 代码质量分析 Pipeline。
    
    Args:
        input_jsonl: 输入任务的 JSONL 文件路径
        output_dir: 输出目录
        client: OpenAI client 实例
        show_progress: 是否显示进度条
    
    Returns:
        包含各输出文件路径的字典
    """
    print("=" * 60)
    print("🚀 开始运行 1vN 代码质量分析 Pipeline")
    print("=" * 60)
    
    # 1) 读取任务
    print("\n📖 [步骤 1/6] 读取任务数据...")
    tasks = read_tasks_jsonl(input_jsonl)
    print(f"   ✓ 成功读取 {len(tasks)} 个任务")

    # 2) 调用 LLM 分析每任务
    print("\n🤖 [步骤 2/6] 调用 LLM 分析任务...")
    results = analyze_tasks(tasks, model=client, show_progress=show_progress)
    print(f"   ✓ 成功分析 {len(results)} 个任务")

    # 3) 写 per_task.jsonl
    print("\n💾 [步骤 3/6] 保存任务分析结果...")
    ensure_dir(output_dir)
    per_task_path = os.path.join(output_dir, "per_task.jsonl")
    write_jsonl(per_task_path, results)
    print(f"   ✓ 已保存到: {per_task_path}")

    # 4) 聚合导出 CSV
    print("\n📊 [步骤 4/6] 聚合统计数据...")
    dim_csv = os.path.join(output_dir, "agg_dimension.csv")
    kw_csv = os.path.join(output_dir, "agg_keywords.csv")
    export_aggregates(per_task_path, dim_csv, kw_csv)
    print(f"   ✓ 维度统计: {dim_csv}")
    print(f"   ✓ 关键词统计: {kw_csv}")

    # 5) 生成全局图表
    print("\n📈 [步骤 5/6] 生成可视化图表...")
    figs_dir = os.path.join(output_dir, "figs")
    ensure_dir(figs_dir)
    
    radar_path = os.path.join(figs_dir, "global_radar.png")
    plot_global_radar(dim_csv, radar_path)
    print(f"   ✓ 雷达图: {radar_path}")
    
    heatmap_path = plot_global_heatmaps(dim_csv, figs_dir)
    print(f"   ✓ 热力图: {heatmap_path}")
    
    # 读取 FONT_PATH 环境变量以支持中文字体
    font_path = os.environ.get("FONT_PATH")
    try:
        wordcloud_path = os.path.join(figs_dir, "global_wordcloud.png")
        plot_global_wordcloud(kw_csv, wordcloud_path, font_path=font_path)
        print(f"   ✓ 词云图: {wordcloud_path}")
    except Exception as e:
        print(f"   ⚠ 跳过词云生成: {e}")
        wordcloud_path = ""

    # 6) 生成报告
    print("\n📝 [步骤 6/6] 生成分析报告...")
    report_md = os.path.join(output_dir, "report.md")
    build_report_markdown(dim_csv, kw_csv, figs_dir, report_md)
    print(f"   ✓ 报告: {report_md}")

    print("\n" + "=" * 60)
    print("✅ Pipeline 执行完成！")
    print("=" * 60)

    return {
        "per_task": per_task_path,
        "agg_dimension": dim_csv,
        "agg_keywords": kw_csv,
        "radar": radar_path,
        "heatmap": heatmap_path,
        "report": report_md,
        "wordcloud": wordcloud_path,
    }


def main() -> int:
    input_jsonl = os.environ.get("INPUT_JSONL", "/home/liangjunbiao/data/processed_data.jsonl")
    output_dir = os.environ.get("OUTPUT_DIR", "outputs")
    from openai import OpenAI

    client = OpenAI(
        base_url="http://localhost:8000/v1",
        api_key="EMPTY"  # vLLM默认不验证
    )

    paths = run_pipeline(input_jsonl=input_jsonl, output_dir=output_dir, client=client)
    for k, v in paths.items():
        print(f"{k}: {v}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
