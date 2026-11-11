"""The boundary to Babel and the filesystem: catalogs and plural rules are read, generated modules read and written."""

import re
from io import BytesIO
from typing import TYPE_CHECKING

from babel import Locale, UnknownLocaleError
from babel.messages.catalog import Catalog, Message
from babel.messages.pofile import PoFileError, PoFileParser

from design.catalogs.catalog import LanguageTag, PluralCategories, PluralCategory, RawCatalog, RawEntry

if TYPE_CHECKING:
    from pathlib import Path


STRING_LINE = re.compile(rb'^(?:msg\w+(?:\[\d+\])?\s+)?"(?:[^"\\]|\\.)*"')
LANGUAGE_FIELD = "Language:"


class CatalogFileError(Exception):
    """A catalog file that cannot be read; the message names the file and, when known, the line."""


class _EveryEntry(Catalog):
    """A catalog that keeps every entry in file order.

    Babel's own catalog merges entries with the same msgctxt and msgid, and treats an empty msgid
    as the header, so a duplicate or an empty entry would never reach a check.
    """

    def __init__(self) -> None:
        super().__init__()
        self.entries: list[Message] = []

    def __setitem__(self, id, message: Message) -> None:  # noqa: A002 - Babel's parameter name
        self.entries.append(message)


def _require_closed_strings(path: Path, content: bytes) -> None:
    """Babel cuts the last character off a string whose closing quote is missing, so no error would show."""
    for number, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith((b"msg", b'"')) and not STRING_LINE.fullmatch(stripped):
            raise CatalogFileError(f"{path}:{number}: the string is not closed by a quote")


def _first_form(value: str | tuple[str, ...]) -> str:
    return value if isinstance(value, str) else value[0]


def _header_language(header: str) -> str | None:
    return next(
        (
            line.removeprefix(LANGUAGE_FIELD).strip(" ")
            for line in header.split("\n")
            if line.startswith(LANGUAGE_FIELD)
        ),
        None,
    )


def read_catalog(path: Path) -> RawCatalog:
    catalog = _EveryEntry()
    try:
        content = path.read_bytes()
        content.decode("utf-8")
        _require_closed_strings(path, content)
        PoFileParser(catalog, ignore_obsolete=True, abort_invalid=True).parse(BytesIO(content))
    except FileNotFoundError:
        raise CatalogFileError(f"{path}: the source catalog is missing") from None
    except UnicodeDecodeError:
        raise CatalogFileError(f"{path}: the catalog is not valid UTF-8") from None
    except PoFileError as error:
        problem = error.args[0].removesuffix(f" on {error.lineno}")
        raise CatalogFileError(f"{path}:{error.lineno + 1}: {problem}") from error
    entries = catalog.entries
    language = None
    if entries and entries[0].context is None and not entries[0].id:
        language = _header_language(str(entries[0].string))
        entries = entries[1:]
    return RawCatalog(
        language,
        tuple(
            RawEntry(
                message.context,
                _first_form(message.id),
                _first_form(message.string),
                message.fuzzy,
                plural=not isinstance(message.id, str),
            )
            for message in entries
        ),
    )


def plural_categories(language: LanguageTag) -> PluralCategories:
    """The CLDR plural categories a language needs, as Babel holds them, and `other`."""
    try:
        locale = Locale.parse(language.value, sep="-")
    except UnknownLocaleError:
        raise CatalogFileError(f"{language.value}: Babel has no CLDR plural rules for this language") from None
    return frozenset({PluralCategory.OTHER, *map(PluralCategory, locale.plural_form.tags)})


def list_files(directory: Path) -> tuple[Path, ...]:
    """The files of a directory by name; none when it does not exist."""
    return tuple(sorted(path for path in directory.iterdir() if path.is_file())) if directory.is_dir() else ()


def read_module(path: Path) -> str | None:
    """The text of a generated module, or None when it does not exist."""
    return path.read_text(encoding="utf-8") if path.is_file() else None


def write_module(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
