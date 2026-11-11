import configparser
import email
import functools
import hashlib
import http.server
import re
import subprocess
import sys
import threading
import tomllib
import zipfile
from pathlib import Path

import pytest

from design.catalogs.command import MISSING_EXTRA

REPOSITORY = Path(__file__).resolve().parent.parent
FAMILY_TOKENS = {
    "--bg",
    "--bg-deep",
    "--surface",
    "--surface-hover",
    "--border",
    "--text",
    "--text-muted",
    "--card-bg",
    "--header-bg",
    "--font-display",
    "--font-body",
    "--ok",
    "--ok-soft",
    "--busy",
    "--busy-soft",
    "--fail",
    "--fail-soft",
}


@pytest.fixture(scope="module")
def installed_package(tmp_path_factory):
    """The package as a consumer gets it: built into a wheel, unpacked, imported from there."""
    root = tmp_path_factory.mktemp("wheel")
    subprocess.run(
        ["uv", "build", "--wheel", "--out-dir", str(root), str(REPOSITORY)],
        check=True,
        capture_output=True,
    )
    (wheel,) = root.glob("*.whl")
    unpacked = root / "site"
    zipfile.ZipFile(wheel).extractall(unpacked)
    probe = (
        "import sys; sys.path.insert(0, sys.argv[1]);"
        "from importlib.resources import files;"
        "print(files('design') / 'static')"
    )
    static = subprocess.run(
        [sys.executable, "-I", "-c", probe, str(unpacked)],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return wheel, Path(static)


def test_wheel_top_level_is_the_design_package_and_its_dist_info(installed_package):
    wheel, _ = installed_package
    top_level = {name.split("/")[0] for name in zipfile.ZipFile(wheel).namelist()}
    assert top_level == {"design", f"{wheel.name.split('-py3')[0]}.dist-info"}


def test_design_resolves_inside_the_unpacked_wheel(installed_package):
    wheel, static = installed_package
    assert static.is_relative_to(wheel.parent / "site")


def test_wheel_holds_the_stylesheet_the_fonts_and_both_licences(installed_package, font_files, licences):
    _, static = installed_package
    assert (static / "design.css").is_file()
    assert {path.name for path in (static / "fonts").iterdir()} == font_files | licences


def test_wheel_stylesheet_is_byte_equal_to_the_source_stylesheet(installed_package):
    _, static = installed_package
    source = REPOSITORY / "src" / "design" / "static" / "design.css"
    assert (static / "design.css").read_bytes() == source.read_bytes()


def test_wheel_holds_only_data_and_no_tests(installed_package):
    wheel, _ = installed_package
    names = zipfile.ZipFile(wheel).namelist()
    assert not [name for name in names if name.startswith("tests")]


def test_wheel_holds_no_svelte_component_and_no_component_build(installed_package):
    wheel, _ = installed_package
    names = zipfile.ZipFile(wheel).namelist()
    assert not [name for name in names if name.endswith(".svelte") or "svelte-dist" in name]


def test_every_url_in_the_stylesheet_names_a_font_in_the_wheel(installed_package, font_files, stylesheet_urls):
    _, static = installed_package
    urls = stylesheet_urls(static / "design.css")
    assert len(urls) == len(font_files)
    for url in urls:
        assert (static / url).is_file(), url


def test_token_list_holds_exactly_the_properties_the_stylesheet_defines(installed_package):
    _, static = installed_package
    listing = subprocess.run(
        [str(REPOSITORY / "scripts" / "list_tokens"), str(static / "design.css")],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split()
    assert listing == sorted(FAMILY_TOKENS)


def top_level_rules(stylesheet):
    """Selector to body of each top-level rule; raises when braces do not balance."""
    rules, depth, selector_start, body_start, selector = {}, 0, 0, 0, ""
    for index, character in enumerate(stylesheet):
        if character == "{":
            if depth == 0:
                selector = stylesheet[selector_start:index].strip()
                body_start = index + 1
            depth += 1
        elif character == "}":
            depth -= 1
            assert depth >= 0, "closing brace without opening brace"
            if depth == 0:
                rules.setdefault(selector, []).append(stylesheet[body_start:index])
                selector_start = index + 1
    assert depth == 0, "unclosed rule"
    return rules


def test_light_is_the_no_choice_case_and_dark_follows_the_device_or_the_attribute(installed_package):
    _, static = installed_package
    rules = top_level_rules((static / "design.css").read_text())
    (device_dark,) = rules["@media (prefers-color-scheme: dark)"]
    assert ":root:not([data-theme='light'])" in device_dark
    bodies = {
        ("light", "no attribute"): rules[":root"][0],
        ("dark", "attribute"): rules[":root[data-theme='dark']"][0],
        ("dark", "device"): device_dark,
    }
    for (scheme, case), body in bodies.items():
        assert re.search(r"^\s+--bg:", body, re.MULTILINE), case
        assert re.search(rf"^\s+color-scheme: {scheme};", body, re.MULTILINE), case
    assert "[data-theme='light']" not in rules


LIGHT_STATE_COLOURS = {
    "ok": "#1e7a1e",
    "ok-soft": "#e0f5e0",
    "busy": "#9a6200",
    "busy-soft": "#fef3e0",
    "fail": "#c02020",
    "fail-soft": "#fde8e8",
}
DARK_STATE_COLOURS = {
    "ok": "#44aa44",
    "ok-soft": "#1a3a1a",
    "busy": "#f0a030",
    "busy-soft": "#2a1f10",
    "fail": "#ff4444",
    "fail-soft": "#3a1a1a",
}


def test_state_tokens_carry_the_pictures_colours_in_light_and_both_dark_branches(installed_package):
    _, static = installed_package
    rules = top_level_rules((static / "design.css").read_text())
    (device_dark,) = rules["@media (prefers-color-scheme: dark)"]
    bodies = {
        "light": (rules[":root"][0], LIGHT_STATE_COLOURS),
        "dark attribute": (rules[":root[data-theme='dark']"][0], DARK_STATE_COLOURS),
        "dark device": (device_dark, DARK_STATE_COLOURS),
    }
    for case, (body, expected) in bodies.items():
        for token, colour in expected.items():
            assert re.search(rf"^\s+--{token}: {colour};", body, re.MULTILINE), (case, token)


def test_wheel_installs_the_declared_commands_and_offers_the_declared_extras(installed_package):
    wheel, _ = installed_package
    archive = zipfile.ZipFile(wheel)
    (entry_points_name,) = [name for name in archive.namelist() if name.endswith(".dist-info/entry_points.txt")]
    (metadata_name,) = [name for name in archive.namelist() if name.endswith(".dist-info/METADATA")]
    entry_points = configparser.ConfigParser()
    entry_points.read_string(archive.read(entry_points_name).decode())
    metadata = email.message_from_string(archive.read(metadata_name).decode())
    declared = tomllib.loads((REPOSITORY / "pyproject.toml").read_text())["project"]

    assert dict(entry_points["console_scripts"]) == declared["scripts"]
    assert metadata.get_all("Provides-Extra") == list(declared["optional-dependencies"])
    shipped = metadata.get_all("Requires-Dist")
    for extra, requirements in declared["optional-dependencies"].items():
        for requirement in requirements:
            name = re.match(r"[A-Za-z0-9_.-]+", requirement)[0].lower()
            assert any(
                line.lower().startswith(name) and re.search(rf"extra == ['\"]{extra}['\"]", line) for line in shipped
            ), (extra, requirement)
    assert len(shipped) == len(declared["dependencies"]) + sum(
        len(requirements) for requirements in declared["optional-dependencies"].values()
    )


@pytest.fixture
def run_declared_command(installed_package, tmp_path):
    """Runs the declared console script from the unpacked wheel in an empty project; only the wheel is importable."""
    wheel, _ = installed_package
    module, function = tomllib.loads((REPOSITORY / "pyproject.toml").read_text())["project"]["scripts"][
        "design-catalogs"
    ].split(":")
    probe = (
        "import importlib, sys; sys.path[:0] = sys.argv[1:];"
        f"sys.exit(getattr(importlib.import_module({module!r}), {function!r})([]))"
    )

    def run(*extra_path: Path) -> subprocess.CompletedProcess[str]:
        # -S keeps the environment's site-packages, and so Babel, out of the import path
        return subprocess.run(
            [sys.executable, "-I", "-S", "-c", probe, str(wheel.parent / "site"), *map(str, extra_path)],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            check=False,
        )

    return run


def test_declared_command_without_babel_fails_with_a_sentence_naming_the_extra(run_declared_command):
    result = run_declared_command()

    assert result.returncode != 0
    assert MISSING_EXTRA in result.stderr


def test_declared_command_does_not_call_a_broken_babel_a_missing_extra(run_declared_command, tmp_path):
    broken = tmp_path / "broken"
    (broken / "babel").mkdir(parents=True)
    (broken / "babel" / "__init__.py").write_text("import a_dependency_babel_needs\n")

    result = run_declared_command(broken)

    assert result.returncode != 0
    assert "a_dependency_babel_needs" in result.stderr
    assert MISSING_EXTRA not in result.stderr


def test_wheel_holds_the_catalogs_package(installed_package):
    wheel, _ = installed_package
    names = set(zipfile.ZipFile(wheel).namelist())
    assert {
        f"design/catalogs/{name}.py"
        for name in ("__init__", "catalog", "command", "declaration", "po_file", "python_module", "sync", "typescript")
    } <= names


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):  # noqa: A002 - the base class's parameter name
        """Serves without writing a line per request."""


@pytest.fixture
def wheel_url(installed_package):
    """The built wheel on a local HTTP server, where a consumer's pin points to a release asset."""
    wheel, _ = installed_package
    handler = functools.partial(QuietHandler, directory=wheel.parent)
    with http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        yield f"http://127.0.0.1:{server.server_port}/{wheel.name}"
        server.shutdown()
        thread.join()


@pytest.fixture
def install_pinned(installed_package, wheel_url, tmp_path):
    """Installs the wheel the way an app pins it: by URL with a `#sha256=` fragment."""
    wheel, _ = installed_package

    def install(sha256):
        return subprocess.run(
            [
                "uv",
                "pip",
                "install",
                "--cache-dir",
                str(tmp_path / "cache"),
                "--target",
                str(tmp_path / "site"),
                f"overnightworks-design @ {wheel_url}#sha256={sha256}",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    return install, hashlib.sha256(wheel.read_bytes()).hexdigest()


def test_install_by_url_with_the_wheels_hash_succeeds(install_pinned):
    install, wheel_hash = install_pinned

    result = install(wheel_hash)

    assert result.returncode == 0, result.stderr


def test_install_by_url_with_another_hash_fails_naming_both_hashes(install_pinned):
    install, wheel_hash = install_pinned
    wrong_hash = "0" * 64

    result = install(wrong_hash)

    assert result.returncode != 0
    assert wrong_hash in result.stderr
    assert wheel_hash in result.stderr
