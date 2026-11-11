"""The entries a translation holds once it follows its source by key."""

from typing import TYPE_CHECKING

from design.catalogs.catalog import PLURAL_PROBLEM, Entry, Finding, PluralCategory, RawEntry, words_of

if TYPE_CHECKING:
    from design.catalogs.catalog import PluralCategories, SourceCatalog


def structural_findings(file: str, raw_entries: tuple[RawEntry, ...]) -> tuple[Finding, ...]:
    """A finding for an entry without a key, a repeated key or a gettext plural: the sync never drops one silently."""
    findings: list[Finding] = []
    seen: set[str] = set()
    for raw in raw_entries:
        if raw.context is None:
            findings.append(Finding(file, raw.text, "has no msgctxt"))
            continue
        if raw.context in seen:
            findings.append(Finding(file, raw.context, "is a duplicate"))
        seen.add(raw.context)
        if raw.plural:
            findings.append(Finding(file, raw.context, PLURAL_PROBLEM))
    return tuple(findings)


def _expected_texts(source: SourceCatalog, categories: PluralCategories) -> dict[str, str]:
    """The source text each key of a translation takes, in the source's order.

    A family holds the categories of the language; one the source lacks takes the source's `other` text.
    """
    expected: dict[str, str] = {}
    for word in words_of(source.entries):
        if isinstance(word, Entry):
            expected[word.key.value] = word.text
            continue
        texts = word.texts
        for category in PluralCategory:
            if category in categories:
                expected[f"{word.key.value}.{category}"] = texts.get(category, texts[PluralCategory.OTHER])
    return expected


def _order(held: list[str], expected: list[str]) -> list[str]:
    """The keys the translation keeps, in its order, and each new one right after its predecessor in the source."""
    wanted = set(expected)
    ordered = [key for key in held if key in wanted]
    placed = set(ordered)
    for position, key in enumerate(expected):
        if key not in placed:
            ordered.insert(ordered.index(expected[position - 1]) + 1 if position else 0, key)
            placed.add(key)
    return ordered


def sync_translation(
    source: SourceCatalog, categories: PluralCategories, raw_entries: tuple[RawEntry, ...]
) -> tuple[RawEntry, ...]:
    """The entries of a translation in line with the source, by key and never by text.

    A missing key comes with the source text as `msgid` and an empty `msgstr`. A changed source text becomes the
    `msgid`; the old `msgstr` stays and the entry is marked fuzzy. A key the source dropped is removed, and a family
    holds exactly the `categories` of the language.
    """
    expected = _expected_texts(source, categories)
    held = {raw.context: raw for raw in raw_entries}
    synced: list[RawEntry] = []
    for key in _order([raw.context for raw in raw_entries if raw.context], list(expected)):
        raw = held.get(key)
        if raw is None:
            synced.append(RawEntry(key, expected[key], "", fuzzy=False, plural=False))
        elif raw.text != expected[key]:
            synced.append(RawEntry(key, expected[key], raw.translation, fuzzy=True, plural=False))
        else:
            synced.append(raw)
    return tuple(synced)
