from layerlens_lint.diff import compare


def test_worse_when_dockerfile_regresses(good_dockerfile, bad_dockerfile):
    comparison = compare(good_dockerfile, bad_dockerfile)
    assert comparison.verdict == "worse"
    assert comparison.delta < 0
    assert len(comparison.new_findings) > 0


def test_better_when_dockerfile_improves(bad_dockerfile, good_dockerfile):
    comparison = compare(bad_dockerfile, good_dockerfile)
    assert comparison.verdict == "better"
    assert comparison.delta > 0
    assert len(comparison.resolved_findings) > 0


def test_unchanged_for_identical_dockerfiles(bad_dockerfile):
    comparison = compare(bad_dockerfile, bad_dockerfile)
    assert comparison.verdict == "unchanged"
    assert comparison.delta == 0
    assert comparison.new_findings == []
    assert comparison.resolved_findings == []


def test_tolerance_absorbs_small_regressions():
    base = "FROM alpine:3.19\nUSER nobody\nCMD [\"sh\"]\n"
    # Adds one low-severity 'ADD instead of COPY' finding (weight 4)
    head = "FROM alpine:3.19\nUSER nobody\nADD app /app\nCMD [\"sh\"]\n"

    strict = compare(base, head, tolerance=0)
    lenient = compare(base, head, tolerance=10)

    assert strict.verdict == "worse"
    assert lenient.verdict == "unchanged"
