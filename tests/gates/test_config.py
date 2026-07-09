from groundwork.tools.gates.config import DEFAULTS, load_config


def test_missing_config_yields_defaults(tmp_path):
    cfg = load_config(tmp_path)
    assert cfg == DEFAULTS
    assert cfg["fail_mode"] == "open"
    assert cfg["secrets"]["enabled"] is True
    assert cfg["paths"]["ask"] == ["**/.env", "**/.env.*"]


def test_partial_config_merges_over_defaults(tmp_path):
    d = tmp_path / ".groundwork"
    d.mkdir()
    (d / "gates.yaml").write_text(
        "fail_mode: closed\npaths:\n  deny: ['**/prod.yaml']\n",
        encoding="utf-8")
    cfg = load_config(tmp_path)
    assert cfg["fail_mode"] == "closed"
    assert cfg["paths"]["deny"] == ["**/prod.yaml"]
    assert cfg["paths"]["ask"] == ["**/.env", "**/.env.*"]   # default survives
    assert cfg["secrets"]["enabled"] is True                  # untouched section


def test_malformed_yaml_falls_back_to_defaults_armed(tmp_path):
    d = tmp_path / ".groundwork"
    d.mkdir()
    (d / "gates.yaml").write_text("fail_mode: [unclosed", encoding="utf-8")
    cfg = load_config(tmp_path)
    assert cfg["secrets"]["enabled"] is True    # gates stay armed
    assert "config_error" in cfg


def test_non_mapping_yaml_falls_back(tmp_path):
    d = tmp_path / ".groundwork"
    d.mkdir()
    (d / "gates.yaml").write_text("- just\n- a\n- list\n", encoding="utf-8")
    cfg = load_config(tmp_path)
    assert cfg["fail_mode"] == "open" and "config_error" in cfg
