"""Settings and configuration management using Pydantic."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class CollectorSettings(BaseSettings):
    ai_model_sources: list[str] = Field(default=["openai", "anthropic", "google", "meta", "mistral", "cohere"])
    github_token: Optional[str] = Field(default=None)
    github_repos: list[str] = Field(default=["huggingface/transformers", "openai/whisper", "facebookresearch/llama", "microsoft/DeepSpeed", "karpathy/nanoGPT"])
    github_max_repos: int = Field(default=50)
    hf_token: Optional[str] = Field(default=None)
    hf_model_tags: list[str] = Field(default=["transformers", "pytorch", "text-generation", "llm"])
    hf_max_models: int = Field(default=100)
    arxiv_categories: list[str] = Field(default=["cs.AI", "cs.LG", "cs.CL", "cs.CV", "cs.NE"])
    arxiv_max_papers: int = Field(default=50)


class AnalyzerSettings(BaseSettings):
    llm_provider: str = Field(default="anthropic")
    llm_model: str = Field(default="claude-sonnet-4-20250514")
    llm_api_key: Optional[str] = Field(default=None)
    llm_max_tokens: int = Field(default=8192)
    llm_temperature: float = Field(default=0.7)
    insight_depth: str = Field(default="comprehensive")
    model_analysis_depth: str = Field(default="detailed")
    enable_code_analysis: bool = Field(default=True)


class SchedulerSettings(BaseSettings):
    enabled: bool = Field(default=True)
    timezone: str = Field(default="Asia/Shanghai")
    collector_schedule: str = Field(default="0 6 * * *")
    analyzer_schedule: str = Field(default="0 8 * * *")
    report_schedule: str = Field(default="0 10 * * *")
    max_retries: int = Field(default=3)
    retry_delay: int = Field(default=300)


class MemorySettings(BaseSettings):
    enabled: bool = Field(default=True)
    storage_backend: str = Field(default="sqlite")
    db_path: Path = Field(default=Path("data/memory/memory.db"))
    max_memory_items: int = Field(default=10000)
    retention_days: int = Field(default=90)


class APISettings(BaseSettings):
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    debug: bool = Field(default=False)
    cors_origins: list[str] = Field(default=["*"])


class GUISettings(BaseSettings):
    enabled: bool = Field(default=True)
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=7860)
    share: bool = Field(default=False)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AI_INSIGHT_", env_nested_delimiter="__", case_sensitive=False)
    app_name: str = Field(default="AI Insight System")
    version: str = Field(default="0.1.0")
    environment: str = Field(default="development")
    log_level: str = Field(default="INFO")
    data_dir: Path = Field(default=Path("data"))
    reports_dir: Path = Field(default=Path("reports"))
    logs_dir: Path = Field(default=Path("logs"))
    collector: CollectorSettings = Field(default_factory=CollectorSettings)
    analyzer: AnalyzerSettings = Field(default_factory=AnalyzerSettings)
    scheduler: SchedulerSettings = Field(default_factory=SchedulerSettings)
    memory: MemorySettings = Field(default_factory=MemorySettings)
    api: APISettings = Field(default_factory=APISettings)
    gui: GUISettings = Field(default_factory=GUISettings)

    @field_validator("data_dir", "reports_dir", "logs_dir", mode="before")
    @classmethod
    def ensure_path(cls, v: Any) -> Path:
        if isinstance(v, str):
            return Path(v)
        return v

    def ensure_directories(self) -> None:
        for path in [self.data_dir, self.reports_dir, self.logs_dir]:
            path.mkdir(parents=True, exist_ok=True)
        if self.memory.enabled:
            self.memory.db_path.parent.mkdir(parents=True, exist_ok=True)


def load_settings(config_path: Optional[Path] = None) -> Settings:
    settings_dict: dict[str, Any] = {}
    if config_path and config_path.exists():
        with open(config_path) as f:
            settings_dict = yaml.safe_load(f) or {}
    env_settings = {
        "github_token": os.getenv("GITHUB_TOKEN"),
        "hf_token": os.getenv("HUGGINGFACE_TOKEN"),
        "llm_api_key": os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY"),
    }
    if settings_dict.get("collector"):
        for key, value in env_settings.items():
            if value is not None:
                settings_dict["collector"][key] = value
    return Settings(**settings_dict)
