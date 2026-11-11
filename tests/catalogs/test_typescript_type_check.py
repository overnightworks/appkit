import subprocess
from pathlib import Path

import pytest

from design.catalogs.catalog import Entry, Key, LanguageTag, SourceCatalog, TranslationCatalog
from design.catalogs.typescript import render, render_translation

REPOSITORY = Path(__file__).resolve().parent.parent.parent
CATALOG = SourceCatalog(
    language=LanguageTag("de"),
    entries=(Entry(key=Key("table.seatFree"), text="Frei"), Entry(key=Key("app.name"), text="Skat")),
)


def translation(*keys: str) -> TranslationCatalog:
    return TranslationCatalog(language=LanguageTag("pl"), entries=tuple(Entry(Key(key), "Tekst") for key in keys))


GAP_CATALOG = SourceCatalog(
    language=LanguageTag("de"),
    entries=(Entry(key=Key("chat.greeting"), text="Hallo {name}, du hast {count} Nachrichten"),),
)


def type_check(
    directory: Path, probe: str, target: str = "", catalog: SourceCatalog = CATALOG
) -> subprocess.CompletedProcess[str]:
    (directory / "de.ts").write_text(render(catalog), encoding="utf-8")
    (directory / "pl.ts").write_text(target, encoding="utf-8")
    (directory / "consumer.ts").write_text(probe, encoding="utf-8")
    return subprocess.run(
        [
            "pnpm",
            "exec",
            "tsc",
            "--noEmit",
            "--strict",
            "--ignoreConfig",
            "--target",
            "ES2022",
            "--module",
            "ESNext",
            "--moduleResolution",
            "bundler",
            "--skipLibCheck",
            str(directory / "consumer.ts"),
        ],
        cwd=REPOSITORY,
        capture_output=True,
        text=True,
        check=False,
    )


def test_a_consumer_using_catalog_keys_passes_tsc_strict(tmp_path):
    probe = (
        'import { words, type Key } from "./de";\n'
        'const key: Key = "table.seatFree";\n'
        'export const text: string = words[key] + words["app.name"];\n'
    )

    result = type_check(tmp_path, probe)

    assert result.returncode == 0, result.stdout


@pytest.mark.parametrize(
    "probe",
    [
        pytest.param('import type { Key } from "./de";\nexport const key: Key = "table.nope";\n', id="key type"),
        pytest.param('import { words } from "./de";\nexport const text = words["table.nope"];\n', id="lookup"),
    ],
)
def test_a_consumer_using_a_wrong_key_fails_tsc_strict(tmp_path, probe):
    result = type_check(tmp_path, probe)

    assert result.returncode != 0
    assert "table.nope" in result.stdout


TARGET_CONSUMER = 'import { words } from "./pl";\nexport const text: string = words["table.seatFree"];\n'


def test_a_target_module_with_every_key_of_the_source_passes_tsc_strict(tmp_path):
    target = render_translation(translation("table.seatFree", "app.name"), LanguageTag("de"))

    result = type_check(tmp_path, TARGET_CONSUMER, target)

    assert result.returncode == 0, result.stdout


@pytest.mark.parametrize(
    ("keys", "named"),
    [
        pytest.param(("table.seatFree",), "app.name", id="missing key"),
        pytest.param(("table.seatFree", "app.name", "table.nope"), "table.nope", id="extra key"),
    ],
)
def test_a_target_module_whose_keys_differ_from_the_sources_fails_tsc_strict(tmp_path, keys, named):
    target = render_translation(translation(*keys), LanguageTag("de"))

    result = type_check(tmp_path, TARGET_CONSUMER, target)

    assert result.returncode != 0
    assert "pl.ts" in result.stdout
    assert named in result.stdout


TARGET_GREETING = (
    'import { words } from "./pl";\nexport const text: string = words["chat.greeting"]({ name: "Eva", count: 3 });\n'
)


def gap_translation(text: str) -> str:
    catalog = TranslationCatalog(language=LanguageTag("pl"), entries=(Entry(Key("chat.greeting"), text),))
    return render_translation(catalog, LanguageTag("de"))


def greet(gaps: str) -> str:
    return f'import {{ words }} from "./de";\nexport const text: string = words["chat.greeting"]({gaps});\n'


def test_a_consumer_passing_every_gap_of_a_text_passes_tsc_strict(tmp_path):
    result = type_check(tmp_path, greet('{ name: "Eva", count: 3 }'), catalog=GAP_CATALOG)

    assert result.returncode == 0, result.stdout


@pytest.mark.parametrize(
    ("gaps", "named"),
    [
        pytest.param('{ name: "Eva" }', "count", id="missing gap"),
        pytest.param('{ name: "Eva", count: 3, other: "x" }', "other", id="extra gap"),
        pytest.param(
            "{ name: 1, count: 3 }", "'number' is not assignable to type 'string'", id="wrong type of a plain gap"
        ),
        pytest.param(
            '{ name: "Eva", count: "3" }',
            "'string' is not assignable to type 'number'",
            id="wrong type of the count gap",
        ),
    ],
)
def test_a_consumer_passing_the_wrong_gaps_fails_tsc_strict(tmp_path, gaps, named):
    result = type_check(tmp_path, greet(gaps), catalog=GAP_CATALOG)

    assert result.returncode != 0
    assert "consumer.ts" in result.stdout
    assert named in result.stdout


def test_a_target_module_with_the_gaps_of_the_source_passes_tsc_strict(tmp_path):
    target = gap_translation("{count} wiadomosci dla {name}")

    result = type_check(tmp_path, TARGET_GREETING, target, GAP_CATALOG)

    assert result.returncode == 0, result.stdout


def test_a_target_module_using_a_gap_the_source_lacks_fails_tsc_strict(tmp_path):
    target = gap_translation("{count} wiadomosci dla {name} {other}")

    result = type_check(tmp_path, TARGET_GREETING, target, GAP_CATALOG)

    assert result.returncode != 0
    assert "pl.ts" in result.stdout
    assert "other" in result.stdout
