"""The Python module of every catalog: the keys and languages as types, the words, the plural rules and the lookup."""

from typing import TYPE_CHECKING

from design.catalogs.catalog import Entry, Family, PluralCategory, without_markers, words_of

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Sequence

    from design.catalogs.catalog import LanguageTag, PluralRule, SourceCatalog, TranslationCatalog

    type Catalog = SourceCatalog | TranslationCatalog

HEADER = "# Generated from the catalogs by design-catalogs. Do not edit."
# `ruff format` rewrites `repr`'s single quotes and folds a one-element subscript onto one line despite its
# trailing comma, so the module keeps the layout this renderer gives it.
KEEP_LAYOUT = "# fmt: off"
# The lookup fills the gaps with `str.format`, which reads `{{` and `}}` as the catalog does. The count is written
# as plain digits: the grouping and digits of `Intl.NumberFormat` need the CLDR data of the language at run time.
# `language` and `key` are positional-only, so a gap may carry either name.
LOOKUP = """\


def text(language: Language, key: Key, /, *, count: int | None = None, **gaps: str) -> str:
    if language not in WORDS:
        raise KeyError(f'unknown language {language!r}; the languages are {list(WORDS)}')
    if key not in WORDS[language]:
        family = key.rpartition('.')[0]
        is_family = any(name == family and not isinstance(entry, str) for name, entry in WORDS[language].items())
        hint = f'; a plural family is named by its family key {family!r}' if is_family else ''
        raise KeyError(f'unknown key {key!r}{hint}')
    words = WORDS[language][key]
    if isinstance(words, str):
        sentence, counted = words, False
    elif count is None:
        raise TypeError(f'{key!r} is a plural family: pass count')
    else:
        sentence, counted = words.get(plural_category(language, count), words['other']), True
    values = gaps if count is None else {**gaps, 'count': str(count)}
    named = {name for _, name, _, _ in Formatter().parse(sentence) if name is not None}
    # A family's sentence may leave out the count.
    unknown = values.keys() - named - ({'count'} if counted else set())
    if missing := named - values.keys():
        raise TypeError(f'{key!r} in {language!r} is missing the gaps {sorted(missing)}')
    if unknown:
        raise TypeError(f'{key!r} in {language!r} has no gaps {sorted(unknown)}')
    return sentence.format(**values)
"""


def _lines(items: Iterable[str], indent: int = 1) -> str:
    return "".join(f"{'    ' * indent}{item},\n" for item in items)


def _word(word: Entry | Family) -> str:
    if isinstance(word, Entry):
        return f"{word.key.value!r}: {without_markers(word.text)!r}"
    sentences = _lines(
        (f"{category.value!r}: {without_markers(text)!r}" for category, text in word.texts.items()), indent=3
    )
    return f"{word.key.value!r}: {{\n{sentences}        }}"


def _words(catalog: Catalog) -> str:
    entries = _lines(map(_word, words_of(catalog.entries)), indent=2)
    return f"    {catalog.language.value!r}: {{\n{entries}    }},\n"


def _case(catalog: Catalog, rule: PluralRule) -> str:
    branches = "".join(
        f"            if {branch.condition}:\n                return {branch.category.value!r}\n" for branch in rule
    )
    return f"        case {catalog.language.value!r}:\n{branches}            return {PluralCategory.OTHER.value!r}\n"


def _plural_category(catalogs: Sequence[Catalog], rule_of: Callable[[LanguageTag], PluralRule]) -> str:
    """The function giving the CLDR category of a whole count, one case per language, written from its rule."""
    rules = [rule_of(catalog.language) for catalog in catalogs]
    cases = "".join(_case(catalog, rule) for catalog, rule in zip(catalogs, rules, strict=True))
    absolute = "    n = abs(count)\n" if any(rules) else ""
    return f"def plural_category(language: Language, count: int) -> Category:\n{absolute}    match language:\n{cases}"


def render(
    source: SourceCatalog, translations: Sequence[TranslationCatalog], rule_of: Callable[[LanguageTag], PluralRule]
) -> str:
    """The module of the source and its translations, in this order, every text `repr`-quoted and
    without its markers.

    A plural family is one key; `rule_of` gives the plural rule of a language, which the module holds as code.
    """
    catalogs = (source, *translations)
    languages = _lines(repr(catalog.language.value) for catalog in catalogs)
    keys = tuple(word.key.value for word in words_of(source.entries))
    key_type = f"Literal[\n{_lines(map(repr, keys))}]" if keys else "Never"
    categories = _lines(repr(category.value) for category in PluralCategory)
    # `Final` on WORDS would narrow its type to the literal below, and a catalog without a plural family or without a
    # gap then makes a branch of `text` unnecessary for a strict type checker.
    return (
        f"{HEADER}\n{KEEP_LAYOUT}\n"
        "from string import Formatter\n"
        f"from typing import TYPE_CHECKING, Final, Literal{'' if keys else ', Never'}\n\n"
        "if TYPE_CHECKING:\n"
        "    from collections.abc import Mapping\n\n"
        f"type Key = {key_type}\n"
        f"type Language = Literal[\n{languages}]\n"
        f"type Category = Literal[\n{categories}]\n\n"
        f"SOURCE_LANGUAGE: Final[Language] = {source.language.value!r}\n"
        f"LANGUAGES: Final[tuple[Language, ...]] = (\n{languages})\n"
        "WORDS: Mapping[Language, Mapping[Key, str | Mapping[Category, str]]] = {\n"
        f"{''.join(map(_words, catalogs))}}}\n\n\n"
        f"{_plural_category(catalogs, rule_of)}{LOOKUP}"
    )
