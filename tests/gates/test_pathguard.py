from groundwork.tools.gates.pathguard import check_path


def test_deny_glob_matches_windows_and_posix_separators():
    rule = check_path("C:\\Users\\x\\.ssh\\id_rsa", deny=("**/.ssh/*",), ask=())
    assert rule == {"action": "deny", "glob": "**/.ssh/*"}


def test_ask_glob_default_env():
    assert check_path("project/.env", deny=(), ask=("**/.env", "**/.env.*")) \
        == {"action": "ask", "glob": "**/.env"}
    assert check_path("project/.env.local", deny=(), ask=("**/.env", "**/.env.*")) \
        == {"action": "ask", "glob": "**/.env.*"}


def test_deny_wins_over_ask():
    out = check_path("a/.env", deny=("**/.env",), ask=("**/.env",))
    assert out["action"] == "deny"


def test_unmatched_path_is_none():
    assert check_path("src/app.py", deny=("**/.ssh/*",), ask=("**/.env",)) is None
