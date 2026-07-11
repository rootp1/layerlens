from layerlens_lint.rules import analyze


def test_bad_dockerfile_flags_expected_rules(bad_dockerfile):
    result = analyze(bad_dockerfile)
    rule_ids = {f.rule_id for f in result.findings}

    assert "large_base_image" in rule_ids
    assert "missing_multistage_build" in rule_ids
    assert "copies_entire_context" in rule_ids
    assert "runs_as_root" in rule_ids
    assert "npm_cache_not_cleaned" in rule_ids
    assert result.score < 70


def test_good_dockerfile_scores_much_higher(bad_dockerfile, good_dockerfile):
    bad_result = analyze(bad_dockerfile)
    good_result = analyze(good_dockerfile)

    assert good_result.score > bad_result.score
    good_rule_ids = {f.rule_id for f in good_result.findings}
    assert "runs_as_root" not in good_rule_ids
    assert "missing_multistage_build" not in good_rule_ids
    assert "missing_healthcheck" not in good_rule_ids


def test_secret_file_copy_is_flagged_as_critical(secret_dockerfile):
    result = analyze(secret_dockerfile)
    critical = [f for f in result.findings if f.rule_id == "sensitive_file_copied"]
    assert len(critical) == 1
    assert critical[0].severity == "critical"


def test_score_never_goes_negative():
    # A deliberately terrible Dockerfile shouldn't drive the score below 0.
    # Stacks enough violations (base image, no pin, no multistage despite a
    # build command, copies everything, unclean apt/npm caches, root user,
    # a secret file, excessive layers, ADD misuse, no healthcheck, no
    # .dockerignore) that the raw weight sum comfortably exceeds 100.
    terrible = "\n".join(
        ["FROM ubuntu", "RUN apt-get install -y build-essential", "RUN npm install", "RUN make build"]
        + [f"RUN echo step{i}" for i in range(40)]
        + ["COPY . .", "ADD .env /app/.env"]
    )
    result = analyze(terrible, dockerignore_present=False)
    assert result.score == 0


def test_scratch_base_is_not_flagged_as_unpinned():
    result = analyze("FROM scratch\nCOPY app /app\nENTRYPOINT [\"/app\"]\n")
    rule_ids = {f.rule_id for f in result.findings}
    assert "unpinned_base_image" not in rule_ids


def test_alpine_base_skips_large_base_image_rule():
    result = analyze("FROM python:3.11-alpine\nCOPY . .\nCMD [\"python\", \"app.py\"]\n")
    rule_ids = {f.rule_id for f in result.findings}
    assert "large_base_image" not in rule_ids


def test_dockerignore_missing_flagged_only_when_told():
    text = "FROM alpine:3.19\nCMD [\"sh\"]\n"
    without_flag = analyze(text)
    with_false = analyze(text, dockerignore_present=False)
    with_true = analyze(text, dockerignore_present=True)

    assert "missing_dockerignore" not in {f.rule_id for f in without_flag.findings}
    assert "missing_dockerignore" in {f.rule_id for f in with_false.findings}
    assert "missing_dockerignore" not in {f.rule_id for f in with_true.findings}
