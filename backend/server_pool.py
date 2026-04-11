"""
Ollama 服务器池管理模块
支持多服务器并行处理、时间窗口调度、健康检测
"""

import os
import re
import time
from datetime import datetime
from typing import List, Optional
from openai import OpenAI


class OllamaServer:
    """单个 Ollama 服务器实例"""

    def __init__(self, base_url: str, schedule: str = "always"):
        self.base_url = base_url
        self.schedule = schedule  # "always" 或 "HH:MM-HH:MM"（可用时段）
        self.client = OpenAI(base_url=base_url, api_key="ollama")
        self.busy = False
        self.consecutive_failures = 0
        self.last_failure_time = 0.0

    def is_available(self) -> bool:
        """检查服务器是否可用（时间窗口 + 健康状态 + 忙碌标志）"""
        # 连续失败 3 次 → 冷却 5 分钟
        if self.consecutive_failures >= 3:
            if time.time() - self.last_failure_time < 300:
                return False
            self.consecutive_failures = 0  # 冷却结束，重置

        if self.busy:
            return False

        if self.schedule == "always":
            return True

        try:
            start_str, end_str = self.schedule.split("-")
            now = datetime.now()
            start_h, start_m = map(int, start_str.split(":"))
            end_h, end_m = map(int, end_str.split(":"))
            start_minutes = start_h * 60 + start_m
            end_minutes = end_h * 60 + end_m
            now_minutes = now.hour * 60 + now.minute

            if start_minutes <= end_minutes:
                return start_minutes <= now_minutes < end_minutes
            else:  # 跨午夜，如 "23:00-07:00"
                return now_minutes >= start_minutes or now_minutes < end_minutes
        except Exception:
            return True

    def report_success(self):
        self.consecutive_failures = 0
        self.busy = False

    def report_failure(self):
        self.consecutive_failures += 1
        self.last_failure_time = time.time()
        self.busy = False

    def __repr__(self):
        return f"OllamaServer({self.base_url}, schedule={self.schedule}, failures={self.consecutive_failures})"


class ServerPool:
    """Ollama 服务器池，支持多服务器调度"""

    def __init__(self):
        self.servers: List[OllamaServer] = []
        self._load_from_env()

    def _load_from_env(self):
        servers_str = os.getenv("OLLAMA_SERVERS", "")
        if not servers_str:
            # 回退到单服务器配置
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
            self.servers = [OllamaServer(base_url, "always")]
            print(f"--- [ServerPool] 单服务器模式: {base_url} ---")
            return

        for url in servers_str.split(","):
            url = url.strip()
            if not url:
                continue
            # 从 URL 提取最后一组 IP 段，用于查找对应的调度配置
            # e.g., http://192.168.1.176:11434/v1 → 查找 OLLAMA_SERVER_176_SCHEDULE
            ip_match = re.search(r'\.(\d+):\d+', url)
            if ip_match:
                last_octet = ip_match.group(1)
                schedule = os.getenv(f"OLLAMA_SERVER_{last_octet}_SCHEDULE", "always")
            else:
                schedule = "always"
            self.servers.append(OllamaServer(url, schedule))

        print(f"--- [ServerPool] 已加载 {len(self.servers)} 台服务器: "
              f"{[(s.base_url, s.schedule) for s in self.servers]} ---")

    def get_available_servers(self) -> List[OllamaServer]:
        """返回当前可用的服务器列表"""
        return [s for s in self.servers if s.is_available()]

    def get_available_count(self) -> int:
        return len(self.get_available_servers())

    def get_any_server(self) -> Optional[OllamaServer]:
        """返回任意一台可用服务器（优先失败次数少的）"""
        available = self.get_available_servers()
        if not available:
            return None
        return min(available, key=lambda s: s.consecutive_failures)
