"""The boundary to Babel and the filesystem: catalogs and plural rules are read, generated modules read and written."""

import re
from io import BytesIO
from typing import TYPE_CHECKING

from babel import Locale, UnknownLocaleError
from babel.messages.catalog import Catalog, Message
from babel.messages.pofile import PoFileError, PoFileParser, generate_po
from babel.plural import _PythonCompiler

from design.catalogs.catalog import (
    LanguageTag,
    PluralBranch,
    PluralCategories,
    PluralCategory,
    PluralRule,
    RawCatalog,
    RawEntry,
)
from design.catalogs.declaration import TABLE

if TYPE_CHECKING:
    from pathlib import Path


# The operands of a whole count: n and i are the absolute count, the fraction and exponent operands are zero.
WHOLE_COUNT_OPERANDS = {"n": "n", "i": "n", "v": "0", "w": "0", "f": "0", "t": "0", "c": "0", "e": "0"}
STRING_LINE = re.compile(rb'^(?:msg\w+(?:\[\d+\])?\s+)?"(?:[^"\\]|\\.)*"')
LANGUAGE_FIELD = "Language:"
FUZZY = "fuzzy"
# Babel's own width, fixed here so that the layout of a written catalog never depends on a default.
LINE_WIDTH = 76


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


def _parse(path: Path, *, ignore_obsolete: bool) -> tuple[str, _EveryEntry]:
    """The text of a catalog file and its entries, the header first where it has one."""
    catalog = _EveryEntry()
    try:
        content = path.read_bytes()
        text = content.decode("utf-8")
        _require_closed_strings(path, content)
        PoFileParser(catalog, ignore_obsolete=ignore_obsolete, abort_invalid=True).parse(BytesIO(content))
    except FileNotFoundError:
        raise CatalogFileError(f"{path}: the source catalog is missing; {TABLE} source names its language") from None
    except UnicodeDecodeError:
        raise CatalogFileError(f"{path}: the catalog is not valid UTF-8") from None
    except PoFileError as error:
        problem = error.args[0].removesuffix(f" on {error.lineno}")
        raise CatalogFileError(f"{path}:{error.lineno + 1}: {problem}") from error
    return text, catalog


def _holds_header(entries: list[Message]) -> bool:
    return bool(entries) and entries[0].context is None and not entries[0].id


def read_catalog(path: Path) -> RawCatalog:
    _, catalog = _parse(path, ignore_obsolete=True)
    entries = catalog.entries
    language = None
    if _holds_header(entries):
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


def _locale(language: LanguageTag) -> Locale | None:
    try:
        return Locale.parse(language.value, sep="-")
    except UnknownLocaleError:
        return None


def plural_categories(language: LanguageTag, catalog: Path) -> PluralCategories:
    """The CLDR plural categories a language needs, as Babel holds them, and `other`; `catalog` is its file."""
    if (locale := _locale(language)) is None:
        raise CatalogFileError(f"{catalog}: Babel has no CLDR plural rules for {language.value}")
    return frozenset({PluralCategory.OTHER, *map(PluralCategory, locale.plural_form.tags)})


# Babel's rule compiler is private; the extra pins `babel<3` and a test compares its output with `to_python`.
class _WholeCountCompiler(_PythonCompiler):
    """Babel's compiler of a plural rule to Python, for whole counts: the module needs no Babel helper to run it.

    A whole count is its own integer part and has no fraction, so `IN` and `WITHIN` are one range test, the modulo of
    a non-negative count is Python's, and what only the zero operands decide is folded into `True` or `False`.
    """

    def compile(self, arg):
        operand, _ = arg
        return WHOLE_COUNT_OPERANDS[operand] if operand in WHOLE_COUNT_OPERANDS else super().compile(arg)

    def compile_mod(self, left, right):
        left, right = self.compile(left), self.compile(right)
        return str(int(left) % int(right)) if left.isdigit() and right.isdigit() else f"({left} % {right})"

    def compile_and(self, left, right):
        return self._join("and", self.compile(left), self.compile(right), neutral="True")

    def compile_or(self, left, right):
        return self._join("or", self.compile(left), self.compile(right), neutral="False")

    def compile_not(self, relation):
        """CLDR negates a relation only (`!=`, `not in`); a single value reads as `!=`."""
        _operator, (_method, expr, range_list) = relation
        subject, (bound, *further) = self.compile(expr), self._bounds(range_list)
        if not further and bound[0] == bound[1] and not subject.isdigit():
            return f"({subject} != {bound[0]})"
        compiled = self.compile(relation)
        return {"True": "False", "False": "True"}.get(compiled, f"(not {compiled})")

    def compile_relation(self, method, expr, range_list):
        subject, bounds = self.compile(expr), self._bounds(range_list)
        if subject.isdigit():
            return str(any(int(low) <= int(subject) <= int(high) for low, high in bounds))
        tests = (f"{subject} == {low}" if low == high else f"{low} <= {subject} <= {high}" for low, high in bounds)
        return f"({' or '.join(tests)})"

    def _bounds(self, range_list):
        return [(self.compile(low), self.compile(high)) for low, high in range_list[1]]

    @staticmethod
    def _join(operator, left, right, *, neutral):
        """`left` and `right` joined by `and` (neutral `True`) or `or` (neutral `False`); a constant is folded."""
        if neutral in {left, right}:
            return right if left == neutral else left
        absorbing = str(neutral != "True")
        return absorbing if absorbing in {left, right} else f"({left} {operator} {right})"


def plural_rule(language: LanguageTag) -> PluralRule:
    """The CLDR rule of a language for whole counts, as Babel's compiler writes it; none where Babel has no rules."""
    if (locale := _locale(language)) is None:
        return ()
    compiler = _WholeCountCompiler()
    return tuple(PluralBranch(PluralCategory(tag), compiler.compile(ast)) for tag, ast in locale.plural_form.abstract)


def list_files(directory: Path) -> tuple[Path, ...]:
    """The files of a directory by name; none when it does not exist."""
    return tuple(sorted(path for path in directory.iterdir() if path.is_file())) if directory.is_dir() else ()


def read_module(path: Path) -> str | None:
    """The text of a generated module, or None when it does not exist."""
    return path.read_text(encoding="utf-8") if path.is_file() else None


def write_module(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _header_text(text: str) -> str:
    """The header of a catalog as the file wrote it: its first line to the last string of its `msgstr`."""
    lines = text.splitlines()
    end = next(number for number, line in enumerate(lines) if line.lstrip().startswith("msgstr")) + 1
    while end < len(lines) and lines[end].lstrip().startswith('"'):
        end += 1
    return "\n".join(lines[:end]) + "\n\n"


def write_synced(path: Path, entries: tuple[RawEntry, ...]) -> None:
    """Writes the entries as the catalog's content, below its header as it was.

    An entry the file holds keeps its comments and flags; its text, translation and fuzzy mark are the entry's. The
    others are written new, and obsolete entries stay.
    """
    text, parsed = _parse(path, ignore_obsolete=False)
    has_header = _holds_header(parsed.entries)
    held = {message.context: message for message in parsed.entries[has_header:]}
    catalog = Catalog()
    for raw in entries:
        message = held.get(raw.context) or Message(raw.text, context=raw.context)
        message.id, message.string = raw.text, raw.translation
        message.flags = (message.flags - {FUZZY}) | ({FUZZY} if raw.fuzzy else set())
        catalog[raw.text] = message
    catalog.obsolete.update(parsed.obsolete)
    body = "".join(generate_po(catalog, omit_header=True, width=LINE_WIDTH))
    path.write_text((_header_text(text) if has_header else "") + body, encoding="utf-8")
