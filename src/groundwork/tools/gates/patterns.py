"""Curated secret pack + entropy hint. Pattern shapes follow the prior art
(gitleaks, detect-secrets); kept deliberately small and high-precision."""
import math
import re
from fnmatch import fnmatch
from pathlib import PurePosixPath

# (name, action, regex). Deny is reserved for unambiguous, high-damage hits.
_RULES = (
    ("aws-access-key-id", "deny", r"\bAKIA[0-9A-Z]{16}\b"),
    ("github-token", "deny", r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    ("gitlab-token", "deny", r"\bglpat-[0-9a-zA-Z_-]{20,}\b"),
    ("slack-token", "deny", r"\bxox[baprs]-[0-9A-Za-z-]{10,}\b"),
    ("stripe-live-key", "deny", r"\bsk_live_[0-9a-zA-Z]{16,}\b"),
    ("openai-key", "deny", r"\bsk-(?:proj-)?[A-Za-z0-9_-]{40,}\b"),
    ("anthropic-key", "deny", r"\bsk-ant-[A-Za-z0-9_-]{16,}\b"),
    ("google-api-key", "deny", r"\bAIza[0-9A-Za-z_-]{30,}\b"),
    ("huggingface-token", "deny", r"\bhf_[A-Za-z0-9]{30,}\b"),
    ("npm-token", "deny", r"\bnpm_[A-Za-z0-9]{30,}\b"),
    ("private-key-block", "deny",
     r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY(?: BLOCK)?-----"),
    ("jwt", "ask", r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\."),
    ("generic-credential-assignment", "ask",
     r"(?i)\b(?:api_key|apikey|secret|token|password|passwd)\b\s*[:=]\s*"
     r"['\"][^'\"]{12,}['\"]"),
)
SECRET_RULES = tuple((n, a, re.compile(rx)) for n, a, rx in _RULES)

# Entropy is a HINT: candidates are long token-ish runs; findings always ask.
_CANDIDATE = re.compile(r"[A-Za-z0-9+/=_-]{28,}")
_ENTROPY_FLOOR = 4.2
_MAX_CANDIDATES = 200
_EXEMPT_GLOBS = ("*.lock", "*package-lock.json", "*.min.js", "*.svg",
                 "*.groundwork/*", ".groundwork/*")


def _shannon(s: str) -> float:
    counts = {c: s.count(c) for c in set(s)}
    n = len(s)
    return -sum((v / n) * math.log2(v / n) for v in counts.values())


def _redact(match: str) -> str:
    return match[:8] + "…"


def _exempt(path: str, allow_files: tuple[str, ...]) -> bool:
    if not path:
        return False
    posix = PurePosixPath(path.replace("\\", "/")).as_posix()
    return any(fnmatch(posix, g) for g in (*_EXEMPT_GLOBS, *allow_files))


def scan_text(text: str, *, path: str = "",
              allow_files: tuple[str, ...] = ()) -> list[dict]:
    """Scan text for secret shapes. Findings carry rule/action/redacted match."""
    if not text or _exempt(path, allow_files):
        return []
    findings = []
    for name, action, rx in SECRET_RULES:
        for m in rx.finditer(text):
            findings.append({"rule": name, "action": action,
                             "match": _redact(m.group(0)),
                             "line": text.count("\n", 0, m.start()) + 1})
    flagged_lines = {f["line"] for f in findings}
    for m in list(_CANDIDATE.finditer(text))[:_MAX_CANDIDATES]:
        token = m.group(0)
        line = text.count("\n", 0, m.start()) + 1
        if line in flagged_lines:
            continue  # already caught by a named rule on this line
        if _shannon(token) >= _ENTROPY_FLOOR:
            findings.append({"rule": "entropy", "action": "ask",
                             "match": _redact(token), "line": line})
    findings.sort(key=lambda f: (f["line"], f["rule"]))
    return findings
