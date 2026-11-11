"""The source catalog as typed, immutable records, and the checks that make it valid."""

import re
from dataclasses import dataclass

KEY_PATTERN = re.compile(r"[a-z][a-zA-Z0-9]*\.[a-z][a-zA-Z0-9]*")
LANGUAGE_TAG_PATTERN = re.compile(r"[a-z]{2,3}(-[A-Za-z0-9]{2,8})*")


@dataclass(frozen=True)
class Key:
    """A catalog key: a surface, a dot and a camelCase name."""

    value: str

    def __post_init__(self) -> None:
        if not KEY_PATTERN.fullmatch(self.value):
            raise ValueError(f"{self.value!r} is not a key of the form surface.camelCase")


@dataclass(frozen=True)
class LanguageTag:
    value: str

    def __post_init__(self) -> None:
        if not LANGUAGE_TAG_PATTERN.fullmatch(self.value):
            raise ValueError(f"{self.value!r} is not a language tag such as de or pt-BR")


@dataclass(frozen=True)
class RawEntry:
    """One entry as the catalog file holds it, before any check."""

    context: str | None
    text: str
    translation: str
    fuzzy: bool


@dataclass(frozen=True)
class Entry:
    key: Key
    text: str


@dataclass(frozen=True)
class SourceCatalog:
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


def read_source(
    file: str, language: LanguageTag, raw_entries: tuple[RawEntry, ...]
) -> tuple[SourceCatalog, tuple[Finding, ...]]:
    """The catalog of the valid entries and a finding for every problem of the others."""
    entries: list[Entry] = []
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
                (raw.translation != "", "has a msgstr; the source holds its text in msgid only"),
                (raw.text == "", "has an empty msgid"),
            )
            if found
        ]
        seen.add(raw.context)
        findings.extend(Finding(file, raw.context, problem) for problem in problems)
        if not problems:
            entries.append(Entry(key, raw.text))
    return SourceCatalog(language, tuple(entries)), tuple(findings)
