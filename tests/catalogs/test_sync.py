import pytest

from design.catalogs.catalog import (
    Entry,
    Finding,
    Key,
    LanguageTag,
    PluralCategory,
    RawEntry,
    SourceCatalog,
)
from design.catalogs.sync import structural_findings, sync_translation

GERMAN = frozenset({PluralCategory.ONE, PluralCategory.OTHER})
POLISH = frozenset({PluralCategory.ONE, PluralCategory.FEW, PluralCategory.MANY, PluralCategory.OTHER})
JAPANESE = frozenset({PluralCategory.OTHER})


def source_of(**texts):
    return SourceCatalog(
        LanguageTag("de"), tuple(Entry(Key(key.replace("_", ".")), text) for key, text in texts.items())
    )


def entry(context, text, translation="", *, fuzzy=False, plural=False):
    return RawEntry(context, text, translation, fuzzy, plural)


@pytest.fixture
def seats():
    """The source with the family `table.seats` in the categories of German, and a plain key after it."""
    return source_of(table_seats_one="{count} Platz", table_seats_other="{count} Plätze", app_name="Skat")


def test_sync_leaves_a_catalog_that_follows_its_source_as_it_is():
    source = source_of(table_seatFree="Frei", app_name="Skat")
    translation = (
        entry("table.seatFree", "Frei", "Wolne"),
        entry("app.name", "Skat", "", fuzzy=True),
    )

    assert sync_translation(source, frozenset(), translation) == translation


def test_sync_adds_a_missing_key_with_the_source_text_as_msgid_and_an_empty_msgstr():
    source = source_of(table_seatFree="Frei", app_name="Skat")

    assert sync_translation(source, frozenset(), (entry("table.seatFree", "Frei", "Wolne"),)) == (
        entry("table.seatFree", "Frei", "Wolne"),
        entry("app.name", "Skat"),
    )


@pytest.mark.parametrize("translation", ["Wolne", ""], ids=["translated", "empty"])
def test_sync_sets_the_new_source_text_as_msgid_keeps_the_msgstr_and_marks_the_entry_fuzzy(translation):
    source = source_of(table_seatFree="Frei oder besetzt")

    assert sync_translation(source, frozenset(), (entry("table.seatFree", "Frei", translation),)) == (
        entry("table.seatFree", "Frei oder besetzt", translation, fuzzy=True),
    )


def test_sync_removes_a_key_the_source_dropped():
    source = source_of(app_name="Skat")

    assert sync_translation(
        source, frozenset(), (entry("table.gone", "Weg", "Zniknęło"), entry("app.name", "Skat", "Skat"))
    ) == (entry("app.name", "Skat", "Skat"),)


@pytest.mark.parametrize(
    ("present", "expected"),
    [
        pytest.param(["b", "a", "c"], ["b", "a", "c"], id="existing order kept"),
        pytest.param(["a", "c"], ["a", "b", "c"], id="new key after its predecessor in the source"),
        pytest.param(["b", "c"], ["a", "b", "c"], id="new first key at the start"),
        pytest.param(["c", "a"], ["c", "a", "b"], id="new key after its predecessor wherever that stands"),
        pytest.param([], ["a", "b", "c"], id="all new keys in the source's order"),
    ],
)
def test_sync_keeps_the_order_of_existing_entries_and_puts_a_new_key_after_its_predecessor_in_the_source(
    present, expected
):
    source = source_of(x_a="A", x_b="B", x_c="C")

    synced = sync_translation(source, frozenset(), tuple(entry(f"x.{name}", name.upper(), "t") for name in present))

    assert [item.context for item in synced] == [f"x.{name}" for name in expected]


def test_sync_gives_a_family_exactly_the_categories_of_its_language(seats):
    translation = (
        entry("table.seats.one", "{count} Platz", "{count} miejsce"),
        entry("table.seats.other", "{count} Plätze", "{count} miejsc"),
        entry("app.name", "Skat", "Skat"),
    )

    assert sync_translation(seats, POLISH, translation) == (
        entry("table.seats.one", "{count} Platz", "{count} miejsce"),
        entry("table.seats.few", "{count} Plätze"),
        entry("table.seats.many", "{count} Plätze"),
        entry("table.seats.other", "{count} Plätze", "{count} miejsc"),
        entry("app.name", "Skat", "Skat"),
    )


def test_sync_removes_a_category_the_language_does_not_take(seats):
    translation = (
        entry("table.seats.one", "{count} Platz", "{count} Sitz"),
        entry("table.seats.few", "{count} Plätze", "{count} Sitze"),
        entry("table.seats.other", "{count} Plätze", "{count} Sitze"),
        entry("app.name", "Skat", "Skat"),
    )

    assert [item.context for item in sync_translation(seats, GERMAN, translation)] == [
        "table.seats.one",
        "table.seats.other",
        "app.name",
    ]


def test_sync_takes_the_source_other_text_for_a_category_the_source_lacks_and_follows_its_change():
    source = source_of(table_seats_one="{count} Platz", table_seats_other="{count} Sitzplätze")
    translation = (
        entry("table.seats.one", "{count} Platz", "{count} miejsce"),
        entry("table.seats.few", "{count} Plätze", "{count} miejsca"),
        entry("table.seats.many", "{count} Sitzplätze", "{count} miejsc"),
        entry("table.seats.other", "{count} Plätze", "{count} miejsca"),
    )

    assert sync_translation(source, POLISH, translation) == (
        entry("table.seats.one", "{count} Platz", "{count} miejsce"),
        entry("table.seats.few", "{count} Sitzplätze", "{count} miejsca", fuzzy=True),
        entry("table.seats.many", "{count} Sitzplätze", "{count} miejsc"),
        entry("table.seats.other", "{count} Sitzplätze", "{count} miejsca", fuzzy=True),
    )


def test_sync_swaps_the_entries_of_a_key_that_changed_from_a_family_to_a_plain_key_and_back():
    plain = source_of(table_seats="Plätze")
    family = source_of(table_seats_other="{count} Plätze")

    to_plain = sync_translation(plain, JAPANESE, (entry("table.seats.other", "{count} Plätze", "席"),))
    to_family = sync_translation(family, JAPANESE, to_plain)

    assert to_plain == (entry("table.seats", "Plätze"),)
    assert to_family == (entry("table.seats.other", "{count} Plätze"),)


@pytest.mark.parametrize(
    ("entries", "problems"),
    [
        pytest.param([entry(None, "Schlicht")], [("Schlicht", "has no msgctxt")], id="without msgctxt"),
        pytest.param(
            [entry("app.name", "Skat", "a"), entry("app.name", "Skat", "b")],
            [("app.name", "is a duplicate")],
            id="duplicate",
        ),
        pytest.param(
            [entry("app.name", "Skat", plural=True)],
            [("app.name", "uses msgid_plural; gettext plural forms are not used")],
            id="msgid_plural",
        ),
        pytest.param([entry("app.name", "Skat"), entry("table.gone", "Weg", fuzzy=True)], [], id="sound"),
    ],
)
def test_structural_findings_name_an_entry_the_sync_could_not_follow_without_losing_a_translation(entries, problems):
    assert structural_findings("pl.po", tuple(entries)) == tuple(Finding("pl.po", key, text) for key, text in problems)
