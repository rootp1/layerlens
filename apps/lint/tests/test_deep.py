from layerlens_lint import deep


class FakeCompletedProcess:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_deep_analysis_skips_when_tools_missing(monkeypatch):
    monkeypatch.setattr(deep.shutil, "which", lambda name: None)
    result = deep.run_deep_analysis("Dockerfile")
    assert "error" in result
    assert "skipping deep analysis" in result["error"]


def test_deep_analysis_reports_build_failure(monkeypatch):
    monkeypatch.setattr(deep.shutil, "which", lambda name: f"/usr/bin/{name}")

    def fake_run(cmd, **kwargs):
        if cmd[0:2] == ["docker", "build"]:
            return FakeCompletedProcess(returncode=1, stderr="failed to compute cache key")
        raise AssertionError(f"unexpected subprocess call: {cmd}")

    monkeypatch.setattr(deep.subprocess, "run", fake_run)

    result = deep.run_deep_analysis("Dockerfile", context_dir=".")
    assert "error" in result
    assert "docker build failed" in result["error"]


def test_deep_analysis_reports_dive_failure_and_still_cleans_up_image(monkeypatch):
    monkeypatch.setattr(deep.shutil, "which", lambda name: f"/usr/bin/{name}")
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        if cmd[0:2] == ["docker", "build"]:
            return FakeCompletedProcess(returncode=0)
        if cmd[0] == "dive":
            return FakeCompletedProcess(returncode=1, stderr="cannot fetch image")
        if cmd[0:2] == ["docker", "rmi"]:
            return FakeCompletedProcess(returncode=0)
        raise AssertionError(f"unexpected subprocess call: {cmd}")

    monkeypatch.setattr(deep.subprocess, "run", fake_run)

    result = deep.run_deep_analysis("Dockerfile", context_dir=".")
    assert "error" in result
    assert "dive failed" in result["error"]
    assert any(cmd[0:2] == ["docker", "rmi"] for cmd in calls)  # cleanup happened despite dive failure


def test_deep_analysis_success_parses_stats_and_cleans_up(monkeypatch):
    monkeypatch.setattr(deep.shutil, "which", lambda name: f"/usr/bin/{name}")
    calls = []
    dive_output = "  efficiency: 91.5000 %\n  wastedBytes: 2048 bytes\n  userWastedPercent: 3.2000 %\n"

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        if cmd[0:2] == ["docker", "build"]:
            return FakeCompletedProcess(returncode=0)
        if cmd[0] == "dive":
            return FakeCompletedProcess(returncode=0, stdout=dive_output)
        if cmd[0:2] == ["docker", "rmi"]:
            return FakeCompletedProcess(returncode=0)
        raise AssertionError(f"unexpected subprocess call: {cmd}")

    monkeypatch.setattr(deep.subprocess, "run", fake_run)

    result = deep.run_deep_analysis("Dockerfile", context_dir=".", image_tag="myimage:test")
    assert result["image_tag"] == "myimage:test"
    assert result["stats"] == {"efficiency": 91.5, "wastedBytes": 2048, "userWastedPercent": 3.2}
    assert any(cmd[0:2] == ["docker", "rmi"] for cmd in calls)


def test_deep_analysis_keep_image_skips_cleanup(monkeypatch):
    monkeypatch.setattr(deep.shutil, "which", lambda name: f"/usr/bin/{name}")
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        if cmd[0:2] == ["docker", "build"]:
            return FakeCompletedProcess(returncode=0)
        if cmd[0] == "dive":
            return FakeCompletedProcess(returncode=0, stdout="efficiency: 100.0000 %\n")
        raise AssertionError(f"unexpected subprocess call: {cmd}")

    monkeypatch.setattr(deep.subprocess, "run", fake_run)

    deep.run_deep_analysis("Dockerfile", context_dir=".", keep_image=True)
    assert not any(cmd[0:2] == ["docker", "rmi"] for cmd in calls)
