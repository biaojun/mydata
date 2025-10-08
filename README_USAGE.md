# Analyze Package 使用指南

1vN 代码质量分析工具包

## 项目结构

```
mydata/
├── analyze/              # 主包
│   ├── __init__.py      # 包导出配置
│   ├── schemas.py       # 数据结构定义
│   ├── io_utils.py      # IO 工具
│   ├── adapters.py      # 数据适配器
│   ├── prompting.py     # Prompt 构造
│   ├── llm_runner.py    # LLM 调用接口
│   ├── per_task.py      # 单任务分析
│   ├── aggregate.py     # 聚合分析
│   ├── visualize.py     # 可视化
│   ├── report.py        # 报告生成
│   └── pipeline.py      # 一键运行 Pipeline
├── run_pipeline.py      # 运行脚本
├── test_analyze.py      # 测试脚本
└── README_USAGE.md      # 本文档
```

## 安装依赖

```bash
pip install openai matplotlib pandas wordcloud
```

## 使用方式

### ❌ 错误的运行方式

```bash
# 不要这样做！会报错：attempted relative import with no known parent
cd analyze
python pipeline.py  # ❌ 错误
```

### ✅ 正确的运行方式

#### 方式 1: 使用 `-m` 作为模块运行（推荐）

```bash
# 在项目根目录
cd /Users/orangezhi/Desktop/mydata

# 运行 pipeline
python -m analyze.pipeline

# 或使用环境变量
INPUT_JSONL=data/tasks.jsonl OUTPUT_DIR=outputs python -m analyze.pipeline
```

#### 方式 2: 使用提供的运行脚本

```bash
# 在项目根目录
cd /Users/orangezhi/Desktop/mydata

# 运行 pipeline
python run_pipeline.py

# 运行测试
python test_analyze.py
```

#### 方式 3: 在 Python 代码中导入使用

```python
# your_script.py（位于项目根目录或 PYTHONPATH 中）
from analyze import run_pipeline
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="EMPTY"
)

paths = run_pipeline(
    input_jsonl="data/tasks.jsonl",
    output_dir="outputs",
    client=client
)

print(f"结果保存在: {paths}")
```

## 为什么会出现 "attempted relative import" 错误？

Python 的相对导入（如 `from .schemas import ...`）只能在包内使用，且需要满足：

1. **模块必须作为包的一部分被导入**，不能直接作为脚本运行
2. **Python 需要知道包的边界**（通过 `__init__.py`）

当您直接运行 `python analyze/pipeline.py` 时：
- Python 将 `pipeline.py` 视为独立脚本
- 它不知道 `pipeline.py` 是 `analyze` 包的一部分
- 相对导入 `from .schemas import ...` 找不到父包

使用 `python -m analyze.pipeline` 时：
- Python 知道 `analyze` 是一个包
- 相对导入可以正确解析
- 所有模块都能正确加载

## 快速开始

### 1. 测试包是否正常工作

```bash
cd /Users/orangezhi/Desktop/mydata
python test_analyze.py
```

### 2. 准备数据文件

创建 `data/tasks.jsonl`，每行一个 JSON 对象：

```json
{"task_id": "T001", "language": "python", "prompt": "...", "good_code": "...", "bad_codes": [{"bad_id": "b1", "code": "..."}]}
```

### 3. 运行 Pipeline

```bash
python run_pipeline.py
```

或使用模块方式：

```bash
python -m analyze.pipeline
```

### 4. 查看结果

结果将保存在 `outputs/` 目录：
- `per_task.jsonl` - 每个任务的分析结果
- `agg_dimension.csv` - 维度聚合统计
- `agg_keywords.csv` - 关键词聚合统计
- `figs/` - 可视化图表
- `report.md` - 分析报告

## 环境变量配置

```bash
# 输入文件路径
export INPUT_JSONL="data/tasks.jsonl"

# 输出目录
export OUTPUT_DIR="outputs"

# 中文字体路径（用于词云）
export FONT_PATH="/System/Library/Fonts/PingFang.ttc"

# 运行
python -m analyze.pipeline
```

## 常见问题

### Q: 如何在其他项目中使用这个包？

A: 将项目根目录添加到 PYTHONPATH：

```bash
export PYTHONPATH=/Users/orangezhi/Desktop/mydata:$PYTHONPATH
```

或在代码中：

```python
import sys
sys.path.insert(0, '/Users/orangezhi/Desktop/mydata')

from analyze import run_pipeline
```

### Q: 如何调试代码？

A: 使用 VS Code 的调试功能，配置如下：

```json
// .vscode/launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Run Pipeline",
            "type": "python",
            "request": "launch",
            "module": "analyze.pipeline",
            "justMyCode": true,
            "cwd": "${workspaceFolder}"
        }
    ]
}
```

## 开发建议

- ✅ 始终在项目根目录运行命令
- ✅ 使用 `python -m` 方式运行模块
- ✅ 使用绝对导入或相对导入（在包内）
- ❌ 不要直接运行包内的 `.py` 文件
- ❌ 不要在包目录内运行命令
