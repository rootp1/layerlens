"""layerlens-lint: static Dockerfile analysis, as a repo scanner and a CI PR-comment bot."""

from .diff import ComparisonResult, compare
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
]

__version__ = "0.1.0"
