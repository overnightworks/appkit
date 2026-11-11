# ruff: noqa: T201 - the command is the one place that prints the findings
"""design-catalogs: write one typed module per language from the catalogs, or check that they are current."""

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from design.catalogs.catalog import (
    LanguageTag,
    PluralCategories,
    RawEntry,
    SourceCatalog,
    TranslationCatalog,
    read_language,
    read_source,
    read_translation,
)
from design.catalogs.declaration import Declaration, DeclarationError, read_declaration
from design.catalogs.python_module import render as render_python
from design.catalogs.sync import structural_findings, sync_translation
from design.catalogs.typescript import render, render_loader, render_translation

if TYPE_CHECKING:
    from collections.abc import Sequence

LOADER = "index.ts"
MISSING_EXTRA = "design-catalogs needs Babel: install overnightworks-design[catalogs]."


def fail(*messages: object) -> int:
    for message in messages:
        print(message, file=sys.stderr)
    return 1


def source_path(declaration: Declaration) -> Path:
    return declaration.catalogs / f"{declaration.source.value}.po"


def source_catalog(declaration: Declaration) -> tuple[SourceCatalog | None, list[object]]:
    """The source catalog of the declaration, none when its file cannot be read, and every problem of the file."""
    from design.catalogs.po_file import CatalogFileError, plural_categories, read_catalog

    path = source_path(declaration)
    try:
        raw = read_catalog(path)
        categories = plural_categories(declaration.source, path) if raw.holds_family else frozenset()
    except CatalogFileError as error:
        return None, [error]
    _, header_findings = read_language(str(path), declaration.source.value, raw.language)
    source, findings = read_source(str(path), declaration.source, categories, raw.entries)
    return source, [*header_findings, *findings]


@dataclass(frozen=True)
class TranslationFile:
    """A translation catalog file as read: its language, the plural categories that language needs and its entries."""

    path: Path
    language: LanguageTag
    categories: PluralCategories
    entries: tuple[RawEntry, ...]


def translation_files(
    paths: tuple[Path, ...], source: SourceCatalog
) -> tuple[tuple[TranslationFile, ...], list[object]]:
    """The translation catalog files, and every problem of the files themselves."""
    from design.catalogs.po_file import CatalogFileError, plural_categories, read_catalog

    files: list[TranslationFile] = []
    problems: list[object] = []
    for path in paths:
        try:
            raw = read_catalog(path)
            language, language_findings = read_language(str(path), path.stem, raw.language)
            problems.extend(language_findings)
            if language is None:
                continue
            categories = plural_categories(language, path) if source.holds_family else frozenset()
        except CatalogFileError as error:
            problems.append(error)
            continue
        files.append(TranslationFile(path, language, categories, raw.entries))
    return tuple(files), problems


def translation_catalogs(
    files: tuple[TranslationFile, ...], source: SourceCatalog
) -> tuple[tuple[TranslationCatalog, ...], list[object]]:
    """The translation of every catalog file, and every problem of the entries."""
    catalogs: list[TranslationCatalog] = []
    problems: list[object] = []
    for file in files:
        catalog, findings = read_translation(str(file.path), file.language, file.categories, file.entries, source)
        problems.extend(findings)
        catalogs.append(catalog)
    return tuple(catalogs), problems


def sync_catalogs(listed: tuple[Path, ...], files: tuple[TranslationFile, ...], source: SourceCatalog) -> int:
    """Brings every translation in line with the source and writes the catalogs that changed; none if one is refused.

    A catalog is written at the path the directory listed, never at one an object read from the file carries.
    """
    from design.catalogs.po_file import write_synced

    problems = [finding for file in files for finding in structural_findings(str(file.path), file.entries)]
    if problems:
        return fail(*problems)
    for file in files:
        synced = sync_translation(source, file.categories, file.entries)
        if synced != file.entries:
            write_synced(next(path for path in listed if path == file.path), synced)
    return 0


def render_modules(
    declaration: Declaration, source: SourceCatalog, translations: tuple[TranslationCatalog, ...]
) -> dict[Path, str]:
    """The text of every module by its path: one TypeScript module per language, their loader and the Python module
    if declared."""
    modules = {declaration.typescript / f"{source.language.value}.ts": render(source)}
    modules.update(
        (declaration.typescript / f"{catalog.language.value}.ts", render_translation(catalog, source.language))
        for catalog in translations
    )
    modules[declaration.typescript / LOADER] = render_loader(
        source.language, tuple(catalog.language for catalog in translations)
    )
    if declaration.python is not None:
        from design.catalogs.po_file import plural_rule

        modules[declaration.python] = render_python(source, translations, plural_rule)
    return modules


def stale_modules(modules: dict[Path, str], directory: Path) -> list[str]:
    """A line for every module that is missing or differs from its catalogs and every file no catalog produces."""
    from design.catalogs.po_file import list_files, read_module

    stale = [
        f"{path}: the module {'is missing' if current is None else 'differs from its catalog'}; run design-catalogs"
        for path, module in modules.items()
        if (current := read_module(path)) != module
    ]
    strays = [
        f"{path}: no catalog produces this file; delete it"
        for path in list_files(directory)
        if path not in modules and not path.name.startswith(".")
    ]
    return [*stale, *strays]


def generate(
    declaration: Declaration,
    source: SourceCatalog,
    files: tuple[TranslationFile, ...],
    problems: list[object],
    *,
    check: bool,
) -> int:
    """Writes the modules of the catalogs, or with `check` finds the modules that are not current."""
    from design.catalogs.po_file import write_module

    translations, entry_problems = translation_catalogs(files, source)
    if problems or entry_problems:
        return fail(*problems, *entry_problems)
    modules = render_modules(declaration, source, translations)
    if not check:
        for path, module in modules.items():
            write_module(path, module)
        return 0
    stale = stale_modules(modules, declaration.typescript)
    return fail(*stale) if stale else 0


def main(arguments: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="design-catalogs", description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="write nothing; fail on a finding or a stale module")
    mode.add_argument(
        "--sync",
        action="store_true",
        help="bring every translation catalog in line with the source by key and write the catalogs only;"
        " run design-catalogs after the translations are written",
    )
    options = parser.parse_args(arguments)
    try:
        from design.catalogs.po_file import list_files
    except ModuleNotFoundError as error:  # pragma: no cover - run in a subprocess without Babel (tests/test_wheel.py)
        if not (error.name or "").startswith("babel"):
            raise
        return fail(MISSING_EXTRA)

    try:
        declaration = read_declaration(Path())
    except DeclarationError as error:
        return fail(error)
    source, problems = source_catalog(declaration)
    if source is None or problems:
        return fail(*problems)

    translation_paths = tuple(
        path for path in list_files(declaration.catalogs) if path.suffix == ".po" and path != source_path(declaration)
    )
    files, problems = translation_files(translation_paths, source)
    if options.sync:
        return fail(*problems) if problems else sync_catalogs(translation_paths, files, source)
    return generate(declaration, source, files, problems, check=options.check)
