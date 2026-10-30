import re
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

REPOSITORY = Path(__file__).resolve().parent.parent
FAMILY_TOKENS = {
    "--bg", "--bg-deep", "--surface", "--surface-hover", "--border", "--text",
    "--text-muted", "--card-bg", "--header-bg", "--font-display", "--font-body",
    "--ok", "--ok-soft", "--busy", "--busy-soft", "--fail", "--fail-soft",
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
        "print(files('appkit') / 'static')"
    )
    static = subprocess.run(
        [sys.executable, "-I", "-c", probe, str(unpacked)],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return wheel, Path(static)


def test_wheel_holds_the_stylesheet_the_fonts_and_both_licences(installed_package, font_files, licences):
    _, static = installed_package
    assert (static / "appkit.css").is_file()
    assert {path.name for path in (static / "fonts").iterdir()} == font_files | licences


def test_wheel_stylesheet_is_byte_equal_to_the_source_stylesheet(installed_package):
    _, static = installed_package
    source = REPOSITORY / "src" / "appkit" / "static" / "appkit.css"
    assert (static / "appkit.css").read_bytes() == source.read_bytes()


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
    urls = stylesheet_urls(static / "appkit.css")
    assert len(urls) == len(font_files)
    for url in urls:
        assert (static / url).is_file(), url


def test_token_list_holds_exactly_the_properties_the_stylesheet_defines(installed_package):
    _, static = installed_package
    listing = subprocess.run(
        [str(REPOSITORY / "scripts" / "list_tokens"), str(static / "appkit.css")],
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
    rules = top_level_rules((static / "appkit.css").read_text())
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
    "ok": "#1e7a1e", "ok-soft": "#e0f5e0", "busy": "#9a6200",
    "busy-soft": "#fef3e0", "fail": "#c02020", "fail-soft": "#fde8e8",
}
DARK_STATE_COLOURS = {
    "ok": "#44aa44", "ok-soft": "#1a3a1a", "busy": "#f0a030",
    "busy-soft": "#2a1f10", "fail": "#ff4444", "fail-soft": "#3a1a1a",
}


def test_state_tokens_carry_the_pictures_colours_in_light_and_both_dark_branches(installed_package):
    _, static = installed_package
    rules = top_level_rules((static / "appkit.css").read_text())
    (device_dark,) = rules["@media (prefers-color-scheme: dark)"]
    bodies = {
        "light": (rules[":root"][0], LIGHT_STATE_COLOURS),
        "dark attribute": (rules[":root[data-theme='dark']"][0], DARK_STATE_COLOURS),
        "dark device": (device_dark, DARK_STATE_COLOURS),
    }
    for case, (body, expected) in bodies.items():
        for token, colour in expected.items():
            assert re.search(rf"^\s+--{token}: {colour};", body, re.MULTILINE), (case, token)
