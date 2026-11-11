import pytest

from design.catalogs.catalog import (
    Entry,
    Finding,
    Key,
    LanguageTag,
    RawEntry,
    SourceCatalog,
    read_language,
    read_source,
    read_translation,
)

FILE = "frontend/src/lib/catalogs/de.po"
TRANSLATION_FILE = "frontend/src/lib/catalogs/pl.po"


@pytest.mark.parametrize("value", ["table.seatFree", "app.name", "login.title2"])
def test_key_accepts_a_surface_and_a_camel_case_name(value):
    assert Key(value).value == value


@pytest.mark.parametrize(
    "value",
    [
        "",
        "seatFree",
        "Table.seatFree",
        "table.SeatFree",
        "table.seat_free",
        "table.seatFree.one",
        "table.seat free",
        "table.seatFree\n",
        "tablé.seatFree",
    ],
)
def test_key_rejects_anything_but_surface_dot_camel_case(value):
    with pytest.raises(ValueError, match=r"surface\.camelCase"):
        Key(value)


@pytest.mark.parametrize("value", ["de", "pl", "pt-BR", "zh-Hant", "zh-Hant-TW", "es-419", "sl-rozaj", "de-CH-1996"])
def test_language_tag_accepts_a_language_with_optional_script_region_and_variants(value):
    assert LanguageTag(value).value == value


@pytest.mark.parametrize(
    "value",
    ["", "DE", "d", "deutsch", "de_DE", "de-", "de-de", "pt-br", "de-DEU", "de-AAAAAAAAA", "de-CH-abc", "x-private"],
)
def test_language_tag_rejects_anything_else(value):
    with pytest.raises(ValueError, match="language tag"):
        LanguageTag(value)


def entry(context, text, translation="", *, fuzzy=False, plural=False):
    return RawEntry(context=context, text=text, translation=translation, fuzzy=fuzzy, plural=plural)


def test_read_source_turns_clean_entries_into_a_catalog_in_file_order():
    catalog, findings = read_source(
        FILE, LanguageTag("de"), (entry("table.seatFree", "Frei"), entry("app.name", "Skat"))
    )

    assert findings == ()
    assert catalog.language == LanguageTag("de")
    assert [(item.key.value, item.text) for item in catalog.entries] == [
        ("table.seatFree", "Frei"),
        ("app.name", "Skat"),
    ]


@pytest.mark.parametrize(
    ("raw", "key"),
    [
        pytest.param((entry(None, "Frei"),), "Frei", id="no msgctxt"),
        pytest.param((entry("seat_free", "Frei"),), "seat_free", id="key outside surface.camelCase"),
        pytest.param((entry("table.seatFree", "Frei", fuzzy=True),), "table.seatFree", id="fuzzy"),
        pytest.param((entry("table.seatFree", "Frei", "Free"),), "table.seatFree", id="non-empty msgstr"),
        pytest.param((entry("table.seatFree", ""),), "table.seatFree", id="empty msgid"),
        pytest.param((entry("table.seatFree", "Frei", plural=True),), "table.seatFree", id="msgid_plural"),
        pytest.param(
            (entry("table.seatFree", "Frei"), entry("table.seatFree", "Platz")), "table.seatFree", id="duplicate"
        ),
    ],
)
def test_read_source_names_file_and_key_of_every_broken_entry(raw, key):
    _, findings = read_source(FILE, LanguageTag("de"), raw)

    assert [(finding.file, finding.key) for finding in findings] == [(FILE, key)]


def test_read_source_reports_every_problem_of_an_entry():
    _, findings = read_source(FILE, LanguageTag("de"), (entry("table.seatFree", "", "x", fuzzy=True),))

    assert len(findings) == 3
    assert {finding.key for finding in findings} == {"table.seatFree"}


def test_finding_reads_as_file_key_and_problem():
    assert str(Finding(file=FILE, key="table.seatFree", problem="is fuzzy")) == f"{FILE}: table.seatFree is fuzzy"


def test_read_source_refuses_a_plural_entry_saying_that_plural_forms_are_not_used():
    _, findings = read_source(FILE, LanguageTag("de"), (entry("table.seatFree", "Frei", plural=True),))

    assert [finding.problem for finding in findings] == ["uses msgid_plural; gettext plural forms are not used"]


@pytest.fixture
def source():
    return SourceCatalog(
        language=LanguageTag("de"),
        entries=(Entry(Key("table.seatFree"), "Frei"), Entry(Key("app.name"), "Skat")),
    )


def test_read_translation_turns_a_current_translation_into_a_catalog_in_the_sources_order(source):
    catalog, findings = read_translation(
        TRANSLATION_FILE,
        LanguageTag("pl"),
        (entry("app.name", "Skat", "Skat (pl)"), entry("table.seatFree", "Frei", "Wolne")),
        source,
    )

    assert findings == ()
    assert catalog.language == LanguageTag("pl")
    assert [(item.key.value, item.text) for item in catalog.entries] == [
        ("table.seatFree", "Wolne"),
        ("app.name", "Skat (pl)"),
    ]


def translated(*changes):
    """The two translated entries of `source`, with each given entry replacing the one of its key."""
    entries = {
        "table.seatFree": entry("table.seatFree", "Frei", "Wolne"),
        "app.name": entry("app.name", "Skat", "Skat"),
    }
    for change in changes:
        entries[change.context] = change
    return tuple(entries.values())


@pytest.mark.parametrize(
    ("raw", "key", "problem"),
    [
        pytest.param(
            tuple(item for item in translated() if item.context != "app.name"),
            "app.name",
            "is missing",
            id="missing key",
        ),
        pytest.param(
            (*translated(), entry("table.extra", "Extra", "Dodatek")),
            "table.extra",
            "not a key of the source",
            id="extra key",
        ),
        pytest.param(
            translated(entry("table.seatFree", "Frei", "Wolne", fuzzy=True)), "table.seatFree", "is fuzzy", id="fuzzy"
        ),
        pytest.param(
            translated(entry("table.seatFree", "Frei", "")), "table.seatFree", "empty msgstr", id="empty msgstr"
        ),
        pytest.param(
            translated(entry("table.seatFree", "Frei", "W", plural=True)),
            "table.seatFree",
            "plural forms are not used",
            id="msgid_plural",
        ),
        pytest.param(
            (*translated(), entry("table.seatFree", "Frei", "Wolne")),
            "table.seatFree",
            "is a duplicate",
            id="duplicate",
        ),
        pytest.param((*translated(), entry(None, "Schlicht", "Prosty")), "Schlicht", "has no msgctxt", id="no msgctxt"),
        pytest.param(
            (*translated(), entry("seat_free", "Frei", "Wolne")), "seat_free", "surface.camelCase", id="bad key"
        ),
    ],
)
def test_read_translation_names_file_and_key_of_every_broken_entry(source, raw, key, problem):
    _, findings = read_translation(TRANSLATION_FILE, LanguageTag("pl"), raw, source)

    assert [(finding.file, finding.key) for finding in findings] == [(TRANSLATION_FILE, key)]
    assert problem in findings[0].problem


def test_read_translation_names_the_key_the_text_it_was_made_from_and_the_sources_current_text(source):
    _, findings = read_translation(
        TRANSLATION_FILE, LanguageTag("pl"), translated(entry("table.seatFree", "Platz frei", "Wolne")), source
    )

    assert len(findings) == 1
    assert findings[0].key == "table.seatFree"
    assert "Platz frei" in findings[0].problem
    assert "Frei" in findings[0].problem


def test_read_translation_leaves_a_broken_entry_out_of_the_catalog(source):
    catalog, _ = read_translation(
        TRANSLATION_FILE, LanguageTag("pl"), translated(entry("table.seatFree", "Frei", "")), source
    )

    assert [item.key.value for item in catalog.entries] == ["app.name"]


@pytest.mark.parametrize(
    ("stem", "header", "tag", "problem"),
    [
        pytest.param("pl", "pl", "pl", None, id="header equals the file stem"),
        pytest.param("pt-BR", "pt-BR", "pt-BR", None, id="region tag"),
        pytest.param("pl", "en", "pl", "en", id="header names another language"),
        pytest.param("pl", None, "pl", "is missing", id="header missing"),
        pytest.param("pl_PL", "pl_PL", None, "language tag", id="stem is no language tag"),
    ],
)
def test_read_language_takes_the_tag_from_the_file_stem_and_requires_the_header_to_equal_it(stem, header, tag, problem):
    language, findings = read_language(TRANSLATION_FILE, stem, header)

    assert language == (LanguageTag(tag) if tag else None)
    assert [(finding.file, problem in finding.problem) for finding in findings] == (
        [(TRANSLATION_FILE, True)] if problem else []
    )
