"""LLM 调用接口（占位）。

当前省略具体网络/API 细节。后续可接入任意提供商，
并替换 NotImplementedError 为真实调用逻辑。
"""

from __future__ import annotations

from typing import Optional
import json
import time

from .schemas import ModelOutput, TaskInput, to_json_compatible
from .prompting import build_1vN_prompt


def call_model(prompt: str, model = None, temperature: float = 0.8, max_tokens: Optional[int] = None, max_retries: int = 3) -> Optional[str]:
    """使用给定 Prompt 调用 LLM 并返回原始文本。

    Args:
        prompt: 要发送给模型的提示文本
        model: OpenAI client 实例，如果为 None 则抛出错误
        temperature: 采样温度
        max_tokens: 最大生成 token 数
        max_retries: 如果响应无法解析为 JSON，最多重试次数
    
    Returns:
        模型返回的原始文本，如果所有重试都失败则返回 None
    """
    if model is None:
        raise ValueError("必须提供 model (OpenAI client) 参数")
    
    for attempt in range(max_retries):
        try:
            # 调用 OpenAI 兼容的 API (vLLM)
            response = model.chat.completions.create(
                model="/var/shared/models/Qwen3-30B-A3B-Instruct-2507",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            content = response.choices[0].message.content
            
            # 验证响应是否可以解析为 JSON
            try:
                json.loads(content)
                # 成功解析，返回内容
                return content
            except json.JSONDecodeError:
                # 尝试提取 JSON 块
                try:
                    extract_json_block(content)
                    # 能提取到 JSON 块，返回原始内容
                    return content
                except ValueError:
                    # 无法提取 JSON
                    if attempt < max_retries - 1:
                        print(f"[警告] 第 {attempt + 1} 次尝试失败，响应无法解析为 JSON，正在重试...")
                        time.sleep(1)  # 等待 1 秒后重试
                        continue
                    else:
                        print(f"[错误] 已重试 {max_retries} 次，仍无法获得有效 JSON 响应，跳过此任务")
                        return None
        
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"[警告] 第 {attempt + 1} 次调用出错: {e}，正在重试...")
                time.sleep(1)
                continue
            else:
                print(f"[错误] 已重试 {max_retries} 次，仍然失败: {e}，跳过此任务")
                return None
    
    return None


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
