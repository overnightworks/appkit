"""The source catalog as typed, immutable records, and the checks that make it valid."""

import re
from dataclasses import dataclass
from string import Formatter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

KEY_PATTERN = re.compile(r"[a-z][a-zA-Z0-9]*\.[a-z][a-zA-Z0-9]*")
LANGUAGE_SUBTAG = re.compile(r"[a-z]{2,3}", re.ASCII)
SCRIPT_SUBTAG = re.compile(r"[A-Z][a-z]{3}", re.ASCII)
REGION_SUBTAG = re.compile(r"[A-Z]{2}|\d{3}", re.ASCII)
VARIANT_SUBTAG = re.compile(r"[a-z0-9]{5,8}|\d[a-z0-9]{3}", re.ASCII)
PLURAL_PROBLEM = "uses msgid_plural; gettext plural forms are not used"


@dataclass(frozen=True)
class Key:
    """A catalog key: a surface, a dot and a camelCase name."""

    value: str

    def __post_init__(self) -> None:
        if not KEY_PATTERN.fullmatch(self.value):
            raise ValueError(f"{self.value!r} is not a key of the form surface.camelCase")


def _is_language_tag(value: str) -> bool:
    """BCP 47 as far as a file name needs it: a two or three letter language, then script, region and variants."""
    language, *subtags = value.split("-")
    if not LANGUAGE_SUBTAG.fullmatch(language):
        return False
    if subtags and SCRIPT_SUBTAG.fullmatch(subtags[0]):
        subtags = subtags[1:]
    if subtags and REGION_SUBTAG.fullmatch(subtags[0]):
        subtags = subtags[1:]
    return all(VARIANT_SUBTAG.fullmatch(subtag) for subtag in subtags)


@dataclass(frozen=True)
class LanguageTag:
    """A language tag such as de or pt-BR; a catalog's file stem, its Language header and its module name."""

    value: str

    def __post_init__(self) -> None:
        if not _is_language_tag(self.value):
            raise ValueError(f"{self.value!r} is not a language tag such as de or pt-BR")


@dataclass(frozen=True)
class Gap:
    """A `{name}` in a text: the place a value is filled in."""

    name: str


Piece = str | Gap


def pieces_of(text: str) -> tuple[Piece, ...]:
    """A text as its literals and gaps in order; `{{` and `}}` are literal braces, as in `str.format`.

    Only `{name}` with a plain identifier is a gap: a format spec, a conversion, a number, an attribute or an
    item is refused, naming the piece.
    """
    try:
        parsed = tuple(Formatter().parse(text))
    except ValueError as error:
        raise ValueError(f"unbalanced brace: {error}") from error
    pieces: list[Piece] = []
    literal = ""
    position = 0
    for text_before, field, _spec, _conversion in parsed:
        literal += text_before
        position += len(text_before.replace("{", "{{").replace("}", "}}"))
        if field is None:
            continue
        # The parser reports an empty format spec like none, so the written piece itself is compared.
        piece = text[position : text.index("}", position) + 1]
        if not field.isidentifier() or piece != "{" + field + "}":
            raise ValueError(f"gap {piece} is not a plain name")
        position += len(piece)
        if literal:
            pieces.append(literal)
            literal = ""
        pieces.append(Gap(field))
    if literal:
        pieces.append(literal)
    return tuple(pieces)


def gap_names(pieces: tuple[Piece, ...]) -> frozenset[str]:
    return frozenset(piece.name for piece in pieces if isinstance(piece, Gap))


def _gaps_text(names: frozenset[str]) -> str:
    return f"{{{', '.join(sorted(names))}}}" if names else "none"


def _gap_problems(text: str, source_text: str | None = None) -> list[str]:
    """What is wrong with the gaps of `text`: a malformed gap and, given the source's text, a gap set that differs."""
    try:
        names = gap_names(pieces_of(text))
    except ValueError as error:
        return [f"is malformed: {error}"]
    if source_text is None or (source_names := gap_names(pieces_of(source_text))) == names:
        return []
    return [f"has the gaps {_gaps_text(names)}; the source has {_gaps_text(source_names)}"]


@dataclass(frozen=True)
class RawEntry:
    """One entry as the catalog file holds it, before any check."""

    context: str | None
    text: str
    translation: str
    fuzzy: bool
    plural: bool


@dataclass(frozen=True)
class RawCatalog:
    """A catalog file as it reads: the language its header names (None when it names none) and its entries."""

    language: str | None
    entries: tuple[RawEntry, ...]


@dataclass(frozen=True)
class Entry:
    key: Key
    text: str


@dataclass(frozen=True)
class SourceCatalog:
    language: LanguageTag
    entries: tuple[Entry, ...]


@dataclass(frozen=True)
class TranslationCatalog:
    """The valid entries of one translation, in the source's order, each holding the translated text."""

    language: LanguageTag
    entries: tuple[Entry, ...]


@dataclass(frozen=True)
class Finding:
    """One broken entry: the catalog file, the key (or the text when there is no key) and what is wrong."""

    file: str
    key: str
    problem: str

    def __str__(self) -> str:
        return f"{self.file}: {self.key} {self.problem}"


def _checked_entries(
    file: str, raw_entries: tuple[RawEntry, ...], entry_problems: Callable[[Key, RawEntry], list[str]]
) -> tuple[tuple[tuple[Key, RawEntry], ...], tuple[Finding, ...]]:
    """The entries without a problem and a finding for every problem of the others.

    `entry_problems` adds what only the source or only a translation requires.
    """
    valid: list[tuple[Key, RawEntry]] = []
    findings: list[Finding] = []
    seen: set[str] = set()
    for raw in raw_entries:
        if raw.context is None:
            findings.append(Finding(file, raw.text, "has no msgctxt"))
            continue
        try:
            key = Key(raw.context)
        except ValueError:
            findings.append(Finding(file, raw.context, "is not a key of the form surface.camelCase"))
            continue
        problems = [
            problem
            for found, problem in (
                (raw.context in seen, "is a duplicate"),
                (raw.fuzzy, "is fuzzy"),
                (raw.plural, PLURAL_PROBLEM),
            )
            if found
        ]
        if not raw.plural:
            problems.extend(entry_problems(key, raw))
        seen.add(raw.context)
        findings.extend(Finding(file, raw.context, problem) for problem in problems)
        if not problems:
            valid.append((key, raw))
    return tuple(valid), tuple(findings)


def read_language(file: str, stem: str, header: str | None) -> tuple[LanguageTag | None, tuple[Finding, ...]]:
    """The language a catalog's file name gives, and a finding when the name or the Language header does not fit."""
    try:
        language = LanguageTag(stem)
    except ValueError as error:
        return None, (Finding(file, "the file name", str(error)),)
    if header == stem:
        return language, ()
    problem = f"is {header!r}; the file name says {stem!r}" if header else f"is missing; the file name says {stem!r}"
    return language, (Finding(file, "the Language header", problem),)


def read_source(
    file: str, language: LanguageTag, raw_entries: tuple[RawEntry, ...]
) -> tuple[SourceCatalog, tuple[Finding, ...]]:
    """The catalog of the valid entries and a finding for every problem of the others."""

    def source_problems(_key: Key, raw: RawEntry) -> list[str]:
        return [
            problem
            for found, problem in (
                (raw.translation != "", "has a msgstr; the source holds its text in msgid only"),
                (raw.text == "", "has an empty msgid"),
            )
            if found
        ] + _gap_problems(raw.text)

    valid, findings = _checked_entries(file, raw_entries, source_problems)
    return SourceCatalog(language, tuple(Entry(key, raw.text) for key, raw in valid)), findings


def read_translation(
    file: str, language: LanguageTag, raw_entries: tuple[RawEntry, ...], source: SourceCatalog
) -> tuple[TranslationCatalog, tuple[Finding, ...]]:
    """The valid entries in the source's order, and a finding for every key the source lacks or has and the
    translation lacks, every empty entry and every entry translated from another text than the source's current one."""
    source_texts = {entry.key.value: entry.text for entry in source.entries}

    def translation_problems(key: Key, raw: RawEntry) -> list[str]:
        if key.value not in source_texts:
            return ["is not a key of the source"]
        problems = [
            problem
            for found, problem in (
                (not raw.translation.strip(), "has an empty msgstr"),
                (
                    raw.text != source_texts[key.value],
                    f"was translated from {raw.text!r}; the source now reads {source_texts[key.value]!r}",
                ),
            )
            if found
        ]
        if raw.translation.strip():
            problems.extend(_gap_problems(raw.translation, source_texts[key.value]))
        return problems

    valid, findings = _checked_entries(file, raw_entries, translation_problems)
    translated = {key.value: Entry(key, raw.translation) for key, raw in valid}
    present = {raw.context for raw in raw_entries}
    missing = tuple(
        Finding(file, entry.key.value, f"is missing; the source has {entry.text!r}")
        for entry in source.entries
        if entry.key.value not in present
    )
    entries = tuple(translated[entry.key.value] for entry in source.entries if entry.key.value in translated)
    return TranslationCatalog(language, entries), (*findings, *missing)
