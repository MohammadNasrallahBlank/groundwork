import json
import shutil
import subprocess
from pathlib import Path

import groundwork


def test_new_tool_scaffold_is_immediately_healthy():
    tools_dir = Path(groundwork.__file__).parent / "tools"
    try:
        p = subprocess.run(["uv", "run", "groundwork", "new-tool", "demo",
                            "--purpose", "Demo purpose."],
                           capture_output=True, text=True)
        assert p.returncode == 0, p.stderr
        # Binding convention: all file paths in JSON output must be posix-style
        out = json.loads(p.stdout)
        assert "\\" not in out["data"]["created"]
        lint = subprocess.run(["uv", "run", "groundwork", "manifest", "lint"],
                              capture_output=True, text=True)
        assert "demo" in json.loads(lint.stdout)["data"]["tools"]
        st = subprocess.run(["uv", "run", "groundwork", "demo", "self-test"],
                            capture_output=True, text=True)
        assert st.returncode == 0
    finally:
        shutil.rmtree(tools_dir / "demo", ignore_errors=True)


def test_new_tool_rejects_bad_name_without_creating_directory():
    tools_dir = Path(groundwork.__file__).parent / "tools"
    bad_dir = tools_dir / "1bad"
    shutil.rmtree(bad_dir, ignore_errors=True)
    try:
        p = subprocess.run(["uv", "run", "groundwork", "new-tool", "1bad",
                            "--purpose", "x"],
                           capture_output=True, text=True)
        assert p.returncode == 2, p.stdout
        out = json.loads(p.stdout)
        assert out["error"]["code"] == "BAD_NAME"
        assert not bad_dir.exists()
    finally:
        shutil.rmtree(bad_dir, ignore_errors=True)


def test_new_tool_refuses_to_clobber_existing_tool():
    tools_dir = Path(groundwork.__file__).parent / "tools"
    hello_dir = tools_dir / "hello"
    cli_before = (hello_dir / "cli.py").read_bytes()
    manifest_before = (hello_dir / "manifest.json").read_bytes()

    p = subprocess.run(["uv", "run", "groundwork", "new-tool", "hello",
                        "--purpose", "x"],
                       capture_output=True, text=True)
    assert p.returncode == 1, p.stdout
    out = json.loads(p.stdout)
    assert out["error"]["code"] == "EXISTS"

    assert (hello_dir / "cli.py").read_bytes() == cli_before
    assert (hello_dir / "manifest.json").read_bytes() == manifest_before
