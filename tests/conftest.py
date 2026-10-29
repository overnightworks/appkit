import re

import pytest


@pytest.fixture(scope="session")
def font_files():
    return {
        f"{family}-{subset}-{weight}-normal.woff2"
        for family, weights in (("oswald", (400, 700)), ("open-sans", (400, 600)))
        for weight in weights
        for subset in ("latin", "latin-ext")
    }


@pytest.fixture(scope="session")
def licences():
    return {"oswald-LICENSE", "open-sans-LICENSE"}


@pytest.fixture(scope="session")
def stylesheet_urls():
    """The url('...') targets a stylesheet names, in file order."""
    return lambda stylesheet: re.findall(r"url\('([^']+)'\)", stylesheet.read_text())
