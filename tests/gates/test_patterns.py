from groundwork.tools.gates.patterns import scan_text


def test_known_token_shapes_are_caught_with_named_rules():
    cases = {
        "aws-access-key-id": "AKIAIOSFODNN7EXAMPLE",
        "github-token": "ghp_" + "a1B2" * 9,
        "slack-token": "xoxb-1234567890-abcdefghijklmnop",
        "stripe-live-key": "sk_live_" + "a1B2c3D4" * 3,
        "anthropic-key": "sk-ant-" + "a1B2c3D4e5F6" * 2,
        "google-api-key": "AIza" + "a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P",
        "private-key-block": "-----BEGIN RSA PRIVATE KEY-----",
    }
    for rule, needle in cases.items():
        findings = scan_text(f"value = '{needle}'\n")
        assert any(f["rule"] == rule for f in findings), (rule, findings)


def test_matches_are_redacted_in_findings():
    findings = scan_text("k = 'AKIAIOSFODNN7EXAMPLE'\n")
    hit = [f for f in findings if f["rule"] == "aws-access-key-id"][0]
    assert "AKIAIOSFODNN7EXAMPLE" not in str(hit)
    assert hit["match"].endswith("…") and len(hit["match"]) <= 9
    assert hit["line"] == 1


def test_generic_password_assignment_is_ask_not_deny():
    findings = scan_text('password = "correct-horse-battery-staple-9"\n')
    hit = [f for f in findings if f["rule"] == "generic-credential-assignment"]
    assert hit and hit[0]["action"] == "ask"


def test_private_key_block_is_deny():
    findings = scan_text("-----BEGIN OPENSSH PRIVATE KEY-----\n")
    assert any(f["rule"] == "private-key-block" and f["action"] == "deny"
               for f in findings)


def test_entropy_hit_is_always_ask():
    # a bare high-entropy blob NOT caught by a named rule (no credential
    # keyword, no known prefix) — proves the entropy hint fires on its own
    # and is always ask, never deny.
    blob = "digest = 'Zk9xJ2mQ7vRt4Wp8Ns6Lc3Hd5Fg1Ba0YeUiOq'\n"
    findings = scan_text(blob)
    ent = [f for f in findings if f["rule"] == "entropy"]
    assert ent and all(f["action"] == "ask" for f in ent)


def test_plain_prose_and_code_are_clean():
    assert scan_text("def add(a, b):\n    return a + b\n") == []
    assert scan_text("The quick brown fox jumps over the lazy dog.\n") == []


def test_lockfiles_and_allow_globs_are_exempt():
    blob = "sha256 = 'Zk9xJ2mQ7vRt4Wp8Ns6Lc3Hd5Fg1Ba0YeUiOq'\n"
    assert scan_text(blob, path="uv.lock") == []
    assert scan_text(blob, path="pkg/package-lock.json") == []
    assert scan_text(blob, path="fixtures/blob.txt",
                     allow_files=("fixtures/*",)) == []
