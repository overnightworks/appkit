import pytest

from design.catalogs.catalog import (
    Entry,
    Finding,
    Gap,
    Key,
    LanguageTag,
    Marker,
    PluralCategory,
    RawCatalog,
    RawEntry,
    SourceCatalog,
    gap_names,
    pieces_of,
    read_language,
    read_source,
    read_translation,
    without_markers,
)

FILE = "frontend/src/lib/catalogs/de.po"
TRANSLATION_FILE = "frontend/src/lib/catalogs/pl.po"
GERMAN = frozenset({PluralCategory.ONE, PluralCategory.OTHER})
POLISH = frozenset({PluralCategory.ONE, PluralCategory.FEW, PluralCategory.MANY, PluralCategory.OTHER})
JAPANESE = frozenset({PluralCategory.OTHER})


@pytest.mark.parametrize(
    "value", ["table.seatFree", "app.name", "login.title2", "table.few", "table.seats.one", "table.seats.other"]
)
def test_key_accepts_a_surface_a_camel_case_name_and_an_optional_plural_category(value):
    assert Key(value).value == value


@pytest.mark.parametrize(
    ("value", "category", "family"),
    [
        pytest.param("table.seatFree", None, "table.seatFree", id="plain key"),
        pytest.param("table.few", None, "table.few", id="plain key named like a category"),
        pytest.param("table.seats.few", PluralCategory.FEW, "table.seats", id="family entry"),
    ],
)
def test_key_names_its_plural_category_and_the_key_of_its_family(value, category, family):
    assert (Key(value).category, Key(value).family) == (category, Key(family))


@pytest.mark.parametrize(
    "value",
    [
        "",
        "seatFree",
        "Table.seatFree",
        "table.SeatFree",
        "table.seat_free",
        "table.seats.some",
        "table.seats.One",
        "table.seats.one.other",
        "table.seats.",
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
        pytest.param(
            "Hi {#strong}{name} dort{/strong}!",
            ("Hi ", Marker("strong"), Gap("name"), " dort", Marker("strong", closing=True), "!"),
            id="a marked part holding a gap and words",
        ),
        pytest.param(
            "{#a}x{/a}{#a}y{/a}",
            (Marker("a"), "x", Marker("a", closing=True), Marker("a"), "y", Marker("a", closing=True)),
            id="two parts of one name",
        ),
        pytest.param("{{#strong}}", ("{#strong}",), id="doubled braces around a marker are literal"),
        pytest.param(
            "{#a}{{ }}{/a}",
            (Marker("a"), "{ }", Marker("a", closing=True)),
            id="white space with a brace is no empty part",
        ),
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


def test_pieces_of_refuses_a_gap_named_proto_and_says_why():
    with pytest.raises(ValueError, match="__proto__") as error:
        pieces_of("Hallo {__proto__}")

    assert "prototype" in str(error.value)


@pytest.mark.parametrize("text", ["Hallo {name", "Hallo name}", "Hallo {", "Hallo }", "Hallo {name!}"])
def test_pieces_of_refuses_an_unbalanced_brace(text):
    with pytest.raises(ValueError, match="unbalanced brace"):
        pieces_of(text)


@pytest.mark.parametrize(
    ("text", "sentence"),
    [
        pytest.param("Frei", "Frei", id="no marker"),
        pytest.param("{{x}} {name}", "{{x}} {name}", id="braces and gaps as written"),
        pytest.param("A {#strong}{n} takes{/strong} {{#b}}", "A {n} takes {{#b}}", id="marked part"),
    ],
)
def test_without_markers_is_the_text_with_its_markers_removed_and_everything_else_as_written(text, sentence):
    assert without_markers(text) == sentence


def entry(context, text, translation="", *, fuzzy=False, plural=False):
    return RawEntry(context=context, text=text, translation=translation, fuzzy=fuzzy, plural=plural)


def test_read_source_turns_clean_entries_into_a_catalog_in_file_order():
    catalog, findings = read_source(
        FILE, LanguageTag("de"), GERMAN, (entry("table.seatFree", "Frei"), entry("app.name", "Skat"))
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
    _, findings = read_source(FILE, LanguageTag("de"), GERMAN, raw)

    assert [(finding.file, finding.key) for finding in findings] == [(FILE, key)]


def test_read_source_reports_every_problem_of_an_entry():
    _, findings = read_source(FILE, LanguageTag("de"), GERMAN, (entry("table.seatFree", "", "x", fuzzy=True),))

    assert len(findings) == 3
    assert {finding.key for finding in findings} == {"table.seatFree"}


def test_read_source_names_the_offending_piece_of_a_malformed_gap():
    _, findings = read_source(FILE, LanguageTag("de"), GERMAN, (entry("table.seatFree", "Hallo {user.name}"),))

    assert [finding.problem for finding in findings] == ["is malformed: gap {user.name} is not a plain name"]


def test_read_source_keeps_a_text_with_gaps_and_doubled_braces_as_the_catalog_wrote_it():
    catalog, findings = read_source(FILE, LanguageTag("de"), GERMAN, (entry("table.seatFree", "{{Hallo}} {name}"),))

    assert findings == ()
    assert [item.text for item in catalog.entries] == ["{{Hallo}} {name}"]


def test_finding_reads_as_file_key_and_problem():
    assert str(Finding(file=FILE, key="table.seatFree", problem="is fuzzy")) == f"{FILE}: table.seatFree is fuzzy"


def test_read_source_refuses_a_plural_entry_saying_that_plural_forms_are_not_used():
    _, findings = read_source(FILE, LanguageTag("de"), GERMAN, (entry("table.seatFree", "Frei", plural=True),))

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
        POLISH,
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
    _, findings = read_translation(TRANSLATION_FILE, LanguageTag("pl"), POLISH, raw, source)

    assert [(finding.file, finding.key) for finding in findings] == [(TRANSLATION_FILE, key)]
    assert problem in findings[0].problem


def test_read_translation_names_the_key_the_text_it_was_made_from_and_the_sources_current_text(source):
    _, findings = read_translation(
        TRANSLATION_FILE, LanguageTag("pl"), POLISH, translated(entry("table.seatFree", "Platz frei", "Wolne")), source
    )

    assert len(findings) == 1
    assert findings[0].key == "table.seatFree"
    assert "Platz frei" in findings[0].problem
    assert "Frei" in findings[0].problem


def test_read_translation_leaves_a_broken_entry_out_of_the_catalog(source):
    catalog, _ = read_translation(
        TRANSLATION_FILE, LanguageTag("pl"), POLISH, translated(entry("table.seatFree", "Frei", "")), source
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
        TRANSLATION_FILE, LanguageTag("pl"), POLISH, greeting("{count} wiadomosci dla {name}"), gap_source
    )

    assert findings == ()
    assert [item.text for item in catalog.entries] == ["{count} wiadomosci dla {name}"]


@pytest.mark.parametrize(
    ("translation", "translated_gaps"),
    [
        pytest.param("Czesc {name}", "{name}", id="a gap dropped"),
        pytest.param("Czesc {name} {count} {other}", "{count, name, other}", id="a gap added"),
        pytest.param("Czesc {nome} {count}", "{count, nome}", id="a gap renamed"),
        pytest.param("Czesc", "has no gaps", id="no gaps"),
    ],
)
def test_read_translation_names_the_key_and_both_gap_sets_of_a_translation_whose_gaps_differ(
    gap_source, translation, translated_gaps
):
    catalog, findings = read_translation(TRANSLATION_FILE, LanguageTag("pl"), POLISH, greeting(translation), gap_source)

    assert [(finding.file, finding.key) for finding in findings] == [(TRANSLATION_FILE, "chat.greeting")]
    assert translated_gaps in findings[0].problem
    assert "{count, name}" in findings[0].problem
    assert catalog.entries == ()


def test_read_translation_names_the_offending_piece_of_a_malformed_gap(gap_source):
    _, findings = read_translation(
        TRANSLATION_FILE, LanguageTag("pl"), POLISH, greeting("Czesc {name:>5} {count}"), gap_source
    )

    assert [(finding.file, finding.key) for finding in findings] == [(TRANSLATION_FILE, "chat.greeting")]
    assert "{name:>5}" in findings[0].problem


def test_read_translation_names_an_empty_msgstr_alone_without_a_gap_mismatch(gap_source):
    _, findings = read_translation(TRANSLATION_FILE, LanguageTag("pl"), POLISH, greeting(""), gap_source)

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


def test_read_translation_says_so_when_the_source_has_no_gaps(source):
    _, findings = read_translation(
        TRANSLATION_FILE, LanguageTag("pl"), POLISH, translated(entry("table.seatFree", "Frei", "Wolne {name}")), source
    )

    assert [finding.problem for finding in findings] == ["has the gaps {name}; the source has no gaps"]


def family(key, **texts):
    """The entries of one plural family as the source catalog writes them, by category."""
    return tuple(entry(f"{key}.{category}", text) for category, text in texts.items())


SEATS = {"one": "{count} Platz", "other": "{count} Plätze"}


@pytest.mark.parametrize(
    ("categories", "texts"),
    [
        pytest.param(GERMAN, SEATS, id="one and other"),
        pytest.param(POLISH, {"one": "a", "few": "b", "many": "c", "other": "d"}, id="four categories"),
        pytest.param(JAPANESE, {"other": "a"}, id="other only"),
    ],
)
def test_read_source_takes_a_family_holding_exactly_the_categories_of_its_language(categories, texts):
    catalog, findings = read_source(FILE, LanguageTag("de"), categories, family("table.seats", **texts))

    assert findings == ()
    assert [item.key.category for item in catalog.entries] == [PluralCategory(name) for name in texts]


@pytest.mark.parametrize(
    ("categories", "texts", "key", "problem"),
    [
        pytest.param(POLISH, {"one": "a", "few": "b", "other": "d"}, "table.seats.many", "is missing", id="missing"),
        pytest.param(GERMAN, {"one": "a"}, "table.seats.other", "is missing", id="missing other"),
        pytest.param(
            GERMAN, {"one": "a", "few": "b", "other": "d"}, "table.seats.few", "is not a plural category", id="extra"
        ),
    ],
)
def test_read_source_names_the_key_and_the_category_a_family_lacks_or_has_too_many_of(categories, texts, key, problem):
    _, findings = read_source(FILE, LanguageTag("de"), categories, family("table.seats", **texts))

    assert [(finding.file, finding.key) for finding in findings] == [(FILE, key)]
    assert problem in findings[0].problem


def test_read_source_names_the_language_and_the_categories_it_needs_in_the_finding_of_a_missing_category():
    _, findings = read_source(FILE, LanguageTag("de"), POLISH, family("table.seats", one="a", few="b", other="d"))

    assert "de" in findings[0].problem
    assert "many" in findings[0].problem


def test_read_source_refuses_a_plain_key_equal_to_the_key_of_a_family():
    _, findings = read_source(
        FILE, LanguageTag("de"), GERMAN, (entry("table.seats", "Plätze"), *family("table.seats", **SEATS))
    )

    assert [(finding.file, finding.key) for finding in findings] == [(FILE, "table.seats")]
    assert "plural family" in findings[0].problem


def test_read_source_refuses_a_family_whose_entries_carry_different_gaps_and_names_each_gap_set():
    _, findings = read_source(
        FILE, LanguageTag("de"), GERMAN, family("table.seats", one="{name}: ein Platz", other="{count} Plätze")
    )

    assert [(finding.file, finding.key) for finding in findings] == [(FILE, "table.seats")]
    assert "one has the gaps {name}" in findings[0].problem
    assert "other has the gaps {count}" in findings[0].problem


@pytest.mark.parametrize(
    "texts",
    [
        pytest.param({"one": "Ein Platz frei", "other": "{count} Plätze frei"}, id="one leaves out the count"),
        pytest.param({"one": "{name}: ein Platz", "other": "{name}: {count} Plätze"}, id="a further gap in both"),
        pytest.param({"one": "{count} Platz", "other": "Plätze"}, id="other leaves out the count"),
    ],
)
def test_read_source_takes_a_family_whose_entries_differ_only_in_leaving_out_the_count(texts):
    _, findings = read_source(FILE, LanguageTag("de"), GERMAN, family("table.seats", **texts))

    assert findings == ()


def test_read_source_names_the_plural_categories_for_a_three_part_key_whose_last_part_is_none():
    _, findings = read_source(FILE, LanguageTag("de"), GERMAN, (entry("table.seats.ones", "Platz"),))

    assert [(finding.file, finding.key) for finding in findings] == [(FILE, "table.seats.ones")]
    assert "'ones'" in findings[0].problem
    assert "zero, one, two, few, many, other" in findings[0].problem


@pytest.mark.parametrize("context", ["seats", "table.seats.one.other", "Table.seats.ones"])
def test_read_source_gives_no_category_hint_for_a_key_that_is_no_surface_name_category(context):
    _, findings = read_source(FILE, LanguageTag("de"), GERMAN, (entry(context, "Platz"),))

    assert "categories" not in findings[0].problem


def test_read_source_reports_the_same_family_once_however_many_entries_it_has():
    _, findings = read_source(
        FILE,
        LanguageTag("de"),
        POLISH,
        family("table.seats", one="{name}", few="{count}", many="{count}", other="{count}"),
    )

    assert len(findings) == 1


@pytest.fixture
def family_source():
    return SourceCatalog(
        language=LanguageTag("de"),
        entries=(
            Entry(Key("table.seats.one"), "{count} Platz"),
            Entry(Key("table.seats.other"), "{count} Plätze"),
            Entry(Key("app.name"), "Skat"),
        ),
    )


def seats_translation(**texts):
    """The Polish entries of the seats family, each with the source text it was translated from (the source's
    `one` for `one`, its `other` for every other category) and the translation `texts`, plus the plain entry."""
    return (
        *(
            entry(f"table.seats.{category}", "{count} Platz" if category == "one" else "{count} Plätze", text)
            for category, text in texts.items()
        ),
        entry("app.name", "Skat", "Skat"),
    )


POLISH_SEATS = {
    "one": "{count} miejsce",
    "few": "{count} miejsca",
    "many": "{count} miejsc",
    "other": "{count} miejsca",
}


def test_read_translation_takes_a_family_with_the_categories_of_its_own_language_in_the_sources_order(family_source):
    catalog, findings = read_translation(
        TRANSLATION_FILE, LanguageTag("pl"), POLISH, seats_translation(**POLISH_SEATS), family_source
    )

    assert findings == ()
    assert [item.key.value for item in catalog.entries] == [
        "table.seats.one",
        "table.seats.few",
        "table.seats.many",
        "table.seats.other",
        "app.name",
    ]


def test_read_translation_names_the_key_and_the_text_of_the_source_for_a_missing_category(family_source):
    texts = {category: text for category, text in POLISH_SEATS.items() if category != "many"}

    _, findings = read_translation(
        TRANSLATION_FILE, LanguageTag("pl"), POLISH, seats_translation(**texts), family_source
    )

    assert [(finding.file, finding.key) for finding in findings] == [(TRANSLATION_FILE, "table.seats.many")]
    assert "is missing" in findings[0].problem
    assert "{count} Plätze" in findings[0].problem


def test_read_translation_refuses_a_category_its_language_does_not_need(family_source):
    _, findings = read_translation(
        TRANSLATION_FILE, LanguageTag("en"), GERMAN, seats_translation(**POLISH_SEATS), family_source
    )

    assert [finding.key for finding in findings] == ["table.seats.few", "table.seats.many"]
    assert all("is not a plural category" in finding.problem for finding in findings)


def test_read_translation_reports_every_category_of_a_family_the_translation_lacks_altogether(family_source):
    _, findings = read_translation(
        TRANSLATION_FILE, LanguageTag("pl"), POLISH, (entry("app.name", "Skat", "Skat"),), family_source
    )

    assert [finding.key for finding in findings] == [f"table.seats.{name}" for name in ("one", "few", "many", "other")]


@pytest.mark.parametrize(
    ("category", "text"),
    [
        pytest.param("few", "{count} Platz", id="category the source lacks, translated from its one"),
        pytest.param("few", "Alt", id="category the source lacks"),
        pytest.param("one", "Alt", id="category the source has"),
    ],
)
def test_read_translation_compares_the_msgid_with_the_source_text_of_the_same_category_or_its_other(
    family_source, category, text
):
    raw = tuple(
        entry(item.context, text, item.translation) if item.context == f"table.seats.{category}" else item
        for item in seats_translation(**POLISH_SEATS)
    )

    _, findings = read_translation(TRANSLATION_FILE, LanguageTag("pl"), POLISH, raw, family_source)

    assert [finding.key for finding in findings] == [f"table.seats.{category}"]
    assert "was translated from" in findings[0].problem


def test_read_translation_compares_the_gaps_with_the_source_text_of_the_same_category(family_source):
    texts = {**POLISH_SEATS, "few": "{count} miejsca {extra}"}

    _, findings = read_translation(
        TRANSLATION_FILE, LanguageTag("pl"), POLISH, seats_translation(**texts), family_source
    )

    assert [finding.key for finding in findings] == ["table.seats.few"]
    assert "has the gaps {count, extra}; the source has the gaps {count}" in findings[0].problem


@pytest.mark.parametrize(
    "key",
    [
        pytest.param("table.seats", id="plain key where the source has a family"),
        pytest.param("table.chairs.one", id="family the source lacks"),
    ],
)
def test_read_translation_refuses_a_key_whose_family_or_plain_key_the_source_lacks(family_source, key):
    raw = (*seats_translation(**POLISH_SEATS), entry(key, "{count} Platz", "x"))

    _, findings = read_translation(TRANSLATION_FILE, LanguageTag("pl"), POLISH, raw, family_source)

    assert [(finding.key, finding.problem) for finding in findings] == [(key, "is not a key of the source")]


def test_read_translation_names_the_missing_plain_key_beside_a_family(family_source):
    _, findings = read_translation(
        TRANSLATION_FILE, LanguageTag("pl"), POLISH, seats_translation(**POLISH_SEATS)[:-1], family_source
    )

    assert [finding.key for finding in findings] == ["app.name"]


@pytest.mark.parametrize(
    ("category", "translation"),
    [
        pytest.param("one", "Jedno miejsce", id="a category leaves out the count"),
        pytest.param("few", "{count} miejsca", id="a category keeps it"),
    ],
)
def test_read_translation_takes_a_family_entry_that_leaves_out_the_count_or_keeps_it(
    family_source, category, translation
):
    texts = {**POLISH_SEATS, category: translation}

    _, findings = read_translation(
        TRANSLATION_FILE, LanguageTag("pl"), POLISH, seats_translation(**texts), family_source
    )

    assert findings == ()


def test_read_translation_takes_a_family_entry_with_the_count_where_the_source_text_has_none():
    source = SourceCatalog(
        language=LanguageTag("de"),
        entries=(Entry(Key("table.seats.one"), "Ein Platz"), Entry(Key("table.seats.other"), "{count} Plätze")),
    )
    raw = (
        entry("table.seats.one", "Ein Platz", "{count} Platz"),
        entry("table.seats.other", "{count} Plätze", "Plätze"),
    )

    _, findings = read_translation(TRANSLATION_FILE, LanguageTag("en"), GERMAN, raw, source)

    assert findings == ()


@pytest.mark.parametrize(
    ("contexts", "holds"),
    [
        pytest.param(("table.seats.one", "app.name"), True, id="a family entry"),
        pytest.param(("table.seats.ones", "table.seats", "app.name", None), False, id="no family entry"),
        pytest.param((), False, id="no entry"),
    ],
)
def test_a_catalog_says_whether_it_holds_a_plural_family(contexts, holds):
    raw = RawCatalog(None, tuple(entry(context, "x") for context in contexts))
    source = SourceCatalog(
        LanguageTag("de"), tuple(Entry(Key(context), "x") for context in contexts if context and "ones" not in context)
    )

    assert (raw.holds_family, source.holds_family) == (holds, holds)


MARKER_REFUSALS = [
    pytest.param("Alles {/strong}", "{/strong}", id="a close without an open"),
    pytest.param("Alles {#strong}hier", "{#strong}", id="a part left open"),
    pytest.param("{#a}x {#b}y{/b}{/a}", "{#b}", id="a part inside a part"),
    pytest.param("{#a}x {#a}y{/a}{/a}", "{#a}", id="a part of one name inside itself"),
    pytest.param("{#a}x {#b}y{/a}{/b}", "{#b}", id="crossing parts"),
    pytest.param("{#a}x{/b}", "{/b}", id="a close of another name"),
    pytest.param("Alles {#strong}{/strong}", "{#strong}", id="an empty part"),
    pytest.param("Alles {#strong} \t{/strong}", "{#strong}", id="a part of white space"),
    pytest.param("Alles {#strong/}", "{#strong/}", id="a standalone marker"),
    pytest.param("Alles {#strong class=x}y{/strong}", "{#strong class=x}", id="an option"),
    pytest.param("Alles {#strong:x}y{/strong}", "{#strong:x}", id="a format spec"),
    pytest.param("Alles {#strong}y{/strong foo}", "{/strong foo}", id="an attribute on the close"),
    pytest.param("Alles {#my-name}y{/my-name}", "{#my-name}", id="a name that is no identifier"),
    pytest.param("Alles {#}y{/}", "{#}", id="no name"),
    pytest.param("Alles {# strong}y{/strong}", "{# strong}", id="a padded name"),
]


@pytest.mark.parametrize(("text", "named"), MARKER_REFUSALS)
def test_read_source_refuses_a_malformed_marker_with_one_finding_naming_the_key_and_the_marker(text, named):
    _, findings = read_source(FILE, LanguageTag("de"), GERMAN, (entry("table.seatFree", text),))

    assert [(finding.file, finding.key) for finding in findings] == [(FILE, "table.seatFree")]
    assert findings[0].problem.startswith("is malformed")
    assert named in findings[0].problem


@pytest.mark.parametrize(("text", "named"), MARKER_REFUSALS)
def test_read_translation_refuses_a_malformed_marker_with_one_finding_naming_the_key(text, named):
    source = SourceCatalog(LanguageTag("de"), (Entry(Key("table.seatFree"), "Frei {#strong}hier{/strong}"),))

    _, findings = read_translation(
        TRANSLATION_FILE,
        LanguageTag("pl"),
        POLISH,
        (entry("table.seatFree", "Frei {#strong}hier{/strong}", text),),
        source,
    )

    assert [(finding.file, finding.key) for finding in findings] == [(TRANSLATION_FILE, "table.seatFree")]
    assert named in findings[0].problem


def test_read_source_takes_a_marked_part_with_gaps_and_leaves_the_text_as_the_catalog_wrote_it():
    text = "Archive {#strong}{count} takes{/strong} and delete {#strong}{deleted}{/strong}. {#code}x{/code}"

    catalog, findings = read_source(FILE, LanguageTag("de"), GERMAN, (entry("retention.confirm", text),))

    assert findings == ()
    assert [item.text for item in catalog.entries] == [text]


@pytest.fixture
def marked_source():
    return SourceCatalog(
        language=LanguageTag("de"),
        entries=(Entry(Key("home.powered"), "{#strong}A{/strong} und {#strong}B{/strong} mit {#code}{name}{/code}"),),
    )


def powered(translation):
    return (entry("home.powered", "{#strong}A{/strong} und {#strong}B{/strong} mit {#code}{name}{/code}", translation),)


@pytest.mark.parametrize(
    "translation",
    [
        pytest.param("{#code}{name}{/code} z {#strong}B{/strong} i {#strong}A{/strong}", id="moved parts"),
        pytest.param(
            "{#strong}Aa Bb{/strong} {#strong}x{/strong} {#code}Ein Wort{/code} {name}", id="gap out of its part"
        ),
        pytest.param("{#strong}Neu {name}{/strong} {#strong}X{/strong} {#code}y{/code}", id="gap into another part"),
    ],
)
def test_read_translation_takes_markers_moved_and_gaps_moved_into_or_out_of_a_part(marked_source, translation):
    _, findings = read_translation(TRANSLATION_FILE, LanguageTag("pl"), POLISH, powered(translation), marked_source)

    assert findings == ()


@pytest.mark.parametrize(
    ("translation", "markers"),
    [
        pytest.param("{#strong}A{/strong} {#code}{name}{/code}", "the markers {#code, #strong}", id="a marker dropped"),
        pytest.param(
            "{#strong}A B{/strong} {#code}{name}{/code}", "the markers {#code, #strong}", id="a marker merged"
        ),
        pytest.param(
            "{#strong}A{/strong} {#strong}B{/strong} {#em}{name}{/em}",
            "the markers {#em, #strong, #strong}",
            id="a marker renamed",
        ),
        pytest.param(
            "{#strong}A{/strong} {#strong}B{/strong} {#strong}{name}{/strong}",
            "the markers {#strong, #strong, #strong}",
            id="a marker added",
        ),
        pytest.param("A B {name}", "no markers", id="no markers"),
    ],
)
def test_read_translation_names_the_key_and_both_marker_multisets_of_a_translation_whose_markers_differ(
    marked_source, translation, markers
):
    catalog, findings = read_translation(
        TRANSLATION_FILE, LanguageTag("pl"), POLISH, powered(translation), marked_source
    )

    assert [(finding.file, finding.key) for finding in findings] == [(TRANSLATION_FILE, "home.powered")]
    assert markers in findings[0].problem
    assert "the source has the markers {#code, #strong, #strong}" in findings[0].problem
    assert catalog.entries == ()


def test_read_translation_names_a_marker_the_source_lacks():
    source = SourceCatalog(LanguageTag("de"), (Entry(Key("table.seatFree"), "Frei"),))

    _, findings = read_translation(
        TRANSLATION_FILE,
        LanguageTag("pl"),
        POLISH,
        (entry("table.seatFree", "Frei", "{#strong}Wolne{/strong}"),),
        source,
    )

    assert [finding.key for finding in findings] == ["table.seatFree"]
    assert "the source has no markers" in findings[0].problem


MARKED_SEATS = {"one": "{#strong}{count}{/strong} Platz", "other": "{#strong}{count}{/strong} Plätze"}


def test_read_source_refuses_a_family_whose_entries_carry_different_markers_and_names_each_set():
    _, findings = read_source(
        FILE,
        LanguageTag("de"),
        GERMAN,
        family("table.seats", one="{#strong}{count}{/strong} Platz", other="{count} Plätze"),
    )

    assert [(finding.file, finding.key) for finding in findings] == [(FILE, "table.seats")]
    assert "one has the markers {#strong}" in findings[0].problem
    assert "other has no markers" in findings[0].problem


def test_read_source_takes_a_family_whose_entries_carry_the_same_markers():
    _, findings = read_source(FILE, LanguageTag("de"), GERMAN, family("table.seats", **MARKED_SEATS))

    assert findings == ()


def test_read_translation_compares_the_markers_with_the_source_text_of_the_same_category_or_its_other():
    source = SourceCatalog(
        LanguageTag("de"), tuple(Entry(Key(f"table.seats.{category}"), text) for category, text in MARKED_SEATS.items())
    )
    translated = {
        category: ("{#strong}{count}{/strong} Platz" if category == "one" else "{#strong}{count}{/strong} Plätze")
        for category in ("one", "few", "many", "other")
    }
    texts = {
        **{category: f"{{#strong}}{{count}}{{/strong}} {category}" for category in translated},
        "few": "{count} few",
    }

    _, findings = read_translation(
        TRANSLATION_FILE,
        LanguageTag("pl"),
        POLISH,
        tuple(entry(f"table.seats.{category}", translated[category], text) for category, text in texts.items()),
        source,
    )

    assert [finding.key for finding in findings] == ["table.seats.few"]
    assert "no markers; the source has the markers {#strong}" in findings[0].problem
