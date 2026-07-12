"""Optional "deep" analysis: build the image from a Dockerfile and run `dive`
against it for real layer-efficiency stats, on top of the static findings.

This is opt-in and gracefully degrades — most repo scans (and every CI
PR-check) should work without Docker/dive ever being installed. Only reach
for this when you specifically want real build-time numbers, not just static
findings.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import uuid


def tools_available() -> bool:
    return shutil.which("docker") is not None and shutil.which("dive") is not None


def _parse_dive_output(output: str) -> dict:
    efficiency_match = re.search(r"efficiency:\s*([\d.]+)\s*%", output)
    wasted_bytes_match = re.search(r"wastedBytes:\s*(\d+)\s*bytes", output)
    user_wasted_match = re.search(r"userWastedPercent:\s*([\d.]+)\s*%", output)
    return {
        "efficiency": float(efficiency_match.group(1)) if efficiency_match else None,
        "wastedBytes": int(wasted_bytes_match.group(1)) if wasted_bytes_match else None,
        "userWastedPercent": float(user_wasted_match.group(1)) if user_wasted_match else None,
    }


def run_deep_analysis(
    dockerfile_path: str,
    context_dir: str = None,
    *,
    image_tag: str = None,
    keep_image: bool = False,
    build_timeout: int = 600,
    dive_timeout: int = 180,
) -> dict:
    if not tools_available():
        return {"error": "'docker' and/or 'dive' aren't available on PATH — skipping deep analysis."}

    context_dir = context_dir or os.path.dirname(os.path.abspath(dockerfile_path)) or "."
    tag = image_tag or f"layerlens-lint-tmp:{uuid.uuid4().hex[:12]}"

    build = subprocess.run(
        ["docker", "build", "-f", dockerfile_path, "-t", tag, context_dir],
        capture_output=True,
        text=True,
        timeout=build_timeout,
    )
    if build.returncode != 0:
        return {"error": f"docker build failed: {build.stderr.strip()[-500:]}"}

    try:
        dive = subprocess.run(
            ["dive", tag, "--ci"],
            capture_output=True,
            text=True,
            timeout=dive_timeout,
        )
    finally:
        if not keep_image:
            subprocess.run(["docker", "rmi", "-f", tag], capture_output=True, text=True)

    if dive.returncode != 0:
        return {"error": f"dive failed: {dive.stderr.strip()[-500:]}"}

    return {"image_tag": tag, "stats": _parse_dive_output(dive.stdout), "output": dive.stdout}
