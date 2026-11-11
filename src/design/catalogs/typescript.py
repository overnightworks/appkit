"""The typed TypeScript module of a source catalog."""

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from design.catalogs.catalog import SourceCatalog

HEADER = "// Generated from the source catalog by design-catalogs. Do not edit."
# The module is laid out by this renderer; prettier would reflow its objects.
PRETTIER_IGNORE = "// prettier-ignore"


def quoted(text: str) -> str:
    return json.dumps(text, ensure_ascii=False)


def render(catalog: SourceCatalog) -> str:
    type_lines = "".join(f"    readonly {quoted(entry.key.value)}: string;\n" for entry in catalog.entries)
    word_lines = "".join(f"    {quoted(entry.key.value)}: {quoted(entry.text)},\n" for entry in catalog.entries)
    return (
        f"{HEADER}\n\n"
        f"export const language = {quoted(catalog.language.value)};\n"
        f"{PRETTIER_IGNORE}\n"
        f"export type Words = {{\n{type_lines}}};\n"
        f"{PRETTIER_IGNORE}\n"
        f"export const words: Words = {{\n{word_lines}}};\n"
        "export type Key = keyof Words;\n"
    )
