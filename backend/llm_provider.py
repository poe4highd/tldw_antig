"""
LLM Provider 管理模块
从 llm_config.yaml 读取配置，按优先级选择 provider。
"""

import os
import yaml
from typing import Optional, Tuple
from openai import OpenAI
from app_logger import get_logger
logger = get_logger(__name__)

_config = None
_config_path = os.path.join(os.path.dirname(__file__), "llm_config.yaml")


def _load_config():
    global _config
    if _config is None:
        with open(_config_path, "r") as f:
            _config = yaml.safe_load(f)
    return _config


def reload_config():
    """强制重新加载配置（热更新用）"""
    global _config
    _config = None
    return _load_config()


def _create_client(provider_cfg) -> Optional[OpenAI]:
    """根据 provider 配置创建 OpenAI 兼容客户端。"""
    name = provider_cfg["name"]

    if name == "ollama":
        # Ollama 用第一个 server 的 URL 作为默认客户端
        servers = provider_cfg.get("servers", [])
        if not servers:
            return None
        return OpenAI(base_url=servers[0]["url"], api_key="ollama")

    # Gemini / OpenAI 等需要 API key
    api_key_env = provider_cfg.get("api_key_env", "")
    api_key = os.getenv(api_key_env, "") if api_key_env else ""
    if not api_key:
        return None

    kwargs = {"api_key": api_key}
    if provider_cfg.get("base_url"):
        kwargs["base_url"] = provider_cfg["base_url"]
    return OpenAI(**kwargs)


def get_provider_config(name: str) -> Optional[dict]:
    """按名称获取 provider 配置。"""
    config = _load_config()
    for p in config.get("providers", []):
        if p["name"] == name:
            return p
    return None


def get_primary() -> Tuple[Optional[OpenAI], str, str]:
    """
    返回第一个 enabled 的 provider。
    返回 (client, provider_name, model)
    """
    config = _load_config()
    for p in config.get("providers", []):
        if not p.get("enabled", False):
            continue
        client = _create_client(p)
        if client:
            model = p.get("model", "")
            logger.info(f"--- [LLM] 主力: {p['name']} ({model}) ---")
            return client, p["name"], model
    return None, "", ""


def get_fallback(exclude: str = "") -> Tuple[Optional[OpenAI], str, str]:
    """
    返回第一个 enabled 且不是 exclude 的 provider（按优先级）。
    返回 (client, provider_name, model)
    """
    config = _load_config()
    for p in config.get("providers", []):
        if not p.get("enabled", False):
            continue
        if p["name"] == exclude:
            continue
        client = _create_client(p)
        if client:
            model = p.get("model", "")
            logger.info(f"--- [LLM Fallback] → {p['name']} ({model}) ---")
            return client, p["name"], model
    return None, "", ""


def get_all_enabled() -> list:
    """返回所有 enabled 的 provider 配置列表（按优先级）。"""
    config = _load_config()
    return [p for p in config.get("providers", []) if p.get("enabled", False)]


def get_ollama_servers() -> list:
    """返回 Ollama 的 servers 配置（供 ServerPool 使用）。"""
    p = get_provider_config("ollama")
    if not p or not p.get("enabled", False):
        return []
    return p.get("servers", [])
