#!/usr/bin/env python
"""便捷的 Pipeline 运行脚本。

使用方式:
    python run_pipeline.py
    
或使用环境变量:
    INPUT_JSONL=data/tasks.jsonl OUTPUT_DIR=outputs python run_pipeline.py
"""

if __name__ == "__main__":
    from analyze.pipeline import main
    raise SystemExit(main())
