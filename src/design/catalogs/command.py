# ruff: noqa: T201 - the command is the one place that prints the findings
"""design-catalogs: write one typed module per language from the catalogs, or check that they are current."""

import argparse
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from design.catalogs.catalog import SourceCatalog, TranslationCatalog, read_language, read_source, read_translation
from design.catalogs.declaration import Declaration, DeclarationError, read_declaration
from design.catalogs.python_module import render as render_python
from design.catalogs.typescript import render, render_translation

if TYPE_CHECKING:
    from collections.abc import Sequence

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


def translation_catalogs(
    paths: tuple[Path, ...], source: SourceCatalog
) -> tuple[tuple[TranslationCatalog, ...], list[object]]:
    """The translation of every catalog file, and every problem of the files."""
    from design.catalogs.po_file import CatalogFileError, plural_categories, read_catalog

    catalogs: list[TranslationCatalog] = []
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
        catalog, findings = read_translation(str(path), language, categories, raw.entries, source)
        problems.extend(findings)
        catalogs.append(catalog)
    return tuple(catalogs), problems


def render_modules(
    declaration: Declaration, source: SourceCatalog, translations: tuple[TranslationCatalog, ...]
) -> dict[Path, str]:
    """The text of every module by its path: one TypeScript module per language and the Python module if declared."""
    modules = {declaration.typescript / f"{source.language.value}.ts": render(source)}
    modules.update(
        (declaration.typescript / f"{catalog.language.value}.ts", render_translation(catalog, source.language))
        for catalog in translations
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


def main(arguments: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="design-catalogs", description=__doc__)
    parser.add_argument("--check", action="store_true", help="write nothing; fail on a finding or a stale module")
    options = parser.parse_args(arguments)
    try:
        from design.catalogs.po_file import list_files, write_module
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
    translations, problems = translation_catalogs(translation_paths, source)
    if problems:
        return fail(*problems)
    modules = render_modules(declaration, source, translations)

    if not options.check:
        for path, module in modules.items():
            write_module(path, module)
        return 0
    problems = stale_modules(modules, declaration.typescript)
    return fail(*problems) if problems else 0
