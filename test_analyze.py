#!/usr/bin/env python
"""测试脚本：验证 analyze 包的基本功能。

使用方式:
    python test_analyze.py
"""

from analyze import (
    TaskInput,
    BadCode,
    Dimension,
    build_1vN_prompt,
    validate_task_input,
)


def test_basic_functionality():
    """测试基本功能是否正常。"""
    print("测试 analyze 包...")
    
    # 创建测试任务
    task = TaskInput(
        task_id="T001",
        language="python",
        prompt="编写一个函数计算两个数的和",
        good_code="def add(a, b):\n    return a + b",
        bad_codes=[
            BadCode(bad_id="b1", code="def add(a, b):\n    return a - b"),
            BadCode(bad_id="b2", code="def add(a, b):\n    return a * b"),
        ]
    )
    
    # 验证任务
    try:
        validate_task_input(task)
        print("✓ 任务验证通过")
    except Exception as e:
        print(f"✗ 任务验证失败: {e}")
        return False
    
    # 构建 Prompt
    try:
        prompt = build_1vN_prompt(task)
        print(f"✓ Prompt 构建成功（长度: {len(prompt)} 字符）")
        print(f"\nPrompt 预览:\n{prompt[:200]}...\n")
    except Exception as e:
        print(f"✗ Prompt 构建失败: {e}")
        return False
    
    # 测试维度枚举
    print(f"✓ 可用维度: {', '.join([d.value for d in Dimension])}")
    
    print("\n所有基本功能测试通过！")
    return True


if __name__ == "__main__":
    success = test_basic_functionality()
    raise SystemExit(0 if success else 1)
