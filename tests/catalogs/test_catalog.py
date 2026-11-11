import pytest

from design.catalogs.catalog import Finding, Key, LanguageTag, RawEntry, read_source

FILE = "frontend/src/lib/catalogs/de.po"


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


@pytest.mark.parametrize("value", ["de", "pl", "pt-BR", "zh-Hant"])
def test_language_tag_accepts_a_language_with_optional_subtags(value):
    assert LanguageTag(value).value == value


@pytest.mark.parametrize("value", ["", "DE", "d", "deutsch", "de_DE", "de-"])
def test_language_tag_rejects_anything_else(value):
    with pytest.raises(ValueError, match="language tag"):
        LanguageTag(value)


def entry(context, text, translation="", *, fuzzy=False):
    return RawEntry(context=context, text=text, translation=translation, fuzzy=fuzzy)


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
