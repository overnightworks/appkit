import pytest

from design.catalogs.catalog import Entry, Key, LanguageTag, SourceCatalog, TranslationCatalog
from design.catalogs.typescript import render, render_translation


@pytest.fixture
def source_catalog():
    def build(**texts):
        return SourceCatalog(
            language=LanguageTag("de"),
            entries=tuple(Entry(key=Key(key.replace("_", ".")), text=text) for key, text in texts.items()),
        )

    return build


def test_render_writes_the_language_the_written_out_type_the_words_and_the_key_type(source_catalog):
    module = render(source_catalog(table_seatFree="Frei", app_name="Skat"))

    assert module == (
        "// Generated from the de catalog by design-catalogs. Do not edit.\n"
        "\n"
        'export const language = "de";\n'
        "// prettier-ignore\n"
        "export type Words = {\n"
        '    readonly "table.seatFree": string;\n'
        '    readonly "app.name": string;\n'
        "};\n"
        "// prettier-ignore\n"
        "export const words: Words = {\n"
        '    "table.seatFree": "Frei",\n'
        '    "app.name": "Skat",\n'
        "};\n"
        "export type Key = keyof Words;\n"
    )


def test_render_translation_imports_the_words_type_of_the_source_and_declares_the_words_with_it():
    catalog = TranslationCatalog(
        language=LanguageTag("pl"),
        entries=(Entry(Key("table.seatFree"), "Wolne"), Entry(Key("app.name"), 'Skat "pl"')),
    )

    assert render_translation(catalog, LanguageTag("de")) == (
        "// Generated from the pl catalog by design-catalogs. Do not edit.\n"
        "\n"
        'import type { Words } from "./de";\n'
        "// prettier-ignore\n"
        "export const words: Words = {\n"
        '    "table.seatFree": "Wolne",\n'
        '    "app.name": "Skat \\"pl\\"",\n'
        "};\n"
    )


def test_render_gives_the_same_bytes_for_the_same_catalog(source_catalog):
    first = render(source_catalog(table_seatFree="Frei"))
    second = render(source_catalog(table_seatFree="Frei"))

    assert first == second


def test_render_keeps_umlauts_readable(source_catalog):
    assert "lässt" in render(source_catalog(table_loadFailed="Der Tisch lässt sich nicht laden"))


@pytest.mark.parametrize(
    "text",
    [
        'say "hi"',
        "back\\slash",
        "two\nlines",
        'break"; process.exit(1); "',
        "</script><script>alert(1)</script>",
        "line\u2028separator",
    ],
)
def test_render_keeps_any_catalog_text_inside_its_literal(evaluate, source_catalog, text):
    probe = 'import { words } from "./de.ts"; process.stdout.write(JSON.stringify(words));'

    assert evaluate({"de.ts": render(source_catalog(table_text=text))}, probe) == {"table.text": text}


GREETING = "Hallo {name}, du hast {count} Nachrichten"
CALL_GREETING = (
    'import { words } from "./de.ts";'
    ' process.stdout.write(JSON.stringify(words["chat.greeting"]({ name: "Eva", count: 1234567 })));'
)


def test_render_writes_a_text_with_gaps_as_a_function_of_its_gaps_in_the_type_and_the_words(source_catalog):
    module = render(source_catalog(chat_greeting=GREETING, app_name="Skat"))

    assert module == (
        "// Generated from the de catalog by design-catalogs. Do not edit.\n"
        "\n"
        'export const language = "de";\n'
        'const numberFormat = new Intl.NumberFormat("de");\n'
        "// prettier-ignore\n"
        "export type Words = {\n"
        '    readonly "chat.greeting": (gaps: { readonly count: number; readonly name: string }) => string;\n'
        '    readonly "app.name": string;\n'
        "};\n"
        "// prettier-ignore\n"
        "export const words: Words = {\n"
        '    "chat.greeting": (gaps) => "Hallo " + gaps.name + ", du hast " + numberFormat.format(gaps.count)'
        ' + " Nachrichten",\n'
        '    "app.name": "Skat",\n'
        "};\n"
        "export type Key = keyof Words;\n"
    )


def test_a_gap_function_fills_its_gaps_and_formats_count_with_the_language_of_the_module(evaluate, source_catalog):
    value = evaluate({"de.ts": render(source_catalog(chat_greeting=GREETING))}, CALL_GREETING)

    assert value == "Hallo Eva, du hast 1.234.567 Nachrichten"


def test_a_translations_gap_function_formats_count_with_its_own_language(evaluate):
    translation = TranslationCatalog(
        language=LanguageTag("en"), entries=(Entry(Key("chat.greeting"), "{name} has {count} messages"),)
    )

    value = evaluate(
        {"en.ts": render_translation(translation, LanguageTag("de"))}, CALL_GREETING.replace("de.ts", "en.ts")
    )

    assert value == "Eva has 1,234,567 messages"


def test_a_module_hoists_one_number_format_however_many_texts_use_count(source_catalog):
    module = render(source_catalog(chat_first="{count} eins", chat_second="{count} zwei", chat_third="{name}"))

    assert module.count("new Intl.NumberFormat(") == 1


def test_a_module_without_a_count_gap_holds_no_number_format(source_catalog):
    assert "NumberFormat" not in render(source_catalog(chat_greeting="Hallo {name}", app_name="Skat"))


def test_a_module_holds_a_gap_function_only_for_a_text_with_gaps(evaluate, source_catalog):
    module = render(source_catalog(chat_greeting="Hallo {name}", app_name="Skat"))
    probe = (
        'import { words } from "./de.ts";'
        ' process.stdout.write(JSON.stringify([typeof words["chat.greeting"], typeof words["app.name"]]));'
    )

    assert evaluate({"de.ts": module}, probe) == ["function", "string"]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        pytest.param("Nutze {{Klammern}} bei {name}", "Nutze {Klammern} bei Eva", id="doubled braces beside a gap"),
        pytest.param('"; process.exit(1); "{name}', '"; process.exit(1); "Eva', id="a literal that tries to leave"),
        pytest.param("{name}{name}", "EvaEva", id="a gap used twice"),
        pytest.param("`${{process.exit(1)}}` {name}", "`${process.exit(1)}` Eva", id="a template literal"),
    ],
)
def test_a_gap_function_keeps_every_literal_inside_its_string_and_unescapes_doubled_braces(
    evaluate, source_catalog, text, expected
):
    probe = (
        'import { words } from "./de.ts"; process.stdout.write(JSON.stringify(words["chat.text"]({ name: "Eva" })));'
    )

    assert evaluate({"de.ts": render(source_catalog(chat_text=text))}, probe) == expected


def test_a_text_without_gaps_but_with_doubled_braces_is_a_string_with_single_braces(evaluate, source_catalog):
    probe = 'import { words } from "./de.ts"; process.stdout.write(JSON.stringify(words["chat.text"]));'

    assert evaluate({"de.ts": render(source_catalog(chat_text="Nutze {{Klammern}}"))}, probe) == "Nutze {Klammern}"
