import json
import subprocess
from pathlib import Path


def test_skillgen_writes_master_skill(tmp_path):
    p = subprocess.run(["uv", "run", "groundwork", "skillgen", "--out", str(tmp_path)],
                       capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    out = json.loads(p.stdout)
    skill = Path(out["data"]["skill_path"]).read_text(encoding="utf-8")
    assert "name: groundwork" in skill
    assert "## hello" in skill
    assert "reach for this tool when" in skill.lower()
    assert "groundwork hello greet" in skill
    assert "\\" not in out["data"]["skill_path"]


def test_skillgen_matches_golden(tmp_path):
    subprocess.run(["uv", "run", "groundwork", "skillgen", "--out", str(tmp_path)],
                   capture_output=True, text=True, check=True)
    generated = (tmp_path / "groundwork" / "SKILL.md").read_text(encoding="utf-8")
    assert generated == Path("tests/golden/SKILL.md").read_text(encoding="utf-8")


def test_committed_plugin_skill_matches_golden():
    # Drift guard: skills/groundwork/SKILL.md is the committed plugin copy Claude
    # Code actually loads. If a manifest changes but nobody re-runs skillgen and
    # commits the regenerated file, this copy silently goes stale relative to the
    # golden fixture skillgen is tested against above.
    committed = Path("skills/groundwork/SKILL.md").read_text(encoding="utf-8")
    golden = Path("tests/golden/SKILL.md").read_text(encoding="utf-8")
    assert committed == golden
