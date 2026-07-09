from groundwork.tools.mutcheck.runner import check_file


def _write(tmp_path, src):
    p = tmp_path / "mod.py"
    p.write_text(src, encoding="utf-8", newline="\n")
    return p


def test_strong_tests_kill_every_mutant(tmp_path):
    p = _write(tmp_path, "def f(x):\n    return x < 10\n")
    # run_tests returns False (fail) iff the file no longer says 'x < 10'
    def run_tests():
        return "x < 10" in p.read_text(encoding="utf-8")
    out = check_file(p, {2}, run_tests)
    assert out["mutants_total"] == 1 and out["killed"] == 1 and out["survived"] == 0
    assert out["survivors"] == []
    # file restored to the original after the run
    assert p.read_text(encoding="utf-8") == "def f(x):\n    return x < 10\n"


def test_weak_tests_leave_survivors(tmp_path):
    p = _write(tmp_path, "def f(x):\n    return x < 10\n")
    def run_tests():
        return True                          # tests never fail -> mutant survives
    out = check_file(p, {2}, run_tests)
    assert out["survived"] == 1 and out["killed"] == 0
    assert out["survivors"][0]["line"] == 2


def test_budget_caps_mutants(tmp_path):
    p = _write(tmp_path, "def f(x):\n    return x<1 or x>2 or x==3 or x!=4\n")
    out = check_file(p, {2}, lambda: True, max_mutants=2)
    assert out["tested"] == 2 and out["budget_hit"] is True
    assert out["mutants_total"] > 2


def test_original_restored_even_if_run_tests_raises(tmp_path):
    original = "def f(x):\n    return x < 10\n"
    p = _write(tmp_path, original)
    calls = {"n": 0}
    def run_tests():
        calls["n"] += 1
        raise RuntimeError("boom")
    try:
        check_file(p, {2}, run_tests)
    except RuntimeError:
        pass
    assert p.read_text(encoding="utf-8") == original   # restored despite raise


def test_no_mutants_is_zero(tmp_path):
    p = _write(tmp_path, "def f(x):\n    return x\n")
    out = check_file(p, {2}, lambda: True)
    assert out["mutants_total"] == 0 and out["survivors"] == []
