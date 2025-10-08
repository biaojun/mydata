"""用于 1vN 代码质量对照评估的分析包脚手架。

本包包含以下模块的占位实现（待后续填充）：
- 模型与数据结构（schemas & types）
- Prompt 构造（prompt construction）
- 模型调用接口（model calling interface）
- 单任务编排（per-task orchestration）
- 跨任务聚合（cross-task aggregation）
- 可视化与报告生成（visualization & report generation）
- 简单的 CLI 入口（simple CLI entry points）

具体实现将于后续补充。
"""

# 版本信息
__version__ = "0.1.0"

# 数据结构和枚举
from .schemas import (
    Dimension,
    BadCode,
    TaskInput,
    ScoreDetail,
    DiscriminativeKeyword,
    PerBadComparison,
    DimensionAggStats,
    TaskLevelAggregation,
    ModelOutput,
    validate_task_input,
    to_json_compatible,
)

# IO 工具
from .io_utils import (
    read_tasks_jsonl,
    write_jsonl,
    ensure_dir,
)

# 数据适配器
from .adapters import (
    record_to_task_input,
    records_to_task_inputs,
)

# Prompt 构造
from .prompting import (
    build_1vN_prompt,
)

# LLM 调用接口
from .llm_runner import (
    call_model,
    parse_model_response,
    extract_json_block,
)

# 单任务分析
from .per_task import (
    analyze_task,
    analyze_tasks,
)

# 聚合分析
from .aggregate import (
    aggregate_dimension_stats,
    aggregate_keywords,
    export_aggregates,
)

# 可视化
from .visualize import (
    plot_task_dimension_lollipop,
    plot_task_keywords_bar,
    plot_task_wordcloud,
    plot_global_radar,
    plot_global_heatmaps,
    plot_global_wordcloud,
)

# 报告生成
from .report import (
    build_report_markdown,
)

# Pipeline（一键运行）
from .pipeline import (
    run_pipeline,
)

# 多 vLLM 实例支持
from .multi_vllm import (
    MultiVLLMClient,
    create_multi_vllm_client,
    get_vllm_urls_from_env,
)

__all__ = [
    # 版本
    "__version__",
    
    # 数据结构
    "Dimension",
    "BadCode",
    "TaskInput",
    "ScoreDetail",
    "DiscriminativeKeyword",
    "PerBadComparison",
    "DimensionAggStats",
    "TaskLevelAggregation",
    "ModelOutput",
    "validate_task_input",
    "to_json_compatible",
    
    # IO 工具
    "read_tasks_jsonl",
    "write_jsonl",
    "ensure_dir",
    
    # 数据适配器
    "record_to_task_input",
    "records_to_task_inputs",
    
    # Prompt 构造
    "build_1vN_prompt",
    
    # LLM 调用
    "call_model",
    "parse_model_response",
    "extract_json_block",
    
    # 单任务分析
    "analyze_task",
    "analyze_tasks",
    
    # 聚合分析
    "aggregate_dimension_stats",
    "aggregate_keywords",
    "export_aggregates",
    
    # 可视化
    "plot_task_dimension_lollipop",
    "plot_task_keywords_bar",
    "plot_task_wordcloud",
    "plot_global_radar",
    "plot_global_heatmaps",
    "plot_global_wordcloud",
    
    # 报告生成
    "build_report_markdown",
    
    # Pipeline
    "run_pipeline",
    
    # 多 vLLM 支持
    "MultiVLLMClient",
    "create_multi_vllm_client",
    "get_vllm_urls_from_env",
]
