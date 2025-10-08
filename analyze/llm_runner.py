"""LLM 调用接口（占位）。

当前省略具体网络/API 细节。后续可接入任意提供商，
并替换 NotImplementedError 为真实调用逻辑。
"""

from __future__ import annotations

from typing import Optional
import json

from .schemas import ModelOutput, TaskInput, to_json_compatible
from .prompting import build_1vN_prompt


def call_model(prompt: str, model: str = "vllm", temperature: float = 0.0, max_tokens: Optional[int] = None) -> str:
    """使用给定 Prompt 调用 LLM 并返回原始文本。

    真实 vLLM 接入点：当 model=="vllm" 时，调用 send_vllm(prompt)。
    你只需实现 send_vllm 并返回字符串。
    """
    if model == "vllm":
        # 真实 vLLM 接入点：请实现 send_vllm(prompt) 返回字符串
        return send_vllm(prompt)
    raise NotImplementedError


def extract_json_block(raw: str) -> str:
    """从原始响应中提取 JSON 片段。

    实现：从“输入：”标记之后查找第一个 '{'，
    做括号匹配提取完整 JSON 对象字符串。
    """
    anchor = "输入："
    start = raw.find(anchor)
    start = start + len(anchor) if start != -1 else 0
    i = raw.find("{", start)
    if i == -1:
        i = raw.find("{")
        if i == -1:
            raise ValueError("未找到 JSON 起始位置")
    # 简单双引号忽略的括号匹配
    depth = 0
    in_str = False
    esc = False
    for j in range(i, len(raw)):
        ch = raw[j]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return raw[i : j + 1]
    raise ValueError("未找到完整的 JSON 块")


def parse_model_response(raw: str) -> ModelOutput:
    """将原始模型输出解析为目标结构。

    默认解析为 JSON dict 并直接返回原始 dict（或可扩展为严格校验）。
    这里我们将其保持为轻量：返回 ModelOutput 的 dict 形式。
    """
    try:
        data = json.loads(raw)
    except Exception:
        # 若返回文本包含前后缀，尝试提取 JSON 片段
        data = json.loads(extract_json_block(raw))
    # 可在此加入严格的 schema 校验或 dataclass 转换。
    # 目前返回原始 dict 以便上游直接写入 JSONL。
    return data  # type: ignore[return-value]


def _taskinput_from_prompt_json(data: dict) -> TaskInput:
    """从 Prompt 中的输入 JSON 恢复 TaskInput。"""
    bads = data.get("bad_codes", [])
    from .schemas import BadCode

    return TaskInput(
        task_id=data.get("task_id", "T0000"),
        language=data.get("language", "python"),
        prompt=data.get("prompt", ""),
        good_code=data.get("good_code", ""),
        bad_codes=[BadCode(bad_id=b.get("bad_id", f"b{i+1}"), code=b.get("code", "")) for i, b in enumerate(bads)],
    )


def send_vllm(prompt: str) -> str:
    """发送 Prompt 到你的 vLLM 服务并返回原始响应字符串。

    你只需要实现这个函数：
    - 输入：已构造好的完整 Prompt（包含规范与输入 JSON）；
    - 输出：模型返回的字符串（推荐严格为 JSON，符合 analyze/schemas.py 中的输出结构）。

    示例（HTTP 请求伪代码）：
    
    import os, requests
    url = os.environ.get("VLLM_URL", "http://localhost:8000/generate")
    payload = {"prompt": prompt, "temperature": 0.0, "max_tokens": 2048}
    resp = requests.post(url, json=payload, timeout=60)
    text = resp.json()["text"][0]
    return text

    注意：如果返回不是严格 JSON，而是含前缀/后缀的文本，保持 parse_model_response 的容错即可；
    如果你能让模型严格输出 JSON，parse_model_response 会直接 json.loads(raw)。
    """
    raise NotImplementedError("请实现 send_vllm(prompt) 与你的 vLLM API 对接")
