"""多 vLLM 实例并发调用管理器。

支持将任务分发到多个 vLLM 实例上并发执行，提高推理吞吐量。
"""

from __future__ import annotations

import os
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from openai import OpenAI


class MultiVLLMClient:
    """管理多个 vLLM 实例的并发调用。
    
    支持负载均衡和故障转移。
    """
    
    def __init__(self, base_urls: List[str], api_key: str = "EMPTY", max_workers: Optional[int] = None):
        """初始化多实例客户端。
        
        Args:
            base_urls: vLLM 实例的 URL 列表，例如:
                ["http://localhost:8001/v1", "http://localhost:8002/v1", ...]
            api_key: API 密钥（vLLM 默认不验证，使用 "EMPTY"）
            max_workers: 最大并发工作线程数，默认为实例数量
        """
        self.clients = [OpenAI(base_url=url, api_key=api_key) for url in base_urls]
        self.num_clients = len(self.clients)
        self.max_workers = max_workers or self.num_clients
        self.current_index = 0
        self.lock = Lock()
        
        print(f"[MultiVLLM] 初始化 {self.num_clients} 个 vLLM 实例")
        for i, url in enumerate(base_urls):
            print(f"  - 实例 {i}: {url}")
    
    def get_next_client(self) -> OpenAI:
        """轮询获取下一个客户端（负载均衡）。"""
        with self.lock:
            client = self.clients[self.current_index]
            self.current_index = (self.current_index + 1) % self.num_clients
            return client
    
    def chat_completions_create(
        self,
        model: str,
        messages: List[dict],
        temperature: float = 0.8,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        """模拟 OpenAI client 的 chat.completions.create 接口。
        
        自动选择一个可用的 vLLM 实例进行调用。
        """
        client = self.get_next_client()
        return client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
    
    @property
    def chat(self):
        """提供 client.chat.completions.create 的访问方式。"""
        class ChatProxy:
            def __init__(self, parent):
                self.parent = parent
                
            @property
            def completions(self):
                class CompletionsProxy:
                    def __init__(self, parent):
                        self.parent = parent
                    
                    def create(self, **kwargs):
                        return self.parent.chat_completions_create(**kwargs)
                
                return CompletionsProxy(self.parent)
        
        return ChatProxy(self)


def create_multi_vllm_client(
    ports: List[int] = [8001, 8002, 8003, 8004],
    host: str = "localhost",
    api_key: str = "EMPTY"
) -> MultiVLLMClient:
    """创建多实例 vLLM 客户端的便捷函数。
    
    Args:
        ports: vLLM 实例的端口列表
        host: 主机地址
        api_key: API 密钥
    
    Returns:
        MultiVLLMClient 实例
    """
    base_urls = [f"http://{host}:{port}/v1" for port in ports]
    return MultiVLLMClient(base_urls, api_key)


def get_vllm_urls_from_env() -> List[str]:
    """从环境变量读取 vLLM URL 列表。
    
    环境变量格式:
        VLLM_URLS="http://localhost:8001/v1,http://localhost:8002/v1,..."
    或
        VLLM_PORTS="8001,8002,8003,8004"
        VLLM_HOST="localhost"  # 可选，默认 localhost
    
    Returns:
        URL 列表
    """
    # 方式 1: 直接指定完整 URL
    urls_str = os.environ.get("VLLM_URLS")
    if urls_str:
        return [url.strip() for url in urls_str.split(",")]
    
    # 方式 2: 指定端口列表
    ports_str = os.environ.get("VLLM_PORTS", "8001,8002,8003,8004")
    host = os.environ.get("VLLM_HOST", "localhost")
    ports = [int(p.strip()) for p in ports_str.split(",")]
    
    return [f"http://{host}:{port}/v1" for port in ports]
