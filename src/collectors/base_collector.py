from __future__ import annotations
"""Base collector class for data gathering."""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class CollectorStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass
class CollectorResult(Generic[T]):
    status: CollectorStatus
    data: list[T] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    collected_at: datetime = field(default_factory=datetime.now)
    items_count: int = 0
    source: str = ""
    
    def __post_init__(self) -> None:
        if not self.items_count:
            self.items_count = len(self.data)


class BaseCollector(ABC, Generic[T]):
    name: str = "base_collector"
    description: str = "Base collector class"
    
    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.logger = logging.getLogger(f"collector.{self.name}")
        self._status = CollectorStatus.PENDING
    
    @property
    def status(self) -> CollectorStatus:
        return self._status
    
    @abstractmethod
    async def collect(self) -> CollectorResult[T]:
        pass
    
    @abstractmethod
    async def validate_config(self) -> bool:
        pass
    
    async def run(self) -> CollectorResult[T]:
        self._status = CollectorStatus.RUNNING
        self.logger.info(f"Starting collector: {self.name}")
        
        try:
            if not await self.validate_config():
                raise ValueError(f"Invalid configuration for {self.name}")
            
            result = await self.collect()
            result.source = self.name
            
            if result.errors:
                self._status = CollectorStatus.PARTIAL
            else:
                self._status = CollectorStatus.SUCCESS
            
            return result
            
        except Exception as e:
            self._status = CollectorStatus.FAILED
            self.logger.error(f"Collector {self.name} failed: {e}")
            return CollectorResult(
                status=CollectorStatus.FAILED,
                errors=[str(e)],
                source=self.name
            )
    
    async def close(self) -> None:
        pass
    
    def _create_result(self, data: list[T], errors: list[str] | None = None, metadata: dict[str, Any] | None = None) -> CollectorResult[T]:
        return CollectorResult(
            status=CollectorStatus.SUCCESS if not errors else CollectorStatus.PARTIAL,
            data=data,
            errors=errors or [],
            metadata=metadata or {},
            source=self.name
        )
