"""The Python module of every catalog: the keys and languages as types, the words and the lookup."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from design.catalogs.catalog import SourceCatalog, TranslationCatalog

HEADER = "# Generated from the catalogs by design-catalogs. Do not edit."
# `ruff format` rewrites `repr`'s single quotes and folds a one-element subscript onto one line despite its
# trailing comma, so the module keeps the layout this renderer gives it.
KEEP_LAYOUT = "# fmt: off"


def _lines(items: Iterable[str], indent: int = 1) -> str:
    return "".join(f"{'    ' * indent}{item},\n" for item in items)


def _words(catalog: SourceCatalog | TranslationCatalog) -> str:
    entries = _lines((f"{entry.key.value!r}: {entry.text!r}" for entry in catalog.entries), indent=2)
    return f"    {catalog.language.value!r}: {{\n{entries}    }},\n"


def render(source: SourceCatalog, translations: Sequence[TranslationCatalog]) -> str:
    """The module of the source and its translations, in this order, every text `repr`-quoted."""
    languages = _lines(repr(catalog.language.value) for catalog in (source, *translations))
    keys = tuple(entry.key.value for entry in source.entries)
    words = "".join(map(_words, (source, *translations)))
    key_type = f"Literal[\n{_lines(map(repr, keys))}]" if keys else "Never"
    return (
        f"{HEADER}\n{KEEP_LAYOUT}\n"
        f"from typing import TYPE_CHECKING, Final, Literal{'' if keys else ', Never'}\n\n"
        "if TYPE_CHECKING:\n"
        "    from collections.abc import Mapping\n\n"
        f"type Key = {key_type}\n"
        f"type Language = Literal[\n{languages}]\n\n"
        f"SOURCE_LANGUAGE: Final[Language] = {source.language.value!r}\n"
        f"LANGUAGES: Final[tuple[Language, ...]] = (\n{languages})\n"
        f"WORDS: Final[Mapping[Language, Mapping[Key, str]]] = {{\n{words}}}\n\n\n"
        "def text(language: Language, key: Key) -> str:\n"
        "    return WORDS[language][key]\n"
    )
