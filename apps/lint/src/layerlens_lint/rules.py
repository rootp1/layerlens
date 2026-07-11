"""Deterministic, static-analysis rule engine for Dockerfiles.

Unlike the main LayerLens backend (which runs `dive` against a real, already-built
image), everything here works purely from the *text* of a Dockerfile — no Docker
daemon, no image pull, no build required. That's what makes it usable both as a
pre-build repo scanner and inside CI on a PR diff, where a built image may not
exist yet.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

SLIM_BASE_HINTS = ("alpine", "slim", "distroless", "scratch", "-minimal")
FAT_BASE_FAMILIES = (
    "ubuntu", "debian", "centos", "fedora", "rockylinux", "almalinux",
    "node", "python", "golang", "openjdk", "ruby", "php",
)
BUILD_COMMANDS = (
    "npm run build", "yarn build", "go build", "mvn ", "gradle", "make ",
    "gcc ", "g++ ", "cargo build", "webpack", "tsc",
)
SECRET_PATTERNS = (
    ".env", "id_rsa", ".pem", "credentials.json", "service-account.json",
    ".aws", ".ssh", ".git",
)

MAX_REASONABLE_LAYERS = 15


@dataclass
class Finding:
    rule_id: str
    severity: str  # 'critical' | 'high' | 'medium' | 'low'
    message: str
    suggestion: str
    weight: int

    def to_dict(self):
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "message": self.message,
            "suggestion": self.suggestion,
            "weight": self.weight,
        }


@dataclass
class AnalysisResult:
    score: int
    findings: list = field(default_factory=list)

    def to_dict(self):
        return {"score": self.score, "findings": [f.to_dict() for f in self.findings]}


def _strip_comments_and_join_continuations(text: str) -> list:
    """Return logical Dockerfile instruction lines (comments stripped, line
    continuations with a trailing backslash joined into one logical line)."""
    raw_lines = text.splitlines()
    logical_lines = []
    buffer = ""
    for raw in raw_lines:
        line = raw.split("#", 1)[0] if not raw.strip().startswith("#") else ""
        if not line.strip() and not buffer:
            continue
        stripped = line.rstrip()
        if stripped.endswith("\\"):
            buffer += stripped[:-1] + " "
            continue
        buffer += line
        if buffer.strip():
            logical_lines.append(buffer.strip())
        buffer = ""
    if buffer.strip():
        logical_lines.append(buffer.strip())
    return logical_lines


def _from_lines(lines):
    return [l for l in lines if l.upper().startswith("FROM ")]


def analyze(dockerfile_text: str, *, dockerignore_present: bool = None) -> AnalysisResult:
    """Analyze raw Dockerfile text and return a score (0-100) plus findings.

    `dockerignore_present` — pass True/False when the caller knows whether a
    sibling .dockerignore exists (e.g. when scanning a real repo checkout);
    leave as None (skips that check) when only a bare Dockerfile string is
    available, such as a `git show base:Dockerfile` snippet in CI.
    """
    findings = []
    lines = _strip_comments_and_join_continuations(dockerfile_text)
    from_lines = _from_lines(lines)
    joined = "\n".join(lines).lower()

    # Rule: large/fat base image
    for from_line in from_lines:
        base_ref = from_line.split()[1] if len(from_line.split()) > 1 else ""
        base_lower = base_ref.lower()
        if any(hint in base_lower for hint in SLIM_BASE_HINTS):
            continue
        family = base_lower.split(":")[0].split("/")[-1]
        if any(family == fam or family.startswith(fam) for fam in FAT_BASE_FAMILIES):
            findings.append(Finding(
                rule_id="large_base_image",
                severity="high",
                message=f"Base image '{base_ref}' doesn't look like a slim/alpine/distroless variant.",
                suggestion=f"Consider a smaller base, e.g. an '-alpine' or '-slim' tag for '{family}', "
                           "or a distroless runtime image.",
                weight=15,
            ))
            break  # one finding is enough even with multiple fat FROMs

    # Rule: unpinned / :latest base image
    for from_line in from_lines:
        parts = from_line.split()
        ref = parts[1] if len(parts) > 1 else ""
        if ref.lower() in ("scratch",):
            continue
        if ":" not in ref.split("@")[0] or ref.endswith(":latest"):
            findings.append(Finding(
                rule_id="unpinned_base_image",
                severity="medium",
                message=f"Base image '{ref}' has no pinned version tag (or uses ':latest').",
                suggestion="Pin an explicit version tag so builds are reproducible.",
                weight=10,
            ))
            break

    # Rule: no multi-stage build despite running build tooling
    is_multistage = len(from_lines) > 1
    uses_build_tools = any(cmd in joined for cmd in BUILD_COMMANDS)
    if not is_multistage and uses_build_tools:
        findings.append(Finding(
            rule_id="missing_multistage_build",
            severity="high",
            message="A build command was found but the Dockerfile only has one stage.",
            suggestion="Use a multi-stage build: compile in a 'builder' stage, then COPY --from=builder "
                       "only the runtime artifacts into the final image.",
            weight=15,
        ))

    # Rule: COPY/ADD everything into the image
    if re.search(r'^(COPY|ADD)\s+\.\s+\.\s*$', "\n".join(lines), re.MULTILINE | re.IGNORECASE):
        findings.append(Finding(
            rule_id="copies_entire_context",
            severity="medium",
            message="Found 'COPY . .' (or 'ADD . .') copying the entire build context into the image.",
            suggestion="Copy only what's needed (e.g. package manifests first, then source), and add a "
                       ".dockerignore to exclude tests, docs, .git, and local env files.",
            weight=10,
        ))

    # Rule: apt cache not cleaned
    if "apt-get install" in joined or "apt install" in joined:
        run_blocks = [l for l in lines if l.upper().startswith("RUN") and
                      ("apt-get install" in l.lower() or "apt install" in l.lower())]
        cleaned = any("rm -rf /var/lib/apt/lists" in b.lower() for b in run_blocks)
        if not cleaned:
            findings.append(Finding(
                rule_id="apt_cache_not_cleaned",
                severity="medium",
                message="apt package cache doesn't appear to be cleaned up in the same RUN layer.",
                suggestion="Append '&& rm -rf /var/lib/apt/lists/*' to the same RUN instruction that "
                           "runs apt-get install, so the cache doesn't persist in that layer.",
                weight=8,
            ))

    # Rule: npm install without cache clean / prod flag (single-stage only)
    if not is_multistage and ("npm install" in joined or "npm ci" in joined):
        if "npm cache clean" not in joined and "--omit=dev" not in joined and "--production" not in joined:
            findings.append(Finding(
                rule_id="npm_cache_not_cleaned",
                severity="low",
                message="npm install/ci runs without clearing the npm cache or excluding dev dependencies.",
                suggestion="Use 'npm ci --omit=dev' for production images, or run "
                           "'npm cache clean --force' after install, ideally inside a multi-stage build.",
                weight=6,
            ))

    # Rule: running as root (no USER instruction switching away from root)
    user_lines = [l for l in lines if l.upper().startswith("USER ")]
    if not any(l.split()[1].lower() not in ("root", "0") for l in user_lines if len(l.split()) > 1):
        findings.append(Finding(
            rule_id="runs_as_root",
            severity="high",
            message="No USER instruction switches the container away from root.",
            suggestion="Create a dedicated non-root user and switch to it with a USER instruction "
                       "before the final CMD/ENTRYPOINT.",
            weight=10,
        ))

    # Rule: secrets / sensitive files copied in
    for pattern in SECRET_PATTERNS:
        if re.search(rf'(COPY|ADD)\s+.*{re.escape(pattern)}', "\n".join(lines), re.IGNORECASE):
            findings.append(Finding(
                rule_id="sensitive_file_copied",
                severity="critical",
                message=f"A COPY/ADD instruction appears to include '{pattern}'.",
                suggestion="Remove secrets/credentials from the build context entirely; inject them at "
                           "runtime instead (env vars, mounted secrets, orchestrator-managed secrets).",
                weight=20,
            ))
            break

    # Rule: too many layers
    instruction_count = sum(
        1 for l in lines
        if l.split(" ", 1)[0].upper() in ("RUN", "COPY", "ADD")
    )
    if instruction_count > MAX_REASONABLE_LAYERS:
        findings.append(Finding(
            rule_id="excessive_layers",
            severity="low",
            message=f"{instruction_count} RUN/COPY/ADD instructions found (over {MAX_REASONABLE_LAYERS}).",
            suggestion="Combine related RUN commands with '&&' where it doesn't hurt readability or "
                       "layer caching.",
            weight=8,
        ))

    # Rule: ADD used for a plain local copy (should be COPY)
    for l in lines:
        if l.upper().startswith("ADD "):
            arg = l.split(None, 1)[1] if len(l.split(None, 1)) > 1 else ""
            if not re.search(r'^https?://', arg, re.IGNORECASE) and not arg.strip().endswith(
                (".tar", ".tar.gz", ".tgz", ".tar.bz2", ".tar.xz")
            ):
                findings.append(Finding(
                    rule_id="add_instead_of_copy",
                    severity="low",
                    message="ADD is used for what looks like a plain local file/directory copy.",
                    suggestion="Prefer COPY for local files — reserve ADD for remote URLs or "
                               "auto-extracting local archives.",
                    weight=4,
                ))
                break

    # Rule: missing HEALTHCHECK (informational)
    if not any(l.upper().startswith("HEALTHCHECK") for l in lines):
        findings.append(Finding(
            rule_id="missing_healthcheck",
            severity="low",
            message="No HEALTHCHECK instruction defined.",
            suggestion="Add a HEALTHCHECK so orchestrators can detect an unhealthy container.",
            weight=3,
        ))

    # Rule: no .dockerignore (only checked when the caller tells us)
    if dockerignore_present is False:
        findings.append(Finding(
            rule_id="missing_dockerignore",
            severity="medium",
            message="No .dockerignore file found next to this Dockerfile.",
            suggestion="Add a .dockerignore excluding .git, node_modules, tests, logs, and local env "
                       "files so they never enter the build context.",
            weight=5,
        ))

    score = max(0, 100 - sum(f.weight for f in findings))
    return AnalysisResult(score=score, findings=findings)
