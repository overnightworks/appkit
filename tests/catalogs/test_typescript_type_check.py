import subprocess
from pathlib import Path

import pytest

from design.catalogs.catalog import Entry, Key, LanguageTag, SourceCatalog, TranslationCatalog
from design.catalogs.typescript import render, render_loader, render_translation

REPOSITORY = Path(__file__).resolve().parent.parent.parent
CATALOG = SourceCatalog(
    language=LanguageTag("de"),
    entries=(Entry(key=Key("table.seatFree"), text="Frei"), Entry(key=Key("app.name"), text="Skat")),
)


def translation(*keys: str) -> TranslationCatalog:
    return TranslationCatalog(language=LanguageTag("pl"), entries=tuple(Entry(Key(key), "Tekst") for key in keys))


def type_check(
    directory: Path, probe: str, target: str = "", catalog: SourceCatalog = CATALOG
) -> subprocess.CompletedProcess[str]:
    (directory / "de.ts").write_text(render(catalog), encoding="utf-8")
    (directory / "pl.ts").write_text(target, encoding="utf-8")
    (directory / "index.ts").write_text(render_loader(catalog.language, (LanguageTag("pl"),)), encoding="utf-8")
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


@pytest.fixture
def gap_catalog():
    return SourceCatalog(
        language=LanguageTag("de"),
        entries=(Entry(key=Key("chat.greeting"), text="Hallo {name}, du hast {count} Nachrichten"),),
    )


@pytest.fixture
def target_greeting():
    return greet_from("pl", '{ name: "Eva", count: 3 }')


def gap_translation(text: str) -> str:
    catalog = TranslationCatalog(language=LanguageTag("pl"), entries=(Entry(Key("chat.greeting"), text),))
    return render_translation(catalog, LanguageTag("de"))


def greet_from(module: str, gaps: str) -> str:
    return f'import {{ words }} from "./{module}";\nexport const text: string = words["chat.greeting"]({gaps});\n'


def greet(gaps: str) -> str:
    return greet_from("de", gaps)


def test_a_consumer_passing_every_gap_of_a_text_passes_tsc_strict(tmp_path, gap_catalog):
    result = type_check(tmp_path, greet('{ name: "Eva", count: 3 }'), catalog=gap_catalog)

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
def test_a_consumer_passing_the_wrong_gaps_fails_tsc_strict(tmp_path, gaps, named, gap_catalog):
    result = type_check(tmp_path, greet(gaps), catalog=gap_catalog)

    assert result.returncode != 0
    assert "consumer.ts" in result.stdout
    assert named in result.stdout


def test_a_target_module_with_the_gaps_of_the_source_passes_tsc_strict(tmp_path, gap_catalog, target_greeting):
    target = gap_translation("{count} wiadomosci dla {name}")

    result = type_check(tmp_path, target_greeting, target, gap_catalog)

    assert result.returncode == 0, result.stdout


@pytest.mark.parametrize(
    ("text", "named"),
    [
        pytest.param("{count} wiadomosci dla {name} {other}", "other", id="gap the source lacks"),
        pytest.param("wiadomosci dla {name}", "count", id="dropped gap of the source"),
    ],
)
def test_a_target_module_whose_gaps_differ_from_the_sources_fails_tsc_strict(
    tmp_path, gap_catalog, target_greeting, text, named
):
    result = type_check(tmp_path, target_greeting, gap_translation(text), gap_catalog)

    assert result.returncode != 0
    assert "pl.ts" in result.stdout
    assert named in result.stdout


@pytest.mark.parametrize("module", [pytest.param("de", id="source"), pytest.param("pl", id="target")])
def test_a_consumer_assigning_to_the_words_of_a_module_fails_tsc_strict(tmp_path, module):
    target = render_translation(translation("table.seatFree", "app.name"), LanguageTag("de"))
    probe = f'import {{ words }} from "./{module}";\nwords["app.name"] = "replacement";\n'

    result = type_check(tmp_path, probe, target)

    assert result.returncode != 0
    assert "consumer.ts" in result.stdout
    assert "read-only" in result.stdout


@pytest.fixture
def family_catalog():
    return SourceCatalog(
        language=LanguageTag("de"),
        entries=(
            Entry(key=Key("table.seats.one"), text="{name} hat {count} Platz"),
            Entry(key=Key("table.seats.other"), text="{name} hat {count} Plätze"),
        ),
    )


def seats(arguments: str, module: str = "de") -> str:
    return f'import {{ words }} from "./{module}";\nexport const text: string = words["table.seats"]({arguments});\n'


def test_a_consumer_passing_the_count_and_the_gaps_of_a_family_passes_tsc_strict(tmp_path, family_catalog):
    result = type_check(tmp_path, seats('3, { name: "Eva" }'), catalog=family_catalog)

    assert result.returncode == 0, result.stdout


@pytest.mark.parametrize(
    ("arguments", "named"),
    [
        pytest.param("", "Expected 2 arguments, but got 0", id="missing count"),
        pytest.param('{ name: "Eva" }', "Expected 2 arguments, but got 1", id="gaps without a count"),
        pytest.param(
            '"3", { name: "Eva" }',
            "Argument of type 'string' is not assignable to parameter of type 'number'",
            id="count as a string",
        ),
        pytest.param("3", "Expected 2 arguments, but got 1", id="missing gaps"),
        pytest.param("3, {}", "'name' is missing", id="missing gap"),
        pytest.param('3, { name: "Eva", count: 3 }', "'count' does not exist", id="a second count in the gaps"),
    ],
)
def test_a_consumer_passing_the_wrong_arguments_to_a_family_fails_tsc_strict(
    tmp_path, family_catalog, arguments, named
):
    result = type_check(tmp_path, seats(arguments), catalog=family_catalog)

    assert result.returncode != 0
    assert "consumer.ts" in result.stdout
    assert named in result.stdout


def test_a_consumer_passing_gaps_to_a_family_without_further_gaps_fails_tsc_strict(tmp_path):
    catalog = SourceCatalog(
        language=LanguageTag("de"),
        entries=(Entry(Key("table.seats.one"), "{count} Platz"), Entry(Key("table.seats.other"), "{count} Plätze")),
    )

    result = type_check(tmp_path, seats("3, {}"), catalog=catalog)

    assert result.returncode != 0
    assert "Expected 1 arguments, but got 2" in result.stdout


def family_translation(*texts: str) -> str:
    """The Polish module of the seats family, one text per category in the order one, few, many, other."""
    categories = ("one", "few", "many", "other")
    catalog = TranslationCatalog(
        language=LanguageTag("pl"),
        entries=tuple(
            Entry(Key(f"table.seats.{category}"), text) for category, text in zip(categories, texts, strict=True)
        ),
    )
    return render_translation(catalog, LanguageTag("de"))


def test_a_target_module_with_the_family_in_the_categories_of_its_language_passes_tsc_strict(tmp_path, family_catalog):
    target = family_translation(*("{name}: {count}",) * 4)

    result = type_check(tmp_path, seats('3, { name: "Eva" }', "pl"), target, family_catalog)

    assert result.returncode == 0, result.stdout


@pytest.mark.parametrize(
    ("texts", "named"),
    [
        pytest.param(("{count}",) * 4, "name", id="dropped gap of the source"),
        pytest.param(("{name}: {count} {other}",) * 4, "other", id="gap the source lacks"),
    ],
)
def test_a_target_module_whose_family_gaps_differ_from_the_sources_fails_tsc_strict(
    tmp_path, family_catalog, texts, named
):
    result = type_check(tmp_path, seats('3, { name: "Eva" }', "pl"), family_translation(*texts), family_catalog)

    assert result.returncode != 0
    assert "pl.ts" in result.stdout
    assert named in result.stdout


def test_a_target_module_without_the_family_fails_tsc_strict(tmp_path, family_catalog):
    catalog = SourceCatalog(
        language=LanguageTag("de"),
        entries=(*family_catalog.entries, Entry(Key("app.name"), "Skat")),
    )
    target = render_translation(translation("app.name"), LanguageTag("de"))

    result = type_check(tmp_path, seats('3, { name: "Eva" }', "pl"), target, catalog)

    assert result.returncode != 0
    assert "pl.ts" in result.stdout
    assert "table.seats" in result.stdout


def test_a_consumer_reading_the_page_language_and_loading_its_words_passes_tsc_strict(tmp_path):
    probe = (
        'import { languages, loadWords, sourceLanguage } from "./index";\n'
        "const tag = document.documentElement.lang;\n"
        "const language = languages.find((candidate) => candidate === tag) ?? sourceLanguage;\n"
        'export const seatFree: string = (await loadWords(language))["table.seatFree"];\n'
    )
    target = render_translation(translation("table.seatFree", "app.name"), LanguageTag("de"))

    result = type_check(tmp_path, probe, target)

    assert result.returncode == 0, result.stdout


def test_a_consumer_loading_a_language_no_catalog_has_fails_tsc_strict(tmp_path):
    probe = 'import { loadWords } from "./index";\nexport const words = loadWords("fr");\n'

    result = type_check(tmp_path, probe)

    assert result.returncode != 0
    assert '"fr"' in result.stdout


def marked(first: str | None, second: str | None, *, gaps: bool) -> str:
    """A sentence of two parts named `first` and `second`; a name of None leaves that part as plain words."""

    def part(name: str | None, content: str) -> str:
        return content if name is None else f"{{#{name}}}{content}{{/{name}}}"

    return f"{part(first, '{count}' if gaps else 'A')} z {part(second, '{name}' if gaps else 'B')}"


MARKED_SHAPES = {
    "plain": ((Entry(Key("home.note"), marked("strong", "code", gaps=False)),), ("home.note",)),
    "gaps": ((Entry(Key("home.note"), marked("strong", "code", gaps=True)),), ("home.note",)),
    "family": (
        (
            Entry(Key("home.note.one"), marked("strong", "code", gaps=True)),
            Entry(Key("home.note.other"), marked("strong", "code", gaps=True)),
        ),
        ("home.note.one", "home.note.few", "home.note.many", "home.note.other"),
    ),
}
CALLS = {
    "plain": 'words["home.note"]',
    "gaps": 'words["home.note"]({ count: 3, name: "Eva" })',
    "family": 'words["home.note"](3, { name: "Eva" })',
}
READ_PARTS = (
    'import { words } from "./MODULE";\n'
    "export const text: string ="
    " CALL.map((part) => (typeof part === 'string' ? part : part.marker + part.text)).join('');\n"
)


def marked_check(directory: Path, shape: str, consumer: str, target: str | None = None):
    """Type checks the consumer (CALL stands for the shape's call) against the de module of the shape and, given
    the text of a Polish translation, its module."""
    entries, keys = MARKED_SHAPES[shape]
    module = ""
    if target is not None:
        translated = TranslationCatalog(
            language=LanguageTag("pl"), entries=tuple(Entry(Key(key), target) for key in keys)
        )
        module = render_translation(translated, LanguageTag("de"))
    source = SourceCatalog(language=LanguageTag("de"), entries=entries)
    return type_check(directory, consumer.replace("CALL", CALLS[shape]), module, source)


@pytest.mark.parametrize("shape", MARKED_SHAPES)
def test_a_consumer_reading_the_parts_of_a_marked_text_passes_tsc_strict(tmp_path, shape):
    result = marked_check(tmp_path, shape, READ_PARTS.replace("MODULE", "de"))

    assert result.returncode == 0, result.stdout


@pytest.mark.parametrize("shape", MARKED_SHAPES)
@pytest.mark.parametrize(
    ("statement", "named"),
    [
        pytest.param("CALL.push('x');", "push", id="changing the list"),
        pytest.param(
            "export const same = CALL.some((part) => typeof part !== 'string' && part.marker === 'em');",
            "no overlap",
            id="a marker the text lacks",
        ),
        pytest.param("export const text: string = CALL;", "not assignable to type 'string'", id="a list as a string"),
    ],
)
def test_a_consumer_misusing_the_parts_of_a_marked_text_fails_tsc_strict(tmp_path, shape, statement, named):
    probe = f'import {{ words }} from "./de";\n{statement}\n'

    result = marked_check(tmp_path, shape, probe)

    assert result.returncode != 0
    assert "consumer.ts" in result.stdout
    assert named in result.stdout


@pytest.mark.parametrize("shape", MARKED_SHAPES)
def test_a_target_module_with_the_markers_of_the_source_passes_tsc_strict_in_both_directions(tmp_path, shape):
    target = marked("code", "strong", gaps=shape != "plain")

    result = marked_check(tmp_path, shape, READ_PARTS.replace("MODULE", "pl"), target)

    assert result.returncode == 0, result.stdout


@pytest.mark.parametrize("shape", MARKED_SHAPES)
@pytest.mark.parametrize(
    ("names", "named"),
    [
        pytest.param(("strong", "em"), "em", id="a marker the source lacks"),
        pytest.param(("strong", None), "code", id="a marker of the source left out"),
    ],
)
def test_a_target_module_whose_markers_differ_from_the_sources_fails_tsc_strict(tmp_path, shape, names, named):
    target = marked(*names, gaps=shape != "plain")

    result = marked_check(tmp_path, shape, READ_PARTS.replace("MODULE", "pl"), target)

    assert result.returncode != 0
    assert "pl.ts" in result.stdout
    assert named in result.stdout
