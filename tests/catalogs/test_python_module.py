import subprocess
import sys
from pathlib import Path

import pytest
from babel import Locale, localedata
from babel.plural import to_python

from design.catalogs.catalog import Entry, Key, LanguageTag, SourceCatalog, TranslationCatalog
from design.catalogs.po_file import plural_rule
from design.catalogs.python_module import render
from design.catalogs.typescript import render as render_typescript
from design.catalogs.typescript import render_translation

REPOSITORY = Path(__file__).resolve().parents[2]


def catalog(kind, language, texts):
    return kind(
        language=LanguageTag(language),
        entries=tuple(Entry(key=Key(key.replace("_", ".")), text=text) for key, text in texts.items()),
    )


@pytest.fixture
def module_text():
    """The module of a source and its translations, each given as a language and its `surface_name: text` pairs."""

    def build(source, *translations):
        return render(
            catalog(SourceCatalog, *source),
            tuple(catalog(TranslationCatalog, *translation) for translation in translations),
            plural_rule,
        )

    return build


@pytest.fixture
def load(tmp_path, import_module):
    """Imports module text the way an app does: as a file on disk."""

    def import_text(text):
        path = tmp_path / "words.py"
        path.write_text(text, encoding="utf-8")
        return import_module(path)

    return import_text


def test_render_writes_the_key_and_language_types_and_the_words_of_every_language_one_entry_per_line(module_text):
    module = module_text(
        (
            "de",
            {
                "table_seatFree": "Frei",
                "app_name": "Skat",
                "table_seats_one": "{count} Platz",
                "table_seats_other": "{count} Plätze",
            },
        ),
        (
            "pl",
            {
                "table_seatFree": "Wolne",
                "app_name": "Skat (pl)",
                "table_seats_one": "{count} miejsce",
                "table_seats_other": "{count} miejsc",
            },
        ),
    )

    assert module.startswith(
        "# Generated from the catalogs by design-catalogs. Do not edit.\n"
        "# fmt: off\n"
        "from string import Formatter\n"
        "from typing import TYPE_CHECKING, Final, Literal\n"
        "\n"
        "if TYPE_CHECKING:\n"
        "    from collections.abc import Mapping\n"
        "\n"
        "type Key = Literal[\n"
        "    'table.seatFree',\n"
        "    'app.name',\n"
        "    'table.seats',\n"
        "]\n"
        "type Language = Literal[\n"
        "    'de',\n"
        "    'pl',\n"
        "]\n"
        "type Category = Literal[\n"
        "    'zero',\n"
        "    'one',\n"
        "    'two',\n"
        "    'few',\n"
        "    'many',\n"
        "    'other',\n"
        "]\n"
        "\n"
        "SOURCE_LANGUAGE: Final[Language] = 'de'\n"
        "LANGUAGES: Final[tuple[Language, ...]] = (\n"
        "    'de',\n"
        "    'pl',\n"
        ")\n"
        "WORDS: Final[Mapping[Language, Mapping[Key, str | Mapping[Category, str]]]] = {\n"
        "    'de': {\n"
        "        'table.seatFree': 'Frei',\n"
        "        'app.name': 'Skat',\n"
        "        'table.seats': {\n"
        "            'one': '{count} Platz',\n"
        "            'other': '{count} Plätze',\n"
        "        },\n"
        "    },\n"
        "    'pl': {\n"
        "        'table.seatFree': 'Wolne',\n"
        "        'app.name': 'Skat (pl)',\n"
        "        'table.seats': {\n"
        "            'one': '{count} miejsce',\n"
        "            'other': '{count} miejsc',\n"
        "        },\n"
        "    },\n"
        "}\n"
    )


def test_the_module_answers_every_language_and_key_by_text(module_text, load):
    module = load(
        module_text(
            ("de", {"table_seatFree": "Frei", "app_name": "Skat"}),
            ("pl", {"table_seatFree": "Wolne", "app_name": "Skat (pl)"}),
        )
    )

    assert module.SOURCE_LANGUAGE == "de"
    assert module.LANGUAGES == ("de", "pl")
    assert [module.text(language, "table.seatFree") for language in module.LANGUAGES] == ["Frei", "Wolne"]
    assert module.WORDS["pl"] == {"table.seatFree": "Wolne", "app.name": "Skat (pl)"}


def test_the_module_of_a_source_alone_holds_the_source_language_only(module_text, load):
    module = load(module_text(("de", {"table_seatFree": "Frei"})))

    assert module.LANGUAGES == ("de",)
    assert module.text("de", "table.seatFree") == "Frei"


def test_the_module_of_a_source_without_entries_imports_and_holds_no_text(module_text, load):
    module = load(module_text(("de", {})))

    assert module.WORDS == {"de": {}}


@pytest.mark.parametrize(
    "text",
    [
        'say "hi"',
        "it's",
        "both ' and \"",
        "back\\slash",
        "two\nlines",
        "ümlaut and 日本語",
        "line\u2028separator",
        "\x00 and \x1f",
        '"""',
        "'''",
        "%s and %(name)s",
        "'; raise SystemExit(1); '",
        "x" * 400,
    ],
)
def test_the_module_keeps_any_catalog_text_inside_its_literal(module_text, load, text):
    module = load(module_text(("de", {"table_text": text})))

    assert module.text("de", "table.text") == text
    assert list(module.WORDS["de"].values()) == [text]


def run_ruff(arguments, path):
    return subprocess.run(
        [sys.executable, "-m", "ruff", *arguments, "--config", str(REPOSITORY / "pyproject.toml"), str(path)],
        capture_output=True,
        text=True,
        check=False,
    )


SHORT_TEXTS = {"table_seatFree": "Frei", "app_text": 'say "hi" and it\'s'}
LONG_TEXTS = {**SHORT_TEXTS, "app_long": "long " * 80}
FAMILY_TEXTS = {**SHORT_TEXTS, "table_seats_one": "{count} Platz", "table_seats_other": "{count} Plätze"}


@pytest.fixture
def write_module(module_text, tmp_path):
    def write(texts):
        path = tmp_path / "words.py"
        path.write_text(module_text(("de", texts), ("pl", texts)), encoding="utf-8")
        return path

    return write


@pytest.mark.parametrize(
    "texts", [SHORT_TEXTS, LONG_TEXTS, FAMILY_TEXTS, {}], ids=["short", "long", "with a family", "without entries"]
)
def test_ruff_format_leaves_the_module_unchanged_whatever_the_texts_and_their_length(write_module, texts):
    result = run_ruff(["format", "--check"], write_module(texts))

    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    "texts", [SHORT_TEXTS, FAMILY_TEXTS, {}], ids=["with texts", "with a family", "without entries"]
)
def test_ruff_check_finds_nothing_in_the_module(write_module, texts):
    result = run_ruff(["check", "--no-cache"], write_module(texts))

    assert result.returncode == 0, result.stdout + result.stderr


SEATS = {"table_seats_one": "{count} Platz", "table_seats_other": "{count} Plätze"}
POLISH_SEATS = {
    "table_seats_one": "{count} miejsce",
    "table_seats_few": "{count} miejsca",
    "table_seats_many": "{count} miejsc",
    "table_seats_other": "{count} miejsca",
}


def test_text_fills_the_named_gaps_and_gives_doubled_braces_as_single_braces(module_text, load):
    module = load(module_text(("de", {"chat_greeting": "Hallo {name}, {{{place}}}"})))

    assert module.text("de", "chat.greeting", name="Eva", place="Ulm") == "Hallo Eva, {Ulm}"


def test_text_gives_doubled_braces_of_a_text_without_gaps_as_single_braces(module_text, load):
    module = load(module_text(("de", {"app_braces": "{{x}}"})))

    assert module.text("de", "app.braces") == "{x}"


def test_text_does_not_read_a_gap_value_as_a_gap(module_text, load):
    module = load(module_text(("de", {"chat_greeting": "Hallo {name}"})))

    assert module.text("de", "chat.greeting", name="{name}") == "Hallo {name}"


def test_text_formats_the_count_of_a_plain_text_that_has_a_count_gap(module_text, load):
    module = load(module_text(("de", {"chat_unread": "{count} ungelesen"})))

    assert module.text("de", "chat.unread", count=3) == "3 ungelesen"


@pytest.mark.parametrize(
    ("arguments", "named"),
    [
        pytest.param({}, "name", id="missing gap"),
        pytest.param({"name": "Eva", "place": "Ulm"}, "place", id="unknown gap"),
        pytest.param({"name": "Eva", "count": 3}, "count", id="count the text has no gap for"),
    ],
)
def test_text_raises_naming_the_key_and_the_gap_when_a_gap_is_missing_or_unknown(module_text, load, arguments, named):
    module = load(module_text(("de", {"chat_greeting": "Hallo {name}"})))

    with pytest.raises(TypeError, match=rf"chat\.greeting.*{named}"):
        module.text("de", "chat.greeting", **arguments)


def test_the_words_hold_a_family_under_its_family_key_and_not_its_categories_as_keys(module_text, load):
    module = load(module_text(("de", SEATS), ("pl", POLISH_SEATS)))

    assert module.WORDS["de"] == {"table.seats": {"one": "{count} Platz", "other": "{count} Plätze"}}
    assert module.WORDS["pl"]["table.seats"]["few"] == "{count} miejsca"


@pytest.mark.parametrize(
    ("language", "count", "expected"),
    [
        pytest.param("de", 0, "0 Plätze", id="zero in german"),
        pytest.param("de", 1, "1 Platz", id="one in german"),
        pytest.param("de", 2, "2 Plätze", id="two in german"),
        pytest.param("pl", 1, "1 miejsce", id="one in polish"),
        pytest.param("pl", 22, "22 miejsca", id="few in polish"),
        pytest.param("pl", 5, "5 miejsc", id="many in polish"),
        pytest.param("pl", 112, "112 miejsc", id="many in polish above a hundred"),
    ],
)
def test_text_of_a_family_chooses_the_sentence_of_the_category_of_the_count_and_fills_the_count(
    module_text, load, language, count, expected
):
    module = load(module_text(("de", SEATS), ("pl", POLISH_SEATS)))

    assert module.text(language, "table.seats", count=count) == expected


def test_text_of_a_family_falls_back_to_other_for_a_category_the_family_lacks(module_text, load):
    module = load(module_text(("de", SEATS), ("fr", SEATS)))

    assert module.text("fr", "table.seats", count=1_000_000) == "1000000 Plätze"


def test_text_of_a_family_returns_a_category_sentence_that_leaves_out_the_count_without_it(module_text, load):
    module = load(
        module_text(("de", {"table_seats_one": "Ein Platz frei", "table_seats_other": "{count} Plätze frei"}))
    )

    assert [module.text("de", "table.seats", count=count) for count in (1, 3)] == ["Ein Platz frei", "3 Plätze frei"]


def test_text_of_a_family_fills_the_gaps_beside_the_count(module_text, load):
    module = load(
        module_text(("de", {"table_seats_one": "{name}: {count} Platz", "table_seats_other": "{name}: {count} Plätze"}))
    )

    assert module.text("de", "table.seats", count=2, name="Eva") == "Eva: 2 Plätze"


@pytest.mark.parametrize(
    ("arguments", "named"),
    [
        pytest.param({}, "count", id="no count"),
        pytest.param({"count": 2, "name": "Eva"}, "name", id="unknown gap beside the count"),
    ],
)
def test_text_of_a_family_raises_naming_the_key_and_what_is_wrong_with_the_arguments(
    module_text, load, arguments, named
):
    module = load(module_text(("de", SEATS)))

    with pytest.raises(TypeError, match=rf"table\.seats.*{named}"):
        module.text("de", "table.seats", **arguments)


@pytest.mark.parametrize(
    ("language", "counts", "expected"),
    [
        pytest.param("de", (0, 1, 2, 11, 21), ["other", "one", "other", "other", "other"], id="german"),
        pytest.param(
            "pl", (0, 1, 2, 5, 12, 22, 112), ["many", "one", "few", "many", "many", "few", "many"], id="polish"
        ),
        pytest.param("fr", (0, 1, 2, 1_000_000), ["one", "one", "other", "many"], id="french"),
        pytest.param("ja", (0, 1, 2), ["other", "other", "other"], id="japanese without a plural"),
        pytest.param("tlh", (0, 1, 2), ["other", "other", "other"], id="a language babel has no rules for"),
    ],
)
def test_plural_category_gives_the_cldr_category_of_a_whole_count(module_text, load, language, counts, expected):
    module = load(module_text(("de", {"app_name": "x"}), (language, {"app_name": "x"})))

    assert [module.plural_category(language, count) for count in counts] == expected


def test_plural_category_takes_the_absolute_count(module_text, load):
    module = load(module_text(("de", {"app_name": "x"})))

    assert [module.plural_category("de", count) for count in (-1, -2)] == ["one", "other"]


def bcp47(identifier):
    """A Babel locale identifier as the language tag of a catalog: Babel writes variants in capitals."""
    return "-".join(part.lower() if len(part) > 4 and part.isupper() else part for part in identifier.split("_"))


def test_plural_category_equals_babels_rule_for_every_locale_babel_ships_over_zero_to_two_hundred(module_text, load):
    identifiers = {bcp47(identifier): identifier for identifier in localedata.locale_identifiers()}
    languages = [(tag, {"app_name": "x"}) for tag in identifiers if tag != "de"]
    module = load(module_text(("de", {"app_name": "x"}), *languages))

    differing = []
    for tag, identifier in identifiers.items():
        babel = to_python(Locale.parse(identifier).plural_form)
        differing.extend((tag, count) for count in range(201) if module.plural_category(tag, count) != babel(count))

    assert differing == []


def test_plural_category_of_a_module_of_a_language_without_a_plural_rule_needs_no_count(module_text, load):
    text = module_text(("ja", {"app_name": "x"}))

    assert "abs(count)" not in text
    assert load(text).plural_category("ja", 1) == "other"


def test_python_and_typescript_modules_of_the_same_catalogs_choose_and_fill_the_same_sentences(
    module_text, load, evaluate
):
    source = ("de", {"table_seats_one": "Ein Platz frei", "table_seats_other": "{count} Plätze frei"})
    translations = [("en", SEATS), ("pl", POLISH_SEATS)]
    counts = [0, 1, 2, 3, 5, 11, 12, 21, 22, 100, 101, 112, 999]
    modules = {
        "de.ts": render_typescript(catalog(SourceCatalog, *source)),
        **{
            f"{language}.ts": render_translation(catalog(TranslationCatalog, language, texts), LanguageTag("de"))
            for language, texts in translations
        },
    }
    probe = (
        f"const counts = {counts}; const result = {{}};"
        + "".join(
            f'{{ const {{ words }} = await import("./{language}.ts");'
            f' result.{language} = counts.map((count) => words["table.seats"](count)); }}'
            for language in ("de", "en", "pl")
        )
        + "process.stdout.write(JSON.stringify(result));"
    )
    python = load(module_text(source, *translations))

    assert evaluate(modules, probe) == {
        language: [python.text(language, "table.seats", count=count) for count in counts]
        for language in ("de", "en", "pl")
    }
