"""Turn a flat list of findings into something a developer can prioritize:
the top-N highest-impact issues, plus a quick-wins vs. advanced-improvements
split. Pure function over `rules.AnalysisResult` — no I/O, trivially testable.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .rules import EFFORT_BY_RULE, AnalysisResult, Finding


@dataclass
class Prioritization:
    top_issues: list = field(default_factory=list)
    quick_wins: list = field(default_factory=list)
    advanced_improvements: list = field(default_factory=list)

    def to_dict(self):
        return {
            "top_issues": [f.to_dict() for f in self.top_issues],
            "quick_wins": [f.to_dict() for f in self.quick_wins],
            "advanced_improvements": [f.to_dict() for f in self.advanced_improvements],
        }


def prioritize(result: AnalysisResult, *, top_n: int = 3) -> Prioritization:
    findings_by_weight = sorted(result.findings, key=lambda f: f.weight, reverse=True)
    top_issues = findings_by_weight[:top_n]

    quick_wins = [f for f in result.findings if EFFORT_BY_RULE.get(f.rule_id, "advanced") == "quick"]
    advanced_improvements = [f for f in result.findings if EFFORT_BY_RULE.get(f.rule_id, "advanced") == "advanced"]

    return Prioritization(
        top_issues=top_issues,
        quick_wins=quick_wins,
        advanced_improvements=advanced_improvements,
    )
