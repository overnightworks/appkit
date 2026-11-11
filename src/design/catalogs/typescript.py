"""The typed TypeScript module of a source catalog."""

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from design.catalogs.catalog import Entry, LanguageTag, SourceCatalog, TranslationCatalog

# The module is laid out by this renderer; prettier would reflow its objects.
PRETTIER_IGNORE = "// prettier-ignore"


def header(language: LanguageTag) -> str:
    return f"// Generated from the {language.value} catalog by design-catalogs. Do not edit."


def quoted(text: str) -> str:
    return json.dumps(text, ensure_ascii=False)


def word_lines(entries: tuple[Entry, ...]) -> str:
    return "".join(f"    {quoted(entry.key.value)}: {quoted(entry.text)},\n" for entry in entries)


def render(catalog: SourceCatalog) -> str:
    type_lines = "".join(f"    readonly {quoted(entry.key.value)}: string;\n" for entry in catalog.entries)
    return (
        f"{header(catalog.language)}\n\n"
        f"export const language = {quoted(catalog.language.value)};\n"
        f"{PRETTIER_IGNORE}\n"
        f"export type Words = {{\n{type_lines}}};\n"
        f"{PRETTIER_IGNORE}\n"
        f"export const words: Words = {{\n{word_lines(catalog.entries)}}};\n"
        "export type Key = keyof Words;\n"
    )


def render_translation(catalog: TranslationCatalog, source: LanguageTag) -> str:
    """The module of a translation, typed by the source module's `Words` so a wrong key set fails the type check."""
    return (
        f"{header(catalog.language)}\n\n"
        f"import type {{ Words }} from {quoted(f'./{source.value}')};\n"
        f"{PRETTIER_IGNORE}\n"
        f"export const words: Words = {{\n{word_lines(catalog.entries)}}};\n"
    )
