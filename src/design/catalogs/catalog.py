"""The source catalog as typed, immutable records, and the checks that make it valid."""

import re
from dataclasses import dataclass
from enum import StrEnum
from string import Formatter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping


class PluralCategory(StrEnum):
    """The CLDR plural categories, in the order of CLDR's table."""

    ZERO = "zero"
    ONE = "one"
    TWO = "two"
    FEW = "few"
    MANY = "many"
    OTHER = "other"


PluralCategories = frozenset[PluralCategory]
PLAIN_KEY = r"[a-z][a-zA-Z0-9]*\.[a-z][a-zA-Z0-9]*"
CATEGORY_PATTERN = rf"\.(?:{'|'.join(PluralCategory)})"
KEY_PATTERN = re.compile(rf"{PLAIN_KEY}(?:{CATEGORY_PATTERN})?")
FAMILY_ENTRY_PATTERN = re.compile(rf"{PLAIN_KEY}{CATEGORY_PATTERN}")
PLAIN_KEY_PATTERN = re.compile(PLAIN_KEY)
LANGUAGE_SUBTAG = re.compile(r"[a-z]{2,3}", re.ASCII)
SCRIPT_SUBTAG = re.compile(r"[A-Z][a-z]{3}", re.ASCII)
REGION_SUBTAG = re.compile(r"[A-Z]{2}|\d{3}", re.ASCII)
VARIANT_SUBTAG = re.compile(r"[a-z0-9]{5,8}|\d[a-z0-9]{3}", re.ASCII)
PLURAL_PROBLEM = "uses msgid_plural; gettext plural forms are not used"
# In an object literal a property of this name sets the prototype, so a consumer's value would not stay data.
PROTOTYPE_GAP = "__proto__"
# A gap with this name is a number. A plural family's sentence may leave it out ("Ein Platz" beside "{count} Plätze").
COUNT = "count"


@dataclass(frozen=True)
class Key:
    """A catalog key: a surface, a dot, a camelCase name and for a plural family's entry a dot and its category."""

    value: str

    def __post_init__(self) -> None:
        if not KEY_PATTERN.fullmatch(self.value):
            raise ValueError(
                f"{self.value!r} is not a key of the form surface.camelCase with an optional plural category"
            )

    @property
    def category(self) -> PluralCategory | None:
        _surface, _name, *category = self.value.split(".")
        return PluralCategory(category[0]) if category else None

    @property
    def family(self) -> Key:
        """The key without its category: the key of the plural family this entry belongs to, a plain key's own."""
        return Key(".".join(self.value.split(".")[:2]))


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
class PluralBranch:
    """One line of a language's plural rule for whole counts: a count takes `category` where `condition` holds.

    The condition is a Python expression over `n`, the absolute count.
    """

    category: PluralCategory
    condition: str


PluralRule = tuple[PluralBranch, ...]


@dataclass(frozen=True)
class Gap:
    """A `{name}` in a text: the place a value is filled in."""

    name: str


@dataclass(frozen=True)
class Marker:
    """A `{#name}` that opens or a `{/name}` that closes a part the page sets apart."""

    name: str
    closing: bool = False

    def __str__(self) -> str:
        return f"{{{'/' if self.closing else '#'}{self.name}}}"


Piece = str | Gap | Marker
CLOSING_SIGN = "/"
MARKER_SIGNS = f"#{CLOSING_SIGN}"


def _gap(field: str, piece: str) -> Gap:
    if not field.isidentifier() or piece != "{" + field + "}":
        raise ValueError(f"gap {piece} is not a plain name")
    if field == PROTOTYPE_GAP:
        raise ValueError(f"gap {piece} is refused: in an object literal {PROTOTYPE_GAP} sets the prototype, not a gap")
    return Gap(field)


def _marker(piece: str) -> Marker:
    name = piece[2:-1]
    if not name.isidentifier():
        raise ValueError(f"marker {piece} is not a plain name")
    return Marker(name, closing=piece[1] == CLOSING_SIGN)


def _check_parts(pieces: tuple[Piece, ...]) -> None:
    """Every marked part is opened, closed by its own marker, not empty and holds no other marker."""
    opened: Marker | None = None
    content: list[Piece] = []
    for piece in pieces:
        if not isinstance(piece, Marker):
            content.append(piece)
        elif opened is None:
            if piece.closing:
                raise ValueError(f"marker {piece} closes no part")
            opened, content = piece, []
        elif piece.closing and piece.name == opened.name:
            if not any(isinstance(item, Gap) or item.strip() for item in content):
                raise ValueError(f"the part {opened} is empty")
            opened = None
        else:
            raise ValueError(f"marker {piece} comes inside the part {opened}; parts do not nest or cross")
    if opened is not None:
        raise ValueError(f"the part {opened} is never closed")


def pieces_of(text: str) -> tuple[Piece, ...]:
    """A text as its literals, gaps and markers in order; `{{` and `}}` are literal braces, as in `str.format`.

    Only `{name}` with a plain identifier is a gap and only `{#name}` and `{/name}` are markers, each part closed
    by its own marker: a format spec, a conversion, a number, an attribute, an item, an option, a standalone marker
    or a marker out of place is refused, naming the piece.
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
        found = _marker(piece) if piece[1] in MARKER_SIGNS else _gap(field, piece)
        position += len(piece)
        if literal:
            pieces.append(literal)
            literal = ""
        pieces.append(found)
    if literal:
        pieces.append(literal)
    _check_parts(tuple(pieces))
    return tuple(pieces)


def gap_names(pieces: tuple[Piece, ...]) -> frozenset[str]:
    return frozenset(piece.name for piece in pieces if isinstance(piece, Gap))


def markers_of(pieces: tuple[Piece, ...]) -> tuple[str, ...]:
    """The names of the marked parts of a text, sorted, a name once for every part that carries it."""
    return tuple(sorted(piece.name for piece in pieces if isinstance(piece, Marker) and not piece.closing))


def without_markers(text: str) -> str:
    """The text as it reads with its marked parts unmarked, everything else as written."""
    return "".join(
        piece.replace("{", "{{").replace("}", "}}") if isinstance(piece, str) else f"{{{piece.name}}}"
        for piece in pieces_of(text)
        if not isinstance(piece, Marker)
    )


def _gaps_text(names: frozenset[str]) -> str:
    return f"the gaps {{{', '.join(sorted(names))}}}" if names else "no gaps"


def _markers_text(names: tuple[str, ...]) -> str:
    return f"the markers {{{', '.join(f'#{name}' for name in names)}}}" if names else "no markers"


def _family_gaps(names: frozenset[str]) -> frozenset[str]:
    """The gaps of a plural family's entry that must agree across its entries and languages: all but `count`."""
    return names - {COUNT}


def _same_gaps(left: frozenset[str], right: frozenset[str], *, family: bool) -> bool:
    return _family_gaps(left) == _family_gaps(right) if family else left == right


def _piece_problems(text: str, source_text: str | None = None, *, family: bool = False) -> list[str]:
    """What is wrong with the gaps and markers of `text`: a malformed one and, given the source's text, a gap set
    or a marker multiset that differs."""
    try:
        pieces = pieces_of(text)
    except ValueError as error:
        return [f"is malformed: {error}"]
    if source_text is None:
        return []
    source_pieces = pieces_of(source_text)
    problems: list[str] = []
    if not _same_gaps(gap_names(source_pieces), gap_names(pieces), family=family):
        problems.append(f"has {_gaps_text(gap_names(pieces))}; the source has {_gaps_text(gap_names(source_pieces))}")
    if markers_of(source_pieces) != markers_of(pieces):
        problems.append(
            f"has {_markers_text(markers_of(pieces))}; the source has {_markers_text(markers_of(source_pieces))}"
        )
    return problems


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

    @property
    def holds_family(self) -> bool:
        return any(
            entry.context is not None and FAMILY_ENTRY_PATTERN.fullmatch(entry.context) for entry in self.entries
        )


@dataclass(frozen=True)
class Entry:
    key: Key
    text: str


@dataclass(frozen=True)
class Family:
    """The entries of one plural family: whole sentences, one per category, that share their gaps."""

    key: Key
    entries: tuple[Entry, ...]

    @property
    def texts(self) -> Mapping[PluralCategory, str]:
        return {entry.key.category: entry.text for entry in self.entries if entry.key.category}

    @property
    def gaps(self) -> frozenset[str]:
        return frozenset().union(*(gap_names(pieces_of(entry.text)) for entry in self.entries))

    @property
    def markers(self) -> tuple[str, ...]:
        """The marker names of the family's entries, sorted, a name once: its entries carry the same markers."""
        return tuple(sorted(set().union(*(markers_of(pieces_of(entry.text)) for entry in self.entries))))


def words_of(entries: tuple[Entry, ...]) -> tuple[Entry | Family, ...]:
    """The words a module holds: a plain entry, and a plural family once, at the place of its first entry."""
    members: dict[Key, list[Entry]] = {}
    for entry in entries:
        if entry.key.category:
            members.setdefault(entry.key.family, []).append(entry)
    words: list[Entry | Family] = []
    for entry in entries:
        if not entry.key.category:
            words.append(entry)
        elif entry.key.family in members:
            words.append(Family(entry.key.family, tuple(members.pop(entry.key.family))))
    return tuple(words)


@dataclass(frozen=True)
class SourceCatalog:
    language: LanguageTag
    entries: tuple[Entry, ...]

    @property
    def holds_family(self) -> bool:
        return any(entry.key.category for entry in self.entries)


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


def _key_problem(context: str) -> str:
    """Why a `msgctxt` is no key; for a surface.name with a third part, the plural categories there are."""
    surface_name, _, last = context.rpartition(".")
    problem = "is not a key of the form surface.camelCase"
    if PLAIN_KEY_PATTERN.fullmatch(surface_name):
        return f"{problem}; {last!r} is no plural category, the categories are {', '.join(PluralCategory)}"
    return problem


def _checked_entries(
    file: str, raw_entries: tuple[RawEntry, ...], entry_problems: Callable[[Key, RawEntry], list[str]]
) -> tuple[tuple[tuple[Key, RawEntry], ...], tuple[Finding, ...], frozenset[Key]]:
    """The entries without a problem, a finding for every problem of the others and the key of every entry that has one.

    `entry_problems` adds what only the source or only a translation requires.
    """
    valid: list[tuple[Key, RawEntry]] = []
    findings: list[Finding] = []
    seen: set[str] = set()
    present: set[Key] = set()
    for raw in raw_entries:
        if raw.context is None:
            findings.append(Finding(file, raw.text, "has no msgctxt"))
            continue
        try:
            key = Key(raw.context)
        except ValueError:
            findings.append(Finding(file, raw.context, _key_problem(raw.context)))
            continue
        present.add(key)
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
    return tuple(valid), tuple(findings), frozenset(present)


def _held_categories(keys: frozenset[Key]) -> dict[Key, frozenset[PluralCategory]]:
    """The categories each plural family holds among `keys`."""
    held: dict[Key, set[PluralCategory]] = {}
    for key in keys:
        if key.category:
            held.setdefault(key.family, set()).add(key.category)
    return {family: frozenset(categories) for family, categories in held.items()}


def _plain_key_findings(file: str, present: frozenset[Key]) -> list[Finding]:
    return [
        Finding(file, family.value, "is a plain key and a plural family")
        for family in _held_categories(present)
        if family in present
    ]


def _takes(language: LanguageTag, categories: PluralCategories) -> str:
    return f"{language.value} takes {', '.join(category for category in PluralCategory if category in categories)}"


def _category_findings(
    file: str,
    language: LanguageTag,
    family: Key,
    held: PluralCategories,
    needed: PluralCategories,
    missing_problem: Callable[[PluralCategory], str],
) -> list[Finding]:
    """A finding for every category of the family that its language needs and it lacks, or has and does not need."""
    return [
        Finding(
            file,
            f"{family.value}.{category}",
            missing_problem(category)
            if category in needed
            else f"is not a plural category; {_takes(language, needed)}",
        )
        for category in PluralCategory
        if (category in needed) != (category in held)
    ]


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
    file: str, language: LanguageTag, categories: PluralCategories, raw_entries: tuple[RawEntry, ...]
) -> tuple[SourceCatalog, tuple[Finding, ...]]:
    """The catalog of the valid entries and a finding for every problem of the others, plural families included:
    each holds the categories of the source language and the same gaps in every entry."""

    def source_problems(_key: Key, raw: RawEntry) -> list[str]:
        return [
            problem
            for found, problem in (
                (raw.translation != "", "has a msgstr; the source holds its text in msgid only"),
                (raw.text == "", "has an empty msgid"),
            )
            if found
        ] + _piece_problems(raw.text)

    valid, findings, present = _checked_entries(file, raw_entries, source_problems)
    entries = tuple(Entry(key, raw.text) for key, raw in valid)
    family_findings = [
        finding
        for family, held in _held_categories(present).items()
        for finding in _category_findings(
            file,
            language,
            family,
            held,
            categories,
            lambda _category: f"is missing; {_takes(language, categories)}",
        )
    ]
    return SourceCatalog(language, entries), (
        *findings,
        *_plain_key_findings(file, present),
        *family_findings,
        *_family_findings(file, entries),
    )


def _family_findings(file: str, entries: tuple[Entry, ...]) -> list[Finding]:
    """A finding for every family whose entries differ in a gap besides `count` or in a marker, naming each set."""
    findings: list[Finding] = []
    for word in words_of(entries):
        if isinstance(word, Entry):
            continue
        pieces = {entry.key.category: pieces_of(entry.text) for entry in word.entries}
        gaps = {category: gap_names(found) for category, found in pieces.items()}
        if len({_family_gaps(names) for names in gaps.values()}) > 1:
            named = ", ".join(f"{category} has {_gaps_text(names)}" for category, names in gaps.items())
            findings.append(Finding(file, word.key.value, f"has different gaps in its entries: {named}"))
        markers = {category: markers_of(found) for category, found in pieces.items()}
        if len(set(markers.values())) > 1:
            named = ", ".join(f"{category} has {_markers_text(names)}" for category, names in markers.items())
            findings.append(Finding(file, word.key.value, f"has different markers in its entries: {named}"))
    return findings


def _source_text(source_texts: Mapping[str, str], key: Key) -> str | None:
    """The source's text for a key; for a category the source lacks, its `other` text."""
    exact = source_texts.get(key.value)
    if exact is not None or key.category is None:
        return exact
    return source_texts.get(f"{key.family.value}.{PluralCategory.OTHER}")


def read_translation(
    file: str,
    language: LanguageTag,
    categories: PluralCategories,
    raw_entries: tuple[RawEntry, ...],
    source: SourceCatalog,
) -> tuple[TranslationCatalog, tuple[Finding, ...]]:
    """The valid entries in the source's order, and a finding for every key the source lacks or has and the
    translation lacks, every empty entry and every entry translated from another text than the source's current one.

    A plural family holds the categories of its own language; a category the source lacks is judged against the
    source's `other` text.
    """
    source_texts = {entry.key.value: entry.text for entry in source.entries}

    def translation_problems(key: Key, raw: RawEntry) -> list[str]:
        expected = _source_text(source_texts, key)
        if expected is None:
            return ["is not a key of the source"]
        problems = [
            problem
            for found, problem in (
                (not raw.translation.strip(), "has an empty msgstr"),
                (
                    raw.text != expected,
                    f"was translated from {raw.text!r}; the source now reads {expected!r}",
                ),
            )
            if found
        ]
        if raw.translation.strip():
            problems.extend(_piece_problems(raw.translation, expected, family=key.category is not None))
        return problems

    valid, findings, present = _checked_entries(file, raw_entries, translation_problems)
    translated = {key.value: Entry(key, raw.translation) for key, raw in valid}
    held = _held_categories(present)
    missing: list[Finding] = []
    entries: list[Entry] = []
    for word in words_of(source.entries):
        if isinstance(word, Entry):
            names = [word.key.value]
            if word.key not in present:
                missing.append(Finding(file, word.key.value, f"is missing; the source has {word.text!r}"))
        else:
            names = [f"{word.key.value}.{category}" for category in PluralCategory]

            def source_has(category: PluralCategory, family: Key = word.key) -> str:
                return f"is missing; the source has {_source_text(source_texts, Key(f'{family.value}.{category}'))!r}"

            missing.extend(
                _category_findings(file, language, word.key, held.get(word.key, frozenset()), categories, source_has)
            )
        entries.extend(translated[name] for name in names if name in translated)
    return TranslationCatalog(language, tuple(entries)), (*findings, *missing)
