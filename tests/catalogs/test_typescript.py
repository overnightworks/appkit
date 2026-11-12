import json

import pytest

from design.catalogs.catalog import Entry, Key, LanguageTag, SourceCatalog, TranslationCatalog
from design.catalogs.typescript import render, render_loader, render_translation


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


def test_render_translation_checks_the_gaps_of_a_translation_with_gaps_in_both_directions():
    catalog = TranslationCatalog(
        language=LanguageTag("pl"),
        entries=(Entry(Key("table.seatFree"), "Wolne"), Entry(Key("chat.greeting"), "Cześć {name}")),
    )

    assert render_translation(catalog, LanguageTag("de")) == (
        "// Generated from the pl catalog by design-catalogs. Do not edit.\n"
        "\n"
        'import type { Words } from "./de";\n'
        "// prettier-ignore\n"
        "const translated = {\n"
        '    "table.seatFree": "Wolne",\n'
        '    "chat.greeting": (gaps: { readonly name: string }) => "Cześć " + gaps.name,\n'
        "} satisfies Words;\n"
        "// A translation that leaves out a gap of its source fails here.\n"
        "({} as Words) satisfies typeof translated;\n"
        "export const words: Words = translated;\n"
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


@pytest.fixture
def greeting():
    """A text with a plain and a `count` gap."""
    return "Hallo {name}, du hast {count} Nachrichten"


@pytest.fixture
def call_greeting():
    """The probe that prints what the greeting of a module returns for Eva and 1234567."""
    return lambda module: (
        f'import {{ words }} from "./{module}.ts";'
        ' process.stdout.write(JSON.stringify(words["chat.greeting"]({ name: "Eva", count: 1234567 })));'
    )


def test_render_writes_a_text_with_gaps_as_a_function_of_its_gaps_in_the_type_and_the_words(source_catalog, greeting):
    module = render(source_catalog(chat_greeting=greeting, app_name="Skat"))

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
        '    "chat.greeting": (gaps: { readonly count: number; readonly name: string }) =>'
        ' "Hallo " + gaps.name + ", du hast " + numberFormat.format(gaps.count) + " Nachrichten",\n'
        '    "app.name": "Skat",\n'
        "};\n"
        "export type Key = keyof Words;\n"
    )


def test_a_gap_function_fills_its_gaps_and_formats_count_with_the_language_of_the_module(
    evaluate, source_catalog, greeting, call_greeting
):
    value = evaluate({"de.ts": render(source_catalog(chat_greeting=greeting))}, call_greeting("de"))

    assert value == "Hallo Eva, du hast 1.234.567 Nachrichten"


def test_a_translations_gap_function_formats_count_with_its_own_language(evaluate, call_greeting):
    translation = TranslationCatalog(
        language=LanguageTag("en"), entries=(Entry(Key("chat.greeting"), "{name} has {count} messages"),)
    )

    value = evaluate({"en.ts": render_translation(translation, LanguageTag("de"))}, call_greeting("en"))

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


def family_catalog(language, **texts):
    """A translation catalog holding one plural family `table.seats`, by category."""
    return TranslationCatalog(
        language=LanguageTag(language),
        entries=tuple(Entry(Key(f"table.seats.{category}"), text) for category, text in texts.items()),
    )


def sentences(*categories):
    """One sentence per category that names the category and the count, so a result says which one was chosen."""
    return {category: f"{category} {{count}}" for category in categories}


def call_seats(counts, module="de"):
    """The probe that prints what the seats family of a module returns for each count."""
    return (
        f'import {{ words }} from "./{module}.ts";'
        f' process.stdout.write(JSON.stringify({list(counts)}.map((count) => words["table.seats"](count))));'
    )


def test_render_writes_a_family_as_one_function_of_the_count_choosing_by_one_hoisted_plural_rules(source_catalog):
    module = render(
        source_catalog(table_seats_one="{count} Platz", table_seats_other="{count} Plätze", app_name="Skat")
    )

    assert module == (
        "// Generated from the de catalog by design-catalogs. Do not edit.\n"
        "\n"
        'export const language = "de";\n'
        'const numberFormat = new Intl.NumberFormat("de");\n'
        'const pluralRules = new Intl.PluralRules("de");\n'
        "// prettier-ignore\n"
        "export type Words = {\n"
        '    readonly "table.seats": (count: number) => string;\n'
        '    readonly "app.name": string;\n'
        "};\n"
        "// prettier-ignore\n"
        "export const words: Words = {\n"
        '    "table.seats": (count: number) => ({\n'
        '        zero: numberFormat.format(count) + " Plätze",\n'
        '        one: numberFormat.format(count) + " Platz",\n'
        '        two: numberFormat.format(count) + " Plätze",\n'
        '        few: numberFormat.format(count) + " Plätze",\n'
        '        many: numberFormat.format(count) + " Plätze",\n'
        '        other: numberFormat.format(count) + " Plätze",\n'
        "    })[pluralRules.select(count)],\n"
        '    "app.name": "Skat",\n'
        "};\n"
        "export type Key = keyof Words;\n"
    )


@pytest.mark.parametrize(
    ("language", "categories", "counts", "expected"),
    [
        pytest.param("de", ("one", "other"), (0, 1, 2), ["other 0", "one 1", "other 2"], id="de"),
        pytest.param("en", ("one", "other"), (0, 1, 2), ["other 0", "one 1", "other 2"], id="en"),
        pytest.param(
            "pl",
            ("one", "few", "many", "other"),
            (0, 1, 2, 5, 22, 1.5),
            ["many 0", "one 1", "few 2", "many 5", "few 22", "other 1,5"],
            id="pl",
        ),
    ],
)
def test_a_family_function_chooses_the_sentence_of_the_category_its_language_gives_the_count(
    evaluate, language, categories, counts, expected
):
    catalog = family_catalog(language, **sentences(*categories))
    module = render_translation(catalog, LanguageTag("de"))

    assert evaluate({f"{language}.ts": module}, call_seats(counts, language)) == expected


def test_a_family_function_falls_back_to_other_for_a_category_the_family_lacks(evaluate):
    module = render_translation(family_catalog("fr", one="eins", other="viele"), LanguageTag("de"))

    assert evaluate({"fr.ts": module}, call_seats((1, 1000000), "fr")) == ["eins", "viele"]


def test_a_family_function_returns_a_category_sentence_that_leaves_out_the_count_without_it(evaluate):
    module = render_translation(
        family_catalog("de", one="Ein Platz frei", other="{count} Plätze frei"), LanguageTag("de")
    )

    assert evaluate({"de.ts": module}, call_seats((1, 3), "de")) == ["Ein Platz frei", "3 Plätze frei"]


def test_a_family_function_fills_the_gaps_beside_the_count(evaluate):
    module = render_translation(
        family_catalog("en", one="{name} has {count} seat", other="{name} has {count} seats"), LanguageTag("de")
    )
    probe = (
        'import { words } from "./en.ts";'
        ' process.stdout.write(JSON.stringify(words["table.seats"](1234, { name: "Eva" })));'
    )

    assert evaluate({"en.ts": module}, probe) == "Eva has 1,234 seats"


def test_a_family_function_takes_the_gaps_object_only_where_the_family_has_a_further_gap(source_catalog):
    module = render(source_catalog(table_seats_one="{count} Platz", table_seats_other="{name}: {count} Plätze"))

    assert "(count: number, gaps: { readonly name: string }) => string;" in module


def test_a_module_hoists_one_plural_rules_however_many_families_it_holds(source_catalog):
    module = render(
        source_catalog(
            table_seats_one="a", table_seats_other="b", table_chairs_one="c", table_chairs_other="d", app_name="Skat"
        )
    )

    assert module.count("new Intl.PluralRules(") == 1


def test_a_module_without_a_family_holds_no_plural_rules(source_catalog):
    assert "PluralRules" not in render(source_catalog(chat_greeting="Hallo {name} {count}", app_name="Skat"))


def test_a_family_and_a_plain_text_of_a_translation_are_two_keys_of_its_words(evaluate):
    catalog = TranslationCatalog(
        language=LanguageTag("pl"),
        entries=(
            *family_catalog("pl", **sentences("one", "few", "many", "other")).entries,
            Entry(Key("app.name"), "Skat"),
        ),
    )
    probe = (
        'import { words } from "./pl.ts";'
        ' process.stdout.write(JSON.stringify([Object.keys(words), words["app.name"]]));'
    )

    assert evaluate({"pl.ts": render_translation(catalog, LanguageTag("de"))}, probe) == [
        ["table.seats", "app.name"],
        "Skat",
    ]


def test_render_loader_lists_the_languages_source_first_and_loads_each_module_by_a_dynamic_import():
    assert render_loader(LanguageTag("de"), (LanguageTag("pl"), LanguageTag("pt-BR"))) == (
        "// Generated from the catalogs by design-catalogs. Do not edit.\n"
        "\n"
        'import type { Words } from "./de";\n'
        "\n"
        'export const languages = ["de", "pl", "pt-BR"] as const;\n'
        "export type Language = (typeof languages)[number];\n"
        'export const sourceLanguage: Language = "de";\n'
        "// prettier-ignore\n"
        "const modules: Record<Language, () => Promise<{ readonly words: Words }>> = {\n"
        '    "de": () => import("./de"),\n'
        '    "pl": () => import("./pl"),\n'
        '    "pt-BR": () => import("./pt-BR"),\n'
        "};\n"
        "export const loadWords = async (language: Language): Promise<Words> => (await modules[language]()).words;\n"
    )


def test_render_loader_lists_the_source_alone_when_there_is_no_translation():
    assert 'export const languages = ["de"] as const;\n' in render_loader(LanguageTag("de"), ())


@pytest.fixture
def run_loader(evaluate):
    """Runs a probe over the loader and the modules of a source (`de`) and a translation (`pl`) in Node.

    The modules import each other without an extension, as an app's bundler resolves them; the hook adds the
    extension Node needs.
    """

    def run(probe: str):
        source = SourceCatalog(LanguageTag("de"), (Entry(Key("table.seatFree"), "Frei"),))
        translation = TranslationCatalog(LanguageTag("pl"), (Entry(Key("table.seatFree"), "Wolne"),))
        hook = (
            "export async function resolve(specifier, context, next) {"
            " try { return await next(specifier, context); }"
            " catch { return next(`${specifier}.ts`, context); } }"
        )
        return evaluate(
            {
                "de.ts": render(source),
                "pl.ts": render_translation(translation, source.language),
                "index.ts": render_loader(source.language, (translation.language,)),
            },
            'import { register } from "node:module";'
            f"register({json.dumps('data:text/javascript,' + hook)});"
            f'const loader = await import("./index.ts"); {probe}',
        )

    return run


def test_load_words_resolves_to_the_words_of_the_language(run_loader):
    probe = (
        "const loaded = await Promise.all(loader.languages.map((language) => loader.loadWords(language)));"
        "process.stdout.write(JSON.stringify(loaded));"
    )

    assert run_loader(probe) == [{"table.seatFree": "Frei"}, {"table.seatFree": "Wolne"}]


def test_the_loader_names_the_languages_and_the_source_language(run_loader):
    probe = "process.stdout.write(JSON.stringify([loader.languages, loader.sourceLanguage]));"

    assert run_loader(probe) == [["de", "pl"], "de"]


PARTS = 'readonly (string | { readonly marker: "strong"; readonly text: string })[]'


def test_render_writes_a_marked_text_without_gaps_as_a_constant_list_of_parts_with_an_explicit_type(source_catalog):
    module = render(source_catalog(home_note="Nur {#strong}wichtig{/strong} hier", app_name="Skat"))

    assert f'    readonly "home.note": {PARTS};\n' in module
    assert f'    "home.note": ["Nur ", {{ marker: "strong", text: "wichtig" }}, " hier"] as {PARTS},\n' in module
    assert '    "app.name": "Skat",\n' in module


def test_render_writes_a_marked_text_with_gaps_as_a_function_returning_parts_with_an_explicit_type(source_catalog):
    module = render(source_catalog(home_confirm="Lösche {#strong}{count} Takes{/strong} von {name}"))

    gaps = "gaps: { readonly count: number; readonly name: string }"
    assert f'    readonly "home.confirm": ({gaps}) => {PARTS};\n' in module
    assert (
        f'    "home.confirm": ({gaps}): {PARTS} =>'
        ' ["Lösche ", { marker: "strong", text: numberFormat.format(gaps.count) + " Takes" }, " von " + gaps.name],\n'
    ) in module


def test_render_writes_a_marked_family_as_a_function_of_the_count_returning_the_parts_of_its_category(source_catalog):
    module = render(
        source_catalog(
            table_seats_one="{#strong}{count}{/strong} Platz", table_seats_other="{#strong}{count}{/strong} Plätze"
        )
    )

    assert f'    readonly "table.seats": (count: number) => {PARTS};\n' in module
    assert (
        f'    "table.seats": (count: number): {PARTS} => ({{\n'
        '        zero: [{ marker: "strong", text: numberFormat.format(count) }, " Plätze"],\n'
        '        one: [{ marker: "strong", text: numberFormat.format(count) }, " Platz"],\n'
    ) in module
    assert "    } as const)[pluralRules.select(count)],\n" in module


def test_render_types_the_marker_of_a_text_as_the_union_of_its_marker_names(source_catalog):
    module = render(source_catalog(home_note="{#code}a{/code} und {#strong}b{/strong} und {#code}c{/code}"))

    union = '"code" | "strong"'
    assert (
        f'    readonly "home.note": readonly (string | {{ readonly marker: {union}; readonly text: string }})[];\n'
        in module
    )


def test_render_translation_gives_a_marked_text_its_own_explicit_type_and_checks_it_in_both_directions():
    catalog = TranslationCatalog(
        language=LanguageTag("pl"), entries=(Entry(Key("home.note"), "Tylko {#strong}wazne{/strong}"),)
    )

    module = render_translation(catalog, LanguageTag("de"))

    assert f'    "home.note": ["Tylko ", {{ marker: "strong", text: "wazne" }}] as {PARTS},\n' in module
    assert "} satisfies Words;\n" in module
    assert "({} as Words) satisfies typeof translated;\n" in module


def evaluated(evaluate, source_catalog, call, **texts):
    """What the call (an expression over `words`) returns for a de module of the texts."""
    probe = f'import {{ words }} from "./de.ts"; process.stdout.write(JSON.stringify({call}));'
    return evaluate({"de.ts": render(source_catalog(**texts))}, probe)


@pytest.mark.parametrize(
    ("text", "parts"),
    [
        pytest.param(
            "Nur {#strong}wichtig{/strong}", ["Nur ", {"marker": "strong", "text": "wichtig"}], id="at the end"
        ),
        pytest.param(
            "{#strong}Wichtig{/strong} nur", [{"marker": "strong", "text": "Wichtig"}, " nur"], id="at the start"
        ),
        pytest.param(
            "{#a}x{/a}{#b}y{/b}",
            [{"marker": "a", "text": "x"}, {"marker": "b", "text": "y"}],
            id="adjacent parts with no empty string between",
        ),
        pytest.param(
            "Use {{braces}} {#a}{{x}}{/a} too",
            ["Use {braces} ", {"marker": "a", "text": "{x}"}, " too"],
            id="doubled braces merge into the literal around them",
        ),
    ],
)
def test_a_marked_text_without_gaps_evaluates_to_its_parts(evaluate, source_catalog, text, parts):
    assert evaluated(evaluate, source_catalog, 'words["home.note"]', home_note=text) == parts


@pytest.mark.parametrize(
    "literal", ['say "hi"', "back\\slash", "two\nlines", '"; process.exit(1); "', "</script>", "line\u2028separator"]
)
def test_a_marked_text_keeps_every_literal_inside_its_string(evaluate, source_catalog, literal):
    escaped = literal.replace("{", "{{").replace("}", "}}")

    assert evaluated(evaluate, source_catalog, 'words["home.note"]', home_note=f"{escaped} {{#a}}{escaped}{{/a}}") == [
        f"{literal} ",
        {"marker": "a", "text": literal},
    ]


def test_a_marked_text_with_gaps_evaluates_to_its_parts_with_the_gaps_filled(evaluate, source_catalog):
    text = "Archive {#strong}{count} takes{/strong} and delete {#strong}{deleted}{/strong}. {name}"
    call = 'words["home.note"]({ count: 1234, deleted: "2", name: "Eva" })'

    assert evaluated(evaluate, source_catalog, call, home_note=text) == [
        "Archive ",
        {"marker": "strong", "text": "1.234 takes"},
        " and delete ",
        {"marker": "strong", "text": "2"},
        ". Eva",
    ]


def test_a_gap_alone_outside_a_part_is_a_string_part(evaluate, source_catalog):
    call = 'words["home.note"]({ name: "Eva" })'

    assert evaluated(evaluate, source_catalog, call, home_note="{name}{#a}x{/a}") == [
        "Eva",
        {"marker": "a", "text": "x"},
    ]


def test_a_marked_family_evaluates_to_the_parts_of_the_category_of_the_count(evaluate, source_catalog):
    call = '[1, 2].map((count) => words["table.seats"](count, { name: "Eva" }))'

    assert evaluated(
        evaluate,
        source_catalog,
        call,
        table_seats_one="{name}: {#strong}{count}{/strong} Platz",
        table_seats_other="{name}: {#strong}{count}{/strong} Plätze",
    ) == [
        ["Eva: ", {"marker": "strong", "text": "1"}, " Platz"],
        ["Eva: ", {"marker": "strong", "text": "2"}, " Plätze"],
    ]
