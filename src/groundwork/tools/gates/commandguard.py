"""Dangerous-command packs for BOTH shell families. Matched against any
command regardless of carrying tool (Bash can launch powershell and back)."""
import re

_DENY = (
    ("bash-rm-root", r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)"
                     r"[a-zA-Z]*\s+(/|/\w+)(\s|$)"),
    ("bash-rm-home", r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)"
                     r"[a-zA-Z]*\s+~/?(\s|$)"),
    ("bash-dd-device", r"\bdd\b[^|]*\bof=/dev/"),
    ("bash-mkfs", r"\bmkfs(\.\w+)?\s"),
    ("bash-fork-bomb", r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:"),
    ("ps-remove-drive-root", r"(?i)\bRemove-Item\b.*-Recurse\b.*-Force\b.*"
                             r"\b[A-Za-z]:\\?\s*$"),
    # global (?i) must be at the START of the whole pattern; a single flag
    # covers both del forms (build-time finding, plan 12 corrected).
    ("ps-del-drive-root", r"(?i)\bdel\s+(?:/[a-z]\s+)*[A-Za-z]:\\?\s*$"),
    ("ps-format-drive", r"(?i)\bformat\s+[A-Za-z]:\s*$"),
)
_ASK = (
    ("git-force-push", r"\bgit\s+push\b.*(\s--force\b|\s-f\b)"),
    ("pipe-to-shell", r"\b(curl|wget)\b[^|]*\|\s*(sudo\s+)?(ba|z|da)?sh\b"),
    ("ps-pipe-to-iex", r"(?i)\b(irm|iwr|Invoke-RestMethod|Invoke-WebRequest)\b"
                       r".*\|\s*iex\b"),
    ("chmod-777", r"\bchmod\s+(-[a-zA-Z]+\s+)*777\b"),
    ("git-hard-reset", r"\bgit\s+reset\s+--hard\b"),
)
_DENY_RULES = tuple((n, "deny", re.compile(rx)) for n, rx in _DENY)
_ASK_RULES = tuple((n, "ask", re.compile(rx)) for n, rx in _ASK)


def check_command(command: str, *, extra_deny: tuple[str, ...] = (),
                  extra_ask: tuple[str, ...] = ()) -> list[dict]:
    """All rules that fire on a command, deny rules first."""
    if not command:
        return []
    rules = (_DENY_RULES
             + tuple((f"config-deny-{i}", "deny", re.compile(rx))
                     for i, rx in enumerate(extra_deny))
             + _ASK_RULES
             + tuple((f"config-ask-{i}", "ask", re.compile(rx))
                     for i, rx in enumerate(extra_ask)))
    findings = []
    for name, action, rx in rules:
        if rx.search(command):
            family = ("powershell" if name.startswith("ps-") else
                      "bash" if name.startswith("bash-") else "any")
            findings.append({"rule": name, "action": action, "family": family})
    return findings
