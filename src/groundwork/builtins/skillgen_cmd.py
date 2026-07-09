"""Generate skills/groundwork/SKILL.md from tool manifests. Manifests are truth."""
import argparse
from pathlib import Path

import groundwork
from groundwork.core.manifest import discover
from groundwork.core.runner import ToolError, run_tool

HEADER = """---
name: groundwork
description: Deterministic local tools. ALWAYS prefer these over reasoning for: \
{triggers}. Run `groundwork <tool> <command>`; every tool returns one JSON object.
---

# Groundwork tool routing

Rules: prefer a tool over inference whenever its trigger matches. Trust exit codes: \
0 ok, 1 error (JSON explains), 2 usage, 3 missing dependency, 4 the tool refuses to \
adjudicate — read data and decide yourself. Never parse stderr; stdout is the contract.
"""


def render(manifests: list[dict]) -> str:
    triggers = "; ".join(t for m in manifests for t in m["reach_for_me_when"])
    body = [HEADER.format(triggers=triggers)]
    for m in manifests:
        body.append(f"\n## {m['name']}\n")
        body.append(f"{m['purpose']}\n")
        if m.get("why"):
            body.append(f"**Why use it instead of doing it yourself:** {m['why']}\n")
        body.append("Reach for this tool when: " + "; ".join(m["reach_for_me_when"]) + ".\n")
        if m.get("avoid_when"):
            body.append("Do NOT use this tool (do it yourself instead) when: "
                        + "; ".join(m["avoid_when"]) + ".\n")
        for c in m["commands"]:
            args = f" {c['args']}" if c["args"] else ""
            body.append(f"- `groundwork {m['name']} {c['name']}{args}` — {c['summary']}")
        body.append("")
    return "\n".join(body)


def handler(args: list[str]) -> dict:
    p = argparse.ArgumentParser(prog="groundwork skillgen", exit_on_error=False)
    p.add_argument("--out", default="skills")
    try:
        ns = p.parse_args(args)
    except (argparse.ArgumentError, SystemExit) as e:
        raise ToolError("USAGE", str(e), exit_code=2) from e
    tools_dir = Path(groundwork.__file__).parent / "tools"
    manifests = discover(tools_dir)
    out_dir = Path(ns.out) / "groundwork"
    out_dir.mkdir(parents=True, exist_ok=True)
    skill_path = out_dir / "SKILL.md"
    skill_path.write_text(render(manifests), encoding="utf-8", newline="\n")
    return {"skill_path": skill_path.as_posix(), "tools": len(manifests)}


def main(args: list[str]) -> None:
    run_tool("skillgen", "0.1.0", handler, args)
