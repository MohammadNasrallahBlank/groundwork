from pathlib import Path

from groundwork.tools.depsurface.envresolve import find_site_packages, package_version

FIXTURE_SP = Path("tests/fixtures/sitepkgs").resolve()


def test_find_site_packages_windows_layout(tmp_path):
    sp = tmp_path / ".venv" / "Lib" / "site-packages"
    sp.mkdir(parents=True)
    assert find_site_packages(tmp_path) == sp


def test_find_site_packages_posix_layout(tmp_path):
    sp = tmp_path / ".venv" / "lib" / "python3.12" / "site-packages"
    sp.mkdir(parents=True)
    assert find_site_packages(tmp_path) == sp


def test_find_site_packages_none_when_no_venv(tmp_path):
    assert find_site_packages(tmp_path) is None


def test_find_site_packages_picks_highest_python_minor(tmp_path):
    # "python3.10" < "python3.9" lexicographically (string compare on the
    # minor digits), and "python3.10" < "python3.12" too — a plain sorted()
    # walk returns the lexicographically-first directory, not the highest
    # minor version. Use 10 and 12 so the lexicographic bug picks 3.10
    # (wrong) instead of the correct 3.12.
    for minor in ("10", "12"):
        (tmp_path / ".venv" / "lib" / f"python3.{minor}" / "site-packages").mkdir(parents=True)
    got = find_site_packages(tmp_path)
    assert got == tmp_path / ".venv" / "lib" / "python3.12" / "site-packages"


def test_package_version_from_dist_info():
    assert package_version(FIXTURE_SP, "demopkg") == "1.2.3"


def test_package_version_unknown_package():
    assert package_version(FIXTURE_SP, "nosuchpkg") is None
