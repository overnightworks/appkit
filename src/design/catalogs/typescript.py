"""The typed TypeScript module of a source catalog."""

import json
from typing import TYPE_CHECKING

from design.catalogs.catalog import gap_names, pieces_of

if TYPE_CHECKING:
    from collections.abc import Iterable

    from design.catalogs.catalog import Entry, LanguageTag, Piece, SourceCatalog, TranslationCatalog

# The module is laid out by this renderer; prettier would reflow its objects.
PRETTIER_IGNORE = "// prettier-ignore"
# A gap with this name is a number; the module formats it with `Intl.NumberFormat` of its own language.
COUNT = "count"
NUMBER_FORMAT = "numberFormat"
TRANSLATED = "translated"
# A function taking fewer gaps than the source's still satisfies `Words`; this checks the other direction.
GAP_SET_CHECK = (
    f"// A translation that leaves out a gap of its source fails here.\n({{}} as Words) satisfies typeof {TRANSLATED};"
)


def header(language: LanguageTag) -> str:
    return f"// Generated from the {language.value} catalog by design-catalogs. Do not edit."


def quoted(text: str) -> str:
    return json.dumps(text, ensure_ascii=False)


def reference(name: str) -> str:
    return f"{NUMBER_FORMAT}.format(gaps.{name})" if name == COUNT else f"gaps.{name}"


def expression(pieces: tuple[Piece, ...]) -> str:
    # Literal parts are JSON strings, so no catalog text can leave its string literal.
    return " + ".join(quoted(piece) if isinstance(piece, str) else reference(piece.name) for piece in pieces)


def gap_field(name: str) -> str:
    return f"readonly {name}: {'number' if name == COUNT else 'string'}"


def gap_parameter(names: Iterable[str]) -> str:
    return f"gaps: {{ {'; '.join(map(gap_field, names))} }}"


def word_type(entry: Entry) -> str:
    names = sorted(gap_names(pieces_of(entry.text)))
    return f"({gap_parameter(names)}) => string" if names else "string"


def word_value(entry: Entry) -> str:
    pieces = pieces_of(entry.text)
    if gap_names(pieces):
        return f"({gap_parameter(sorted(gap_names(pieces)))}) => {expression(pieces)}"
    return quoted("".join(piece for piece in pieces if isinstance(piece, str)))


def word_lines(entries: tuple[Entry, ...]) -> str:
    return "".join(f"    {quoted(entry.key.value)}: {word_value(entry)},\n" for entry in entries)


def number_format_line(language: LanguageTag, entries: tuple[Entry, ...]) -> str:
    """The one number format of the module, written only where a text has a `count` gap."""
    if any(COUNT in gap_names(pieces_of(entry.text)) for entry in entries):
        return f"const {NUMBER_FORMAT} = new Intl.NumberFormat({quoted(language.value)});\n"
    return ""


def render(catalog: SourceCatalog) -> str:
    type_lines = "".join(f"    readonly {quoted(entry.key.value)}: {word_type(entry)};\n" for entry in catalog.entries)
    return (
        f"{header(catalog.language)}\n\n"
        f"export const language = {quoted(catalog.language.value)};\n"
        f"{number_format_line(catalog.language, catalog.entries)}"
        f"{PRETTIER_IGNORE}\n"
        f"export type Words = {{\n{type_lines}}};\n"
        f"{PRETTIER_IGNORE}\n"
        f"export const words: Words = {{\n{word_lines(catalog.entries)}}};\n"
        "export type Key = keyof Words;\n"
    )


def words_declaration(entries: tuple[Entry, ...]) -> str:
    """The words typed as `Words`; where a text has gaps, also checked for a gap its source has and it leaves out."""
    if any(gap_names(pieces_of(entry.text)) for entry in entries):
        return (
            f"const {TRANSLATED} = {{\n{word_lines(entries)}}} satisfies Words;\n"
            f"{GAP_SET_CHECK}\n"
            f"export const words: Words = {TRANSLATED};\n"
        )
    return f"export const words: Words = {{\n{word_lines(entries)}}};\n"


def render_translation(catalog: TranslationCatalog, source: LanguageTag) -> str:
    """The module of a translation, typed by the source module's `Words` so a wrong key set fails the type check."""
    return (
        f"{header(catalog.language)}\n\n"
        f"import type {{ Words }} from {quoted(f'./{source.value}')};\n"
        f"{number_format_line(catalog.language, catalog.entries)}"
        f"{PRETTIER_IGNORE}\n"
        f"{words_declaration(catalog.entries)}"
    )
