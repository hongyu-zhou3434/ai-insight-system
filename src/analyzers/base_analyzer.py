from __future__ import annotations
"""Base analyzer class for AI content analysis."""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Generic, TypeVar

T = TypeVar("T")
R = TypeVar("R")


class AnalysisStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass
class AnalysisResult(Generic[R]):
    status: AnalysisStatus
    result: R | None = None
    insights: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    analyzed_at: datetime = field(default_factory=datetime.now)
    source: str = ""
    errors: list[str] = field(default_factory=list)


class BaseAnalyzer(ABC, Generic[T, R]):
    name: str = "base_analyzer"
    description: str = "Base analyzer class"
    
    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.logger = logging.getLogger(f"analyzer.{self.name}")
        self._status = AnalysisStatus.PENDING
    
    @property
    def status(self) -> AnalysisStatus:
        return self._status
    
    @abstractmethod
    async def analyze(self, data: T) -> AnalysisResult[R]:
        pass
    
    async def run(self, data: T) -> AnalysisResult[R]:
        self._status = AnalysisStatus.RUNNING
        self.logger.info(f"Starting analyzer: {self.name}")
        
        try:
            result = await self.analyze(data)
            result.source = self.name
            self._last_result = result
            
            if result.errors:
                self._status = AnalysisStatus.PARTIAL
            else:
                self._status = AnalysisStatus.SUCCESS
            
            return result
        except Exception as e:
            self._status = AnalysisStatus.FAILED
            self.logger.error(f"Analyzer {self.name} failed: {e}")
            return AnalysisResult(
                status=AnalysisStatus.FAILED,
                errors=[str(e)],
                source=self.name
            )
