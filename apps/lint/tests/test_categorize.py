from layerlens_lint.categorize import prioritize
from layerlens_lint.rules import analyze


def test_top_issues_sorted_by_weight_desc(bad_dockerfile):
    result = analyze(bad_dockerfile)
    prio = prioritize(result, top_n=3)

    assert len(prio.top_issues) == 3
    weights = [f.weight for f in prio.top_issues]
    assert weights == sorted(weights, reverse=True)
    # the highest-weight findings in bad_dockerfile are the 15-point ones
    assert weights[0] >= weights[1] >= weights[2]


def test_quick_wins_and_advanced_are_disjoint_and_cover_all_findings(bad_dockerfile):
    result = analyze(bad_dockerfile)
    prio = prioritize(result)

    quick_ids = {f.rule_id for f in prio.quick_wins}
    advanced_ids = {f.rule_id for f in prio.advanced_improvements}
    all_ids = {f.rule_id for f in result.findings}

    assert quick_ids.isdisjoint(advanced_ids)
    assert quick_ids | advanced_ids == all_ids


def test_top_n_is_configurable(bad_dockerfile):
    result = analyze(bad_dockerfile)
    prio = prioritize(result, top_n=1)
    assert len(prio.top_issues) == 1


def test_prioritize_on_clean_dockerfile_is_all_empty():
    result = analyze("FROM alpine:3.19\nUSER nobody\nHEALTHCHECK CMD true\nCMD [\"sh\"]\n", dockerignore_present=True)
    prio = prioritize(result)
    assert prio.top_issues == []
    assert prio.quick_wins == []
    assert prio.advanced_improvements == []
