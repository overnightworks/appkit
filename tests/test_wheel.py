import re
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

REPOSITORY = Path(__file__).resolve().parent.parent
FONT_FILES = {
    f"{family}-{subset}-{weight}-normal.woff2"
    for family, weights in (("oswald", (400, 700)), ("open-sans", (400, 600)))
    for weight in weights
    for subset in ("latin", "latin-ext")
}
LICENCES = {"oswald-LICENSE", "open-sans-LICENSE"}
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


def test_wheel_holds_the_stylesheet_the_fonts_and_both_licences(installed_package):
    _, static = installed_package
    assert (static / "appkit.css").is_file()
    assert {path.name for path in (static / "fonts").iterdir()} == FONT_FILES | LICENCES


def test_wheel_holds_only_data_and_no_tests(installed_package):
    wheel, _ = installed_package
    names = zipfile.ZipFile(wheel).namelist()
    assert not [name for name in names if name.startswith("tests")]


def test_every_url_in_the_stylesheet_names_a_font_in_the_wheel(installed_package):
    _, static = installed_package
    urls = re.findall(r"url\('([^']+)'\)", (static / "appkit.css").read_text())
    assert len(urls) == len(FONT_FILES)
    for url in urls:
        assert (static / url).is_file(), url


def test_token_list_holds_exactly_the_properties_the_stylesheet_defines(installed_package):
    _, static = installed_package
    listing = subprocess.run(
        [str(REPOSITORY / "scripts" / "token-list"), str(static / "appkit.css")],
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
        for state in ("ok", "busy", "fail"):
            assert f"--{state}:" in body and f"--{state}-soft:" in body, (case, state)
    assert "[data-theme='light']" not in rules
