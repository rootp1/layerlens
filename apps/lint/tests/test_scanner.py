import os

from layerlens_lint.scanner import find_dockerfiles, scan_file, scan_path


def _write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


def test_find_dockerfiles_recurses_and_skips_ignored_dirs(tmp_path):
    _write(str(tmp_path / "Dockerfile"), "FROM alpine\n")
    _write(str(tmp_path / "services" / "api" / "Dockerfile"), "FROM alpine\n")
    _write(str(tmp_path / "services" / "web" / "Dockerfile.dev"), "FROM alpine\n")
    _write(str(tmp_path / "node_modules" / "somepkg" / "Dockerfile"), "FROM alpine\n")

    found = find_dockerfiles(str(tmp_path))
    relative = sorted(os.path.relpath(p, str(tmp_path)) for p in found)

    assert "Dockerfile" in relative
    assert os.path.join("services", "api", "Dockerfile") in relative
    assert os.path.join("services", "web", "Dockerfile.dev") in relative
    assert not any("node_modules" in p for p in relative)


def test_scan_file_detects_sibling_dockerignore(tmp_path, bad_dockerfile):
    dockerfile_path = tmp_path / "Dockerfile"
    _write(str(dockerfile_path), bad_dockerfile)

    report_without = scan_file(str(dockerfile_path))
    assert report_without.dockerignore_present is False
    assert "missing_dockerignore" in {f.rule_id for f in report_without.result.findings}

    _write(str(tmp_path / ".dockerignore"), "node_modules\n.git\n")
    report_with = scan_file(str(dockerfile_path))
    assert report_with.dockerignore_present is True
    assert "missing_dockerignore" not in {f.rule_id for f in report_with.result.findings}


def test_scan_path_on_directory_finds_all_files(tmp_path, bad_dockerfile, good_dockerfile):
    _write(str(tmp_path / "a" / "Dockerfile"), bad_dockerfile)
    _write(str(tmp_path / "b" / "Dockerfile"), good_dockerfile)

    report = scan_path(str(tmp_path))
    assert len(report.files) == 2
    scores = {os.path.relpath(f.path, str(tmp_path)): f.result.score for f in report.files}
    assert scores[os.path.join("a", "Dockerfile")] < scores[os.path.join("b", "Dockerfile")]
    assert report.lowest_score == min(scores.values())


def test_scan_path_on_single_file(tmp_path, good_dockerfile):
    dockerfile_path = tmp_path / "Dockerfile"
    _write(str(dockerfile_path), good_dockerfile)

    report = scan_path(str(dockerfile_path))
    assert len(report.files) == 1
    assert report.files[0].path == str(dockerfile_path)
