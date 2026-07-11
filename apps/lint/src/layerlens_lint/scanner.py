"""Repo-scanning: find Dockerfiles in a tree and run the rule engine on each,
before anything gets built. This is the "repo tool that scans Dockerfiles
automatically and suggests fixes before build" half of the package.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from .rules import AnalysisResult, analyze

IGNORED_DIR_NAMES = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "flaskenv",
    "build", "dist", ".next", ".cache",
}


def _is_dockerfile(filename: str) -> bool:
    return filename == "Dockerfile" or filename.startswith("Dockerfile.") or filename.endswith(".Dockerfile")


def find_dockerfiles(root: str) -> list:
    """Recursively find Dockerfile paths under `root`, skipping common
    dependency/build/vcs directories."""
    matches = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIR_NAMES]
        for filename in filenames:
            if _is_dockerfile(filename):
                matches.append(os.path.join(dirpath, filename))
    return sorted(matches)


@dataclass
class FileReport:
    path: str
    result: AnalysisResult
    dockerignore_present: bool

    def to_dict(self):
        return {
            "path": self.path,
            "dockerignore_present": self.dockerignore_present,
            **self.result.to_dict(),
        }


@dataclass
class ScanReport:
    files: list = field(default_factory=list)

    @property
    def lowest_score(self) -> int:
        if not self.files:
            return 100
        return min(f.result.score for f in self.files)

    def to_dict(self):
        return {"files": [f.to_dict() for f in self.files]}


def scan_file(path: str) -> FileReport:
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    dockerignore_path = os.path.join(os.path.dirname(os.path.abspath(path)), ".dockerignore")
    dockerignore_present = os.path.exists(dockerignore_path)
    result = analyze(text, dockerignore_present=dockerignore_present)
    return FileReport(path=path, result=result, dockerignore_present=dockerignore_present)


def scan_path(path: str) -> ScanReport:
    """Scan a single Dockerfile, or every Dockerfile found under a directory."""
    if os.path.isfile(path):
        return ScanReport(files=[scan_file(path)])

    paths = find_dockerfiles(path)
    return ScanReport(files=[scan_file(p) for p in paths])
