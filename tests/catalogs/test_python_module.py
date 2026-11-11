import subprocess
import sys
from pathlib import Path

import pytest

from design.catalogs.catalog import Entry, Key, LanguageTag, SourceCatalog, TranslationCatalog
from design.catalogs.python_module import render

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


def test_render_writes_the_key_and_language_types_the_words_of_every_language_and_the_lookup(module_text):
    module = module_text(
        ("de", {"table_seatFree": "Frei", "app_name": "Skat"}),
        ("pl", {"table_seatFree": "Wolne", "app_name": "Skat (pl)"}),
    )

    assert module == (
        "# Generated from the catalogs by design-catalogs. Do not edit.\n"
        "# fmt: off\n"
        "from typing import TYPE_CHECKING, Final, Literal\n"
        "\n"
        "if TYPE_CHECKING:\n"
        "    from collections.abc import Mapping\n"
        "\n"
        "type Key = Literal[\n"
        "    'table.seatFree',\n"
        "    'app.name',\n"
        "]\n"
        "type Language = Literal[\n"
        "    'de',\n"
        "    'pl',\n"
        "]\n"
        "\n"
        "SOURCE_LANGUAGE: Final[Language] = 'de'\n"
        "LANGUAGES: Final[tuple[Language, ...]] = (\n"
        "    'de',\n"
        "    'pl',\n"
        ")\n"
        "WORDS: Final[Mapping[Language, Mapping[Key, str]]] = {\n"
        "    'de': {\n"
        "        'table.seatFree': 'Frei',\n"
        "        'app.name': 'Skat',\n"
        "    },\n"
        "    'pl': {\n"
        "        'table.seatFree': 'Wolne',\n"
        "        'app.name': 'Skat (pl)',\n"
        "    },\n"
        "}\n"
        "\n"
        "\n"
        "def text(language: Language, key: Key) -> str:\n"
        "    return WORDS[language][key]\n"
    )


def test_render_gives_the_same_bytes_for_the_same_catalogs(module_text):
    arguments = (("de", {"table_seatFree": "Frei"}), ("pl", {"table_seatFree": "Wolne"}))

    assert module_text(*arguments) == module_text(*arguments)


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
        "{name} and %s",
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


@pytest.fixture
def write_module(module_text, tmp_path):
    def write(texts):
        path = tmp_path / "words.py"
        path.write_text(module_text(("de", texts), ("pl", texts)), encoding="utf-8")
        return path

    return write


@pytest.mark.parametrize("texts", [SHORT_TEXTS, LONG_TEXTS, {}], ids=["short", "long", "without entries"])
def test_ruff_format_leaves_the_module_unchanged_whatever_the_texts_and_their_length(write_module, texts):
    result = run_ruff(["format", "--check"], write_module(texts))

    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("texts", [SHORT_TEXTS, {}], ids=["with texts", "without entries"])
def test_ruff_check_finds_nothing_in_the_module(write_module, texts):
    result = run_ruff(["check", "--no-cache"], write_module(texts))

    assert result.returncode == 0, result.stdout + result.stderr
