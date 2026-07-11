"""Compare two versions of a Dockerfile (typically a PR's base ref vs. its
head) and decide whether it got better, worse, or stayed the same. This is
the core of the "CI/CD assistant that comments on PRs when Dockerfiles get
worse" feature — GitHub-specific plumbing lives in github.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .rules import analyze


@dataclass
class ComparisonResult:
    base_score: int
    head_score: int
    verdict: str  # 'better' | 'worse' | 'unchanged'
    new_findings: list = field(default_factory=list)
    resolved_findings: list = field(default_factory=list)
    head_findings: list = field(default_factory=list)

    @property
    def delta(self) -> int:
        return self.head_score - self.base_score

    def to_dict(self):
        return {
            "base_score": self.base_score,
            "head_score": self.head_score,
            "delta": self.delta,
            "verdict": self.verdict,
            "new_findings": [f.to_dict() for f in self.new_findings],
            "resolved_findings": [f.to_dict() for f in self.resolved_findings],
        }


def compare(base_text: str, head_text: str, *, tolerance: int = 0) -> ComparisonResult:
    """`tolerance` is how many score points a change is allowed to drop by
    before being called "worse" — 0 means any decrease counts."""
    base_result = analyze(base_text)
    head_result = analyze(head_text)

    base_rule_ids = {f.rule_id for f in base_result.findings}
    head_rule_ids = {f.rule_id for f in head_result.findings}

    new_findings = [f for f in head_result.findings if f.rule_id not in base_rule_ids]
    resolved_findings = [f for f in base_result.findings if f.rule_id not in head_rule_ids]

    delta = head_result.score - base_result.score
    if delta < -tolerance:
        verdict = "worse"
    elif delta > tolerance:
        verdict = "better"
    else:
        verdict = "unchanged"

    return ComparisonResult(
        base_score=base_result.score,
        head_score=head_result.score,
        verdict=verdict,
        new_findings=new_findings,
        resolved_findings=resolved_findings,
        head_findings=head_result.findings,
    )
