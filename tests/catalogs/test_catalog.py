import pytest

from design.catalogs.catalog import (
    Entry,
    Finding,
    Gap,
    Key,
    LanguageTag,
    RawEntry,
    SourceCatalog,
    gap_names,
    pieces_of,
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


@pytest.mark.parametrize(
    ("text", "pieces"),
    [
        pytest.param("", (), id="empty"),
        pytest.param("Frei", ("Frei",), id="no gap"),
        pytest.param("{name}", (Gap("name"),), id="only a gap"),
        pytest.param("Hallo {name}!", ("Hallo ", Gap("name"), "!"), id="gap between literals"),
        pytest.param("{a}{b}", (Gap("a"), Gap("b")), id="adjacent gaps"),
        pytest.param("{name} und {name}", (Gap("name"), " und ", Gap("name")), id="a gap used twice"),
        pytest.param("Use {{braces}}", ("Use {braces}",), id="doubled braces are literal braces"),
        pytest.param("{{{name}}}", ("{", Gap("name"), "}"), id="doubled braces around a gap"),
    ],
)
def test_pieces_of_splits_a_text_into_literals_and_gaps(text, pieces):
    assert pieces_of(text) == pieces


def test_gap_names_are_the_set_of_names_in_a_text():
    assert gap_names(pieces_of("{b} {a} {b}")) == frozenset({"a", "b"})


@pytest.mark.parametrize(
    ("text", "piece"),
    [
        pytest.param("Hallo {name:>5}", "{name:>5}", id="format spec"),
        pytest.param("Hallo {name:}", "{name:}", id="empty format spec"),
        pytest.param("Hallo {name!r}", "{name!r}", id="conversion"),
        pytest.param("Hallo {name!r:>5}", "{name!r:>5}", id="conversion and format spec"),
        pytest.param("Hallo {0}", "{0}", id="positional"),
        pytest.param("Hallo {}", "{}", id="auto-numbered"),
        pytest.param("Hallo {user.name}", "{user.name}", id="attribute"),
        pytest.param("Hallo {names[0]}", "{names[0]}", id="item"),
        pytest.param("Hallo { name }", "{ name }", id="padded name"),
    ],
)
def test_pieces_of_refuses_a_gap_that_is_not_a_plain_name_and_names_it(text, piece):
    with pytest.raises(ValueError, match="not a plain name") as error:
        pieces_of(text)

    assert piece in str(error.value)


@pytest.mark.parametrize("text", ["Hallo {name", "Hallo name}", "Hallo {", "Hallo }", "Hallo {name!}"])
def test_pieces_of_refuses_an_unbalanced_brace(text):
    with pytest.raises(ValueError, match="unbalanced brace"):
        pieces_of(text)


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
        pytest.param((entry("table.seatFree", "Hallo {name:>5}"),), "table.seatFree", id="gap with a format spec"),
        pytest.param((entry("table.seatFree", "Hallo {name"),), "table.seatFree", id="unclosed brace"),
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


def test_read_source_names_the_offending_piece_of_a_malformed_gap():
    _, findings = read_source(FILE, LanguageTag("de"), (entry("table.seatFree", "Hallo {user.name}"),))

    assert [finding.problem for finding in findings] == ["is malformed: gap {user.name} is not a plain name"]


def test_read_source_keeps_a_text_with_gaps_and_doubled_braces_as_the_catalog_wrote_it():
    catalog, findings = read_source(FILE, LanguageTag("de"), (entry("table.seatFree", "{{Hallo}} {name}"),))

    assert findings == ()
    assert [item.text for item in catalog.entries] == ["{{Hallo}} {name}"]


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
            translated(entry("table.seatFree", "Frei", " \t ")),
            "table.seatFree",
            "empty msgstr",
            id="whitespace-only msgstr",
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


@pytest.fixture
def gap_source():
    return SourceCatalog(
        language=LanguageTag("de"),
        entries=(Entry(Key("chat.greeting"), "Hallo {name}, du hast {count} Nachrichten"),),
    )


def greeting(translation):
    return (entry("chat.greeting", "Hallo {name}, du hast {count} Nachrichten", translation),)


def test_read_translation_accepts_a_translation_with_the_same_gaps_in_another_order(gap_source):
    catalog, findings = read_translation(
        TRANSLATION_FILE, LanguageTag("pl"), greeting("{count} wiadomosci dla {name}"), gap_source
    )

    assert findings == ()
    assert [item.text for item in catalog.entries] == ["{count} wiadomosci dla {name}"]


@pytest.mark.parametrize(
    ("translation", "translated_gaps"),
    [
        pytest.param("Czesc {name}", "{name}", id="a gap dropped"),
        pytest.param("Czesc {name} {count} {other}", "{count, name, other}", id="a gap added"),
        pytest.param("Czesc {nome} {count}", "{count, nome}", id="a gap renamed"),
        pytest.param("Czesc", "none", id="no gaps"),
    ],
)
def test_read_translation_names_the_key_and_both_gap_sets_of_a_translation_whose_gaps_differ(
    gap_source, translation, translated_gaps
):
    catalog, findings = read_translation(TRANSLATION_FILE, LanguageTag("pl"), greeting(translation), gap_source)

    assert [(finding.file, finding.key) for finding in findings] == [(TRANSLATION_FILE, "chat.greeting")]
    assert translated_gaps in findings[0].problem
    assert "{count, name}" in findings[0].problem
    assert catalog.entries == ()


def test_read_translation_names_the_offending_piece_of_a_malformed_gap(gap_source):
    _, findings = read_translation(TRANSLATION_FILE, LanguageTag("pl"), greeting("Czesc {name:>5} {count}"), gap_source)

    assert [(finding.file, finding.key) for finding in findings] == [(TRANSLATION_FILE, "chat.greeting")]
    assert "{name:>5}" in findings[0].problem


def test_read_translation_names_an_empty_msgstr_alone_without_a_gap_mismatch(gap_source):
    _, findings = read_translation(TRANSLATION_FILE, LanguageTag("pl"), greeting(""), gap_source)

    assert [finding.problem for finding in findings] == ["has an empty msgstr"]


@pytest.mark.parametrize(
    ("stem", "header", "tag", "problem"),
    [
        pytest.param("pl", "pl", "pl", None, id="header equals the file stem"),
        pytest.param("pt-BR", "pt-BR", "pt-BR", None, id="region tag"),
        pytest.param("pl", "en", "pl", "en", id="header names another language"),
        pytest.param("pl", None, "pl", "is missing", id="header missing"),
        pytest.param("pt-BR", "pt_BR", "pt-BR", "pt_BR", id="header in the POSIX form"),
        pytest.param("pl_PL", "pl_PL", None, "language tag", id="stem is no language tag"),
    ],
)
def test_read_language_takes_the_tag_from_the_file_stem_and_requires_the_header_to_equal_it(stem, header, tag, problem):
    language, findings = read_language(TRANSLATION_FILE, stem, header)

    assert language == (LanguageTag(tag) if tag else None)
    assert [(finding.file, problem in finding.problem) for finding in findings] == (
        [(TRANSLATION_FILE, True)] if problem else []
    )
