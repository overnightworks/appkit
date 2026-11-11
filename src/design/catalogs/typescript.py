"""The typed TypeScript module of a source catalog."""

import json
from typing import TYPE_CHECKING

from design.catalogs.catalog import Entry, Family, PluralCategory, gap_names, pieces_of, words_of

if TYPE_CHECKING:
    from collections.abc import Iterable

    from design.catalogs.catalog import LanguageTag, Piece, SourceCatalog, TranslationCatalog

# The module is laid out by this renderer; prettier would reflow its objects.
PRETTIER_IGNORE = "// prettier-ignore"
# A gap with this name is a number; the module formats it with `Intl.NumberFormat` of its own language.
COUNT = "count"
NUMBER_FORMAT = "numberFormat"
# A family's function takes the count as its own argument, so the sentence is chosen by the number it shows.
PLURAL_RULES = "pluralRules"
TRANSLATED = "translated"
# A function taking fewer gaps than the source's still satisfies `Words`; this checks the other direction.
GAP_SET_CHECK = (
    f"// A translation that leaves out a gap of its source fails here.\n({{}} as Words) satisfies typeof {TRANSLATED};"
)


def header(language: LanguageTag) -> str:
    return f"// Generated from the {language.value} catalog by design-catalogs. Do not edit."


def quoted(text: str) -> str:
    return json.dumps(text, ensure_ascii=False)


def reference(name: str, *, family: bool) -> str:
    if name != COUNT:
        return f"gaps.{name}"
    return f"{NUMBER_FORMAT}.format({COUNT if family else f'gaps.{COUNT}'})"


def expression(pieces: tuple[Piece, ...], *, family: bool = False) -> str:
    # Literal parts are JSON strings, so no catalog text can leave its string literal.
    return " + ".join(
        quoted(piece) if isinstance(piece, str) else reference(piece.name, family=family) for piece in pieces
    )


def gap_field(name: str) -> str:
    return f"readonly {name}: {'number' if name == COUNT else 'string'}"


def gap_parameter(names: Iterable[str]) -> str:
    return f"gaps: {{ {'; '.join(map(gap_field, names))} }}"


def family_parameters(family: Family) -> str:
    """The count, and the gaps beside it where the family has any: the count is no field of the gaps."""
    further = sorted(family.gaps - {COUNT})
    return f"{COUNT}: number, {gap_parameter(further)}" if further else f"{COUNT}: number"


def word_type(word: Entry | Family) -> str:
    if isinstance(word, Family):
        return f"({family_parameters(word)}) => string"
    names = sorted(gap_names(pieces_of(word.text)))
    return f"({gap_parameter(names)}) => string" if names else "string"


def family_value(family: Family) -> str:
    """The function choosing the sentence of the category `Intl.PluralRules` gives the count.

    Every category has a row, so a category the family lacks falls back to its `other` sentence without a branch.
    """
    texts = family.texts
    rows = "".join(
        f"        {category}: {expression(pieces_of(texts.get(category, texts[PluralCategory.OTHER])), family=True)},\n"
        for category in PluralCategory
    )
    return f"({family_parameters(family)}) => ({{\n{rows}    }})[{PLURAL_RULES}.select({COUNT})]"


def word_value(word: Entry | Family) -> str:
    if isinstance(word, Family):
        return family_value(word)
    pieces = pieces_of(word.text)
    if gap_names(pieces):
        return f"({gap_parameter(sorted(gap_names(pieces)))}) => {expression(pieces)}"
    return quoted("".join(piece for piece in pieces if isinstance(piece, str)))


def word_lines(words: tuple[Entry | Family, ...]) -> str:
    return "".join(f"    {quoted(word.key.value)}: {word_value(word)},\n" for word in words)


def formats_count(word: Entry | Family) -> bool:
    gaps = word.gaps if isinstance(word, Family) else gap_names(pieces_of(word.text))
    return COUNT in gaps


def helper_lines(language: LanguageTag, words: tuple[Entry | Family, ...]) -> str:
    """The number format and the plural rules of the module, each written once and only where a word uses it."""
    tag = quoted(language.value)
    number_format = f"const {NUMBER_FORMAT} = new Intl.NumberFormat({tag});\n"
    plural_rules = f"const {PLURAL_RULES} = new Intl.PluralRules({tag});\n"
    return (number_format if any(map(formats_count, words)) else "") + (
        plural_rules if any(isinstance(word, Family) for word in words) else ""
    )


def render(catalog: SourceCatalog) -> str:
    words = words_of(catalog.entries)
    type_lines = "".join(f"    readonly {quoted(word.key.value)}: {word_type(word)};\n" for word in words)
    return (
        f"{header(catalog.language)}\n\n"
        f"export const language = {quoted(catalog.language.value)};\n"
        f"{helper_lines(catalog.language, words)}"
        f"{PRETTIER_IGNORE}\n"
        f"export type Words = {{\n{type_lines}}};\n"
        f"{PRETTIER_IGNORE}\n"
        f"export const words: Words = {{\n{word_lines(words)}}};\n"
        "export type Key = keyof Words;\n"
    )


def words_declaration(words: tuple[Entry | Family, ...]) -> str:
    """The words typed as `Words`; where a word is a function, also checked for a gap it leaves out."""
    if any(isinstance(word, Family) or gap_names(pieces_of(word.text)) for word in words):
        return (
            f"const {TRANSLATED} = {{\n{word_lines(words)}}} satisfies Words;\n"
            f"{GAP_SET_CHECK}\n"
            f"export const words: Words = {TRANSLATED};\n"
        )
    return f"export const words: Words = {{\n{word_lines(words)}}};\n"


def render_translation(catalog: TranslationCatalog, source: LanguageTag) -> str:
    """The module of a translation, typed by the source module's `Words` so a wrong key set fails the type check."""
    words = words_of(catalog.entries)
    return (
        f"{header(catalog.language)}\n\n"
        f"import type {{ Words }} from {quoted(f'./{source.value}')};\n"
        f"{helper_lines(catalog.language, words)}"
        f"{PRETTIER_IGNORE}\n"
        f"{words_declaration(words)}"
    )
