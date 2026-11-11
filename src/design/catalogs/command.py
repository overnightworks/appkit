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
        from design.catalogs.po_file import read_entries
    except ModuleNotFoundError:
        return fail(MISSING_EXTRA)

    catalog_path = CATALOGS / f"{SOURCE_LANGUAGE}.po"
    module_path = MODULES / f"{SOURCE_LANGUAGE}.ts"
    if not catalog_path.is_file():
        return fail(f"{catalog_path}: the source catalog is missing")
    catalog, findings = read_source(str(catalog_path), LanguageTag(SOURCE_LANGUAGE), read_entries(catalog_path))
    if findings:
        return fail(*findings)

    module = render(catalog)
    if not options.check:
        module_path.parent.mkdir(parents=True, exist_ok=True)
        module_path.write_text(module, encoding="utf-8")
        return 0
    if not module_path.is_file():
        return fail(f"{module_path}: the module is missing; run design-catalogs")
    if module_path.read_text(encoding="utf-8") != module:
        return fail(f"{module_path}: the module differs from its catalog; run design-catalogs")
    return 0
