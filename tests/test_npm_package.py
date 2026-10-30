import json
import subprocess
import tarfile
import tomllib
from pathlib import Path

import pytest

REPOSITORY = Path(__file__).resolve().parent.parent
STATIC = "src/appkit/static"
INSTALL_SCRIPTS = {"preinstall", "install", "postinstall", "prepare"}
COMPONENT_FILES = {
    "svelte-dist/index.js",
    "svelte-dist/index.d.ts",
    "svelte-dist/types.js",
    "svelte-dist/types.d.ts",
    "svelte-dist/SignInPage.svelte",
    "svelte-dist/SignInPage.svelte.d.ts",
}


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


def export_targets(exports):
    """Every file an exports map names, through nested conditions."""
    if isinstance(exports, str):
        return {exports}
    return set().union(*(export_targets(value) for value in exports.values()))


def test_tarball_holds_exactly_the_manifest_readme_licence_stylesheet_fonts_font_licences_and_component(tarball, font_files, licences):
    expected = {"package.json", "README.md", "LICENSE", f"{STATIC}/appkit.css"} | COMPONENT_FILES
    expected |= {f"{STATIC}/fonts/{name}" for name in font_files | licences}
    assert packed_files(tarball) == expected


def test_every_export_target_is_a_packed_file(tarball):
    exports = json.loads((tarball / "package.json").read_text())["exports"]
    assert exports
    for target in export_targets(exports):
        assert (tarball / target).is_file(), target


def test_every_url_in_the_packed_stylesheet_names_a_packed_font(tarball, font_files, stylesheet_urls):
    stylesheet = tarball / STATIC / "appkit.css"
    urls = stylesheet_urls(stylesheet)
    assert len(urls) == len(font_files)
    for url in urls:
        assert (stylesheet.parent / url).is_file(), url


def test_packed_stylesheet_is_byte_equal_to_the_source_stylesheet(tarball):
    source = REPOSITORY / STATIC / "appkit.css"
    assert (tarball / STATIC / "appkit.css").read_bytes() == source.read_bytes()


def test_manifest_is_private_and_exports_the_component_with_types_and_the_stylesheet_as_appkit_css(tarball):
    manifest = json.loads((tarball / "package.json").read_text())
    assert manifest["private"] is True
    exports = manifest["exports"]
    assert set(exports) == {".", "./appkit.css"}
    assert set(exports["."]) == {"types", "svelte"}
    assert exports["./appkit.css"] == f"./{STATIC}/appkit.css"


def test_package_version_equals_the_python_package_version(tarball):
    python_version = tomllib.loads((REPOSITORY / "pyproject.toml").read_text())["project"]["version"]
    assert json.loads((tarball / "package.json").read_text())["version"] == python_version


def test_package_has_only_svelte_as_a_peer_and_no_install_scripts(tarball):
    manifest = json.loads((tarball / "package.json").read_text())
    assert not {"dependencies", "optionalDependencies"} & manifest.keys()
    assert manifest["peerDependencies"] == {"svelte": "^5.0.0"}
    assert not INSTALL_SCRIPTS & manifest.get("scripts", {}).keys()
