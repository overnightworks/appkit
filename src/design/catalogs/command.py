# ruff: noqa: T201 - the command is the one place that prints the findings
"""design-catalogs: write the typed module of the source catalog, or check that it is current."""

import argparse
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from design.catalogs.catalog import LanguageTag, read_source
from design.catalogs.typescript import render

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


def main(arguments: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="design-catalogs", description=__doc__)
    parser.add_argument("--check", action="store_true", help="write nothing; fail on a finding or a stale module")
    options = parser.parse_args(arguments)
    try:
        from design.catalogs.po_file import CatalogFileError, read_entries, read_module, write_module
    except ModuleNotFoundError as error:  # pragma: no cover - run in a subprocess without Babel (tests/test_wheel.py)
        if not (error.name or "").startswith("babel"):
            raise
        return fail(MISSING_EXTRA)

    catalog_path = CATALOGS / f"{SOURCE_LANGUAGE}.po"
    module_path = MODULES / f"{SOURCE_LANGUAGE}.ts"
    try:
        entries = read_entries(catalog_path)
    except CatalogFileError as error:
        return fail(error)
    catalog, findings = read_source(str(catalog_path), LanguageTag(SOURCE_LANGUAGE), entries)
    if findings:
        return fail(*findings)

    module = render(catalog)
    if not options.check:
        write_module(module_path, module)
        return 0
    current = read_module(module_path)
    if current is None:
        return fail(f"{module_path}: the module is missing; run design-catalogs")
    if current != module:
        return fail(f"{module_path}: the module differs from its catalog; run design-catalogs")
    return 0
