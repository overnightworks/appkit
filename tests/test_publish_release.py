import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPOSITORY = Path(__file__).resolve().parent.parent
RELEASED_VERSION = "9.9.9"
TAG = f"v{RELEASED_VERSION}"
BORROWED_TOOLS = (
    "bash", "env", "git", "sed", "ls", "cat", "cut", "tr", "grep", "sort", "mktemp",
    "rm", "dirname", "sha256sum", "openssl", "base64",
)
# Each fake records its arguments in the file named by RECORD and fails on request.
FAKE_GH = """#!/usr/bin/env bash
echo "gh $*" >>"$RECORD"
[[ $1 == release && -n ${FAIL_RELEASE:-} ]] && exit 1
exit 0
"""
FAKE_UV = """#!/usr/bin/env bash
echo "uv $*" >>"$RECORD"
out=$4
echo wheel >"$out/overnightworks_appkit-9.9.9-py3-none-any.whl"
"""
FAKE_PNPM = """#!/usr/bin/env bash
echo "pnpm $*" >>"$RECORD"
[[ -n ${FAIL_PACK:-} ]] && exit 1
echo tarball >"$3/overnightworks-appkit-9.9.9.tgz"
"""
FAKE_FAILING_OPENSSL = """#!/usr/bin/env bash
exit 1
"""


def write_executable(path, text):
    path.write_text(text)
    path.chmod(0o755)


def git(directory, *arguments):
    return subprocess.run(
        ["git", "-C", str(directory), *arguments], check=True, capture_output=True, text=True
    ).stdout


class Release:
    """A throwaway clone of main with a local bare origin and fake gh, uv and pnpm."""

    def __init__(self, root):
        self.root = root
        self.record = root / "record.txt"
        self.record.touch()
        self.origin = root / "origin.git"
        self.clone = root / "clone"
        self.fakes = root / "fakes"
        self.tools = root / "tools"
        self.fakes.mkdir()
        self.tools.mkdir()
        for tool in BORROWED_TOOLS:
            (self.tools / tool).symlink_to(shutil.which(tool))
        write_executable(self.fakes / "gh", FAKE_GH)
        write_executable(self.fakes / "uv", FAKE_UV)
        self.install_pnpm()
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(self.origin)], check=True)
        self.populate_clone()

    def install_pnpm(self):
        write_executable(self.fakes / "pnpm", FAKE_PNPM)

    def populate_clone(self):
        (self.clone / "scripts").mkdir(parents=True)
        (self.clone / "src/appkit/static").mkdir(parents=True)
        shutil.copy(REPOSITORY / "scripts/publish_release", self.clone / "scripts")
        shutil.copy(REPOSITORY / "scripts/list_tokens", self.clone / "scripts")
        shutil.copy(REPOSITORY / "src/appkit/static/appkit.css", self.clone / "src/appkit/static")
        (self.clone / "ui-style.css").write_text("/* frozen */\n")
        self.write_versions(RELEASED_VERSION, RELEASED_VERSION)
        git(self.clone, "init", "-q", "-b", "main")
        git(self.clone, "remote", "add", "origin", str(self.origin))
        git(self.clone, "add", "-A")
        git(self.clone, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "release candidate")
        git(self.clone, "push", "-q", "origin", "main")

    def write_versions(self, python_version, npm_version):
        (self.clone / "pyproject.toml").write_text(f'[project]\nversion = "{python_version}"\n')
        (self.clone / "package.json").write_text(f'{{\n  "version": "{npm_version}",\n  "private": true\n}}\n')

    def commit_versions(self, python_version, npm_version):
        self.write_versions(python_version, npm_version)
        git(self.clone, "add", "-A")
        git(self.clone, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "versions")
        git(self.clone, "push", "-q", "origin", "main")

    def publish(self, **environment):
        path = f"{self.fakes}:{self.tools}"
        return subprocess.run(
            [str(self.clone / "scripts/publish_release"), TAG],
            cwd=self.clone,
            capture_output=True,
            text=True,
            env={"PATH": path, "RECORD": str(self.record), "HOME": str(self.root), "TMPDIR": str(self.root), **environment},
        )

    def calls(self, program):
        return [line for line in self.record.read_text().splitlines() if line.startswith(program + " ")]

    def local_tags(self):
        return git(self.clone, "tag").split()

    def origin_tags(self):
        return git(self.origin, "tag").split()


@pytest.fixture
def release(tmp_path):
    return Release(tmp_path)


def test_a_good_release_pushes_the_tag_attaches_four_assets_and_prints_both_hashes(release):
    result = release.publish()
    assert result.returncode == 0, result.stderr
    assert release.origin_tags() == [TAG]
    (create,) = release.calls("gh release create")
    assert re.search(
        rf"overnightworks_appkit-9\.9\.9-py3-none-any\.whl .*overnightworks-appkit-9\.9\.9\.tgz "
        rf"ui-style\.css .*appkit-9\.9\.9-tokens\.txt",
        create,
    )
    assert re.search(r"^wheel sha256: [0-9a-f]{64}$", result.stdout, re.MULTILINE)
    assert re.search(r"^tarball integrity: sha512-[A-Za-z0-9+/]{86}==$", result.stdout, re.MULTILINE)


def test_a_package_json_version_that_differs_from_the_tag_refuses_without_a_tag(release):
    release.commit_versions(RELEASED_VERSION, "9.9.8")
    result = release.publish()
    assert result.returncode != 0
    assert "package.json version" in result.stderr
    assert release.local_tags() == [] and release.origin_tags() == []


def test_a_missing_pnpm_refuses_without_a_tag(release):
    (release.fakes / "pnpm").unlink()
    result = release.publish()
    assert result.returncode != 0
    assert "pnpm is missing" in result.stderr
    assert release.local_tags() == [] and release.origin_tags() == []


def test_a_failing_pnpm_pack_refuses_without_a_tag(release):
    result = release.publish(FAIL_PACK="1")
    assert result.returncode != 0
    assert "pnpm pack failed" in result.stderr
    assert release.local_tags() == [] and release.origin_tags() == []


def test_a_failing_upload_after_the_tag_names_the_rerun_and_keeps_both_staged_files(release):
    result = release.publish(FAIL_RELEASE="1")
    assert result.returncode != 0
    assert release.origin_tags() == [TAG]
    rerun = re.search(r"run: gh release create \S+ (\S+\.whl) (\S+\.tgz) ", result.stderr)
    assert rerun, result.stderr
    assert all(Path(path).is_file() for path in rerun.groups())


def test_a_failing_digest_exits_nonzero_without_printing_the_tarball_integrity(release):
    write_executable(release.fakes / "openssl", FAKE_FAILING_OPENSSL)
    result = release.publish()
    assert result.returncode != 0
    assert "tarball integrity could not be computed" in result.stderr
    assert "tarball integrity: sha512-" not in result.stdout
