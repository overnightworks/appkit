# ruff: noqa: T201 - the command is the one place that prints the findings
"""design-catalogs: write the typed module of the source catalog, or check that it is current."""

import argparse
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from design.catalogs.catalog import LanguageTag, SourceCatalog, read_language, read_source, read_translation
from design.catalogs.typescript import render, render_translation

if TYPE_CHECKING:
    from collections.abc import Sequence

SOURCE_LANGUAGE = "de"
CATALOGS = Path("frontend/src/lib/catalogs")
MODULES = Path("frontend/src/lib/words")
MISSING_EXTRA = "design-catalogs needs Babel: install overnightworks-design[catalogs]."


def fail(*messages: object) -> int:
    for message in messages:
        print(message, file=sys.stderr)
    return 1


def translation_modules(paths: tuple[Path, ...], source: SourceCatalog) -> tuple[dict[Path, str], list[object]]:
    """The module text of every translation catalog by module path, and every problem of the catalogs."""
    from design.catalogs.po_file import CatalogFileError, read_catalog

    modules: dict[Path, str] = {}
    problems: list[object] = []
    for path in paths:
        try:
            raw = read_catalog(path)
        except CatalogFileError as error:
            problems.append(error)
            continue
        language, language_findings = read_language(str(path), path.stem, raw.language)
        problems.extend(language_findings)
        if language is None:
            continue
        catalog, findings = read_translation(str(path), language, raw.entries, source)
        problems.extend(findings)
        modules[MODULES / f"{language.value}.ts"] = render_translation(catalog, source.language)
    return modules, problems


def stale_modules(modules: dict[Path, str]) -> list[str]:
    """A line for every module that is missing or differs from its catalog and every file no catalog produces."""
    from design.catalogs.po_file import list_files, read_module

    stale = [
        f"{path}: the module {'is missing' if current is None else 'differs from its catalog'}; run design-catalogs"
        for path, module in modules.items()
        if (current := read_module(path)) != module
    ]
    strays = [
        f"{path}: no catalog produces this file; delete it" for path in list_files(MODULES) if path not in modules
    ]
    return [*stale, *strays]


def main(arguments: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="design-catalogs", description=__doc__)
    parser.add_argument("--check", action="store_true", help="write nothing; fail on a finding or a stale module")
    options = parser.parse_args(arguments)
    try:
        from design.catalogs.po_file import CatalogFileError, list_files, read_catalog, write_module
    except ModuleNotFoundError as error:  # pragma: no cover - run in a subprocess without Babel (tests/test_wheel.py)
        if not (error.name or "").startswith("babel"):
            raise
        return fail(MISSING_EXTRA)

    source_path = CATALOGS / f"{SOURCE_LANGUAGE}.po"
    try:
        raw = read_catalog(source_path)
    except CatalogFileError as error:
        return fail(error)
    _, header_findings = read_language(str(source_path), SOURCE_LANGUAGE, raw.language)
    source, findings = read_source(str(source_path), LanguageTag(SOURCE_LANGUAGE), raw.entries)
    if header_findings or findings:
        return fail(*header_findings, *findings)

    translation_paths = tuple(path for path in list_files(CATALOGS) if path.suffix == ".po" and path != source_path)
    modules, problems = translation_modules(translation_paths, source)
    if problems:
        return fail(*problems)
    modules[MODULES / f"{SOURCE_LANGUAGE}.ts"] = render(source)

    if not options.check:
        for path, module in modules.items():
            write_module(path, module)
        return 0
    problems = stale_modules(modules)
    return fail(*problems) if problems else 0
