import json
import subprocess

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
        "// Generated from the source catalog by design-catalogs. Do not edit.\n"
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
        "// Generated from the source catalog by design-catalogs. Do not edit.\n"
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
        "`${process.exit(1)}`",
    ],
)
def test_render_keeps_any_catalog_text_inside_its_literal(tmp_path, source_catalog, text):
    (tmp_path / "de.ts").write_text(render(source_catalog(table_text=text)), encoding="utf-8")
    probe = 'import { words } from "./de.ts"; process.stdout.write(JSON.stringify(words));'

    result = subprocess.run(
        ["node", "--input-type=module", "--eval", probe],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(result.stdout) == {"table.text": text}
