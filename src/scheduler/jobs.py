from __future__ import annotations
"""Daily job definitions for scheduled tasks."""

import asyncio
import logging
from datetime import datetime
from typing import Any

from src.analyzers.insight_analyzer import InsightAnalyzer
from src.analyzers.model_analyzer import ModelStructureAnalyzer
from src.collectors.ai_model_collector import AIModelCollector
from src.collectors.arxiv_collector import ArxivCollector
from src.collectors.github_collector import GitHubCollector
from src.collectors.huggingface_collector import HuggingFaceCollector
from src.generators.base_generator import ReportFormat
from src.generators.insight_report_generator import InsightReportGenerator
from src.generators.model_report_generator import ModelReportGenerator
from src.memory.memory_store import MemoryStore


class DailyJobManager:
    def __init__(self, config: dict[str, Any], memory_store: MemoryStore | None = None):
        self.config = config
        self.memory_store = memory_store
        self.logger = logging.getLogger("jobs")
        self.ai_model_collector = AIModelCollector(config.get("collector", {}))
        self.github_collector = GitHubCollector(config.get("collector", {}))
        self.hf_collector = HuggingFaceCollector(config.get("collector", {}))
        self.arxiv_collector = ArxivCollector(config.get("collector", {}))
        self.insight_analyzer = InsightAnalyzer(config.get("analyzer", {}))
        self.model_analyzer = ModelStructureAnalyzer(config.get("analyzer", {}))
        self.insight_generator = InsightReportGenerator()
        self.model_generator = ModelReportGenerator()
        self._last_collection: dict[str, datetime] = {}
        self._collected_data: dict[str, Any] = {}

    async def run_collection_job(self) -> dict[str, Any]:
        self.logger.info("Starting daily collection job")
        start_time = datetime.now()
        results: dict[str, Any] = {"models": [], "papers": [], "repos": [], "hf_models": [], "errors": []}
        tasks = [
            self._safe_collect("ai_models", self.ai_model_collector),
            self._safe_collect("github", self.github_collector),
            self._safe_collect("huggingface", self.hf_collector),
            self._safe_collect("arxiv", self.arxiv_collector)
        ]
        collected = await asyncio.gather(*tasks, return_exceptions=True)
        for name, result in zip(["ai_models", "github", "huggingface", "arxiv"], collected):
            if isinstance(result, Exception):
                results["errors"].append(f"{name}: {result}")
            elif result:
                if name == "ai_models": results["models"] = result.data
                elif name == "github": results["repos"] = result.data
                elif name == "huggingface": results["hf_models"] = result.data
                elif name == "arxiv": results["papers"] = result.data
        self._collected_data = results
        self._last_collection["all"] = start_time
        if self.memory_store:
            await self.memory_store.store(key="last_collection", value={"timestamp": start_time.isoformat(), "counts": {"models": len(results["models"]), "papers": len(results["papers"]), "repos": len(results["repos"]), "hf_models": len(results["hf_models"])}})
        duration = (datetime.now() - start_time).total_seconds()
        self.logger.info(f"Collection job completed in {duration:.2f}s")
        return results

    async def run_analysis_job(self) -> dict[str, Any]:
        self.logger.info("Starting daily analysis job")
        start_time = datetime.now()
        if not self._collected_data:
            self.logger.warning("No data available for analysis. Run collection first.")
            return {"error": "No data available"}
        results: dict[str, Any] = {"insights": None, "model_analyses": [], "errors": []}
        try:
            insight_result = await self.insight_analyzer.run(self._collected_data)
            if insight_result.result: results["insights"] = insight_result.result
        except Exception as e:
            results["errors"].append(f"Insight analysis: {e}")
        model_analyses_results = []
        for model in self._collected_data.get("hf_models", [])[:5]:
            try:
                model_data = {"model_info": {"name": model.model_id, "provider": model.author, "type": model.pipeline_tag}, "config": {}}
                analysis_result = await self.model_analyzer.run(model_data)
                if analysis_result.result:
                    results["model_analyses"].append(analysis_result.result)
                    model_analyses_results.append(analysis_result.result)
            except Exception as e:
                self.logger.warning(f"Model analysis failed for {model.model_id}: {e}")
        self.model_analyzer._last_results = model_analyses_results
        if self.memory_store:
            insight_count = len(results["insights"].insights) if results.get("insights") and hasattr(results["insights"], 'insights') else 0
            await self.memory_store.store(key="last_analysis", value={"timestamp": start_time.isoformat(), "insight_count": insight_count, "model_analyses": len(results["model_analyses"])})
        duration = (datetime.now() - start_time).total_seconds()
        self.logger.info(f"Analysis job completed in {duration:.2f}s")
        return results

    async def run_report_job(self) -> dict[str, Any]:
        self.logger.info("Starting daily report generation job")
        start_time = datetime.now()
        results: dict[str, Any] = {"insight_report": None, "model_reports": [], "errors": []}
        analysis_data = getattr(self.insight_analyzer, "_last_result", None)
        if analysis_data and analysis_data.result:
            try:
                report = await self.insight_generator.generate(analysis_data.result, format=ReportFormat.PPT)
                results["insight_report"] = {"path": str(report.file_path) if report.file_path else None, "title": report.title, "status": report.status.value}
            except Exception as e:
                results["errors"].append(f"Insight report generation: {e}")
        for model_analysis in getattr(self.model_analyzer, "_last_results", []):
            try:
                report = await self.model_generator.generate(model_analysis, format=ReportFormat.PPT)
                results["model_reports"].append({"path": str(report.file_path) if report.file_path else None, "model": model_analysis.model_name, "status": report.status.value})
            except Exception as e:
                self.logger.warning(f"Model report generation failed: {e}")
        duration = (datetime.now() - start_time).total_seconds()
        self.logger.info(f"Report generation completed in {duration:.2f}s")
        return results

    async def run_full_pipeline(self) -> dict[str, Any]:
        self.logger.info("Starting full daily pipeline")
        start_time = datetime.now()
        collection = await self.run_collection_job()
        analysis = await self.run_analysis_job()
        reports = await self.run_report_job()
        duration = (datetime.now() - start_time).total_seconds()
        return {"collection": collection, "analysis": analysis, "reports": reports, "total_duration_seconds": duration, "completed_at": datetime.now().isoformat()}

    async def _safe_collect(self, name: str, collector: Any) -> Any:
        try:
            return await collector.run()
        except Exception as e:
            self.logger.error(f"Collector {name} failed: {e}")
            raise

    async def cleanup(self) -> None:
        await self.github_collector.close()
