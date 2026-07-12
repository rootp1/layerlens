"""layerlens-lint: static Dockerfile analysis, as a repo scanner and a CI PR-comment bot."""

from .categorize import Prioritization, prioritize
from .deep import run_deep_analysis, tools_available
from .diff import ComparisonResult, compare
from .explain import ExplainConfig, generate_fix_explanation
from .rules import AnalysisResult, Finding, analyze
from .scanner import FileReport, ScanReport, find_dockerfiles, scan_file, scan_path

__all__ = [
    "analyze",
    "AnalysisResult",
    "Finding",
    "compare",
    "ComparisonResult",
    "scan_path",
    "scan_file",
    "find_dockerfiles",
    "FileReport",
    "ScanReport",
    "prioritize",
    "Prioritization",
    "generate_fix_explanation",
    "ExplainConfig",
    "run_deep_analysis",
    "tools_available",
]

__version__ = "0.2.0"
