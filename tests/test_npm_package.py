import json
import re
import subprocess
import tarfile
import tomllib
from pathlib import Path

import pytest

REPOSITORY = Path(__file__).resolve().parent.parent
STATIC = "src/appkit/static"
FONT_FILES = {
    f"{family}-{subset}-{weight}-normal.woff2"
    for family, weights in (("oswald", (400, 700)), ("open-sans", (400, 600)))
    for weight in weights
    for subset in ("latin", "latin-ext")
}
LICENCES = {"oswald-LICENSE", "open-sans-LICENSE"}
INSTALL_SCRIPTS = {"preinstall", "install", "postinstall", "prepare"}


@pytest.fixture(scope="module")
def tarball(tmp_path_factory):
    """The package as a consumer gets it: packed by pnpm, read back from the tarball."""
    root = tmp_path_factory.mktemp("npm")
    subprocess.run(
        ["pnpm", "pack", "--pack-destination", str(root)],
        cwd=REPOSITORY,
        check=True,
        capture_output=True,
    )
    (archive,) = root.glob("*.tgz")
    unpacked = root / "unpacked"
    with tarfile.open(archive) as opened:
        opened.extractall(unpacked, filter="data")
    return unpacked / "package"


def packed_files(package):
    return {path.relative_to(package).as_posix() for path in package.rglob("*") if path.is_file()}


def test_tarball_holds_exactly_the_manifest_readme_licence_stylesheet_fonts_and_font_licences(tarball):
    expected = {"package.json", "README.md", "LICENSE", f"{STATIC}/appkit.css"}
    expected |= {f"{STATIC}/fonts/{name}" for name in FONT_FILES | LICENCES}
    assert packed_files(tarball) == expected


def test_every_export_target_is_a_packed_file(tarball):
    exports = json.loads((tarball / "package.json").read_text())["exports"]
    assert exports
    for target in exports.values():
        assert (tarball / target).is_file(), target


def test_every_url_in_the_packed_stylesheet_names_a_packed_font(tarball):
    stylesheet = tarball / STATIC / "appkit.css"
    urls = re.findall(r"url\('([^']+)'\)", stylesheet.read_text())
    assert len(urls) == len(FONT_FILES)
    for url in urls:
        assert (stylesheet.parent / url).is_file(), url


def test_packed_stylesheet_is_byte_equal_to_the_source_stylesheet(tarball):
    source = REPOSITORY / STATIC / "appkit.css"
    assert (tarball / STATIC / "appkit.css").read_bytes() == source.read_bytes()


def test_manifest_is_private_and_exports_the_stylesheet_as_appkit_css(tarball):
    manifest = json.loads((tarball / "package.json").read_text())
    assert manifest["private"] is True
    assert manifest["exports"] == {"./appkit.css": f"./{STATIC}/appkit.css"}


def test_package_version_equals_the_python_package_version(tarball):
    python_version = tomllib.loads((REPOSITORY / "pyproject.toml").read_text())["project"]["version"]
    assert json.loads((tarball / "package.json").read_text())["version"] == python_version


def test_package_has_no_dependencies_and_no_install_scripts(tarball):
    manifest = json.loads((tarball / "package.json").read_text())
    assert not {"dependencies", "peerDependencies"} & manifest.keys()
    assert not INSTALL_SCRIPTS & manifest.get("scripts", {}).keys()
