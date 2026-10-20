# ui-console

This package carries design tokens and the grammar of a console page: lists
of things with states, facts and fields. It refuses components, product-specific
page layout, JavaScript and fonts; a product renders through this grammar with its own
markup.

Design tokens and the settings grammar shared by overnightworks products.
Owned by agent-presentator's blessed picture `docs/mockups/m0-lobby.html`.

Distribution is one stylesheet, published as a GitHub release asset. Tags are
never moved; a broken release gets the next patch tag.

Every pull request passes the shared quality gate (`quality / verdict`, from
`overnightworks/quality`): secret scan, workflow-security scan and SonarCloud analysis of the CSS and HTML.

Pin:

```
https://github.com/overnightworks/ui-console/releases/download/v0.3.0/ui-console.css
```

Jinja and Svelte products vendor that file (do not hot-link it at runtime) and
load it before the product stylesheet.

## What it owns

- The token names and the picture's default values: surfaces (`--canvas`,
  `--canvas-2`, `--screen`, `--shadow`), ink, lines, accent, state colours,
  type stacks, and `--radius` (2px).
- The three theme selectors the picture uses: `:root`; the dark media query
  guarded by `:root:not([data-theme="light"])`; and `:root[data-theme="dark"]`.
  No attribute follows the OS; `data-theme="light"` beats the media query;
  `data-theme="dark"` forces dark.
- The settings grammar, as class names from the picture:

  | Piece | Classes |
  |---|---|
  | Title row | `.list-head` — one `h1`, optionally one primary control. Zero actions is valid and must not look broken. |
  | Tab strip | `nav.tabs` > `a.tab` / `.tab--now` |
  | Table with STATE | `.rows` > `.row.row--head` + `.row` > `.state` |
  | State as shape plus word | `.state--ok` disc, `.state--busy` ring, `.state--fail` triangle, `.state--never` dashed square, `.state--off` split disc |
  | Label and value | `.stand` / `.lbl` (facts), `.field` / `label` (forms), `.form-part` / `.sub` (groups) |
  | Uppercase outline pill | `.tag` |
  | Right-aligned outline buttons | `.btn`, `.btn--primary`, `.btn--s`, `.row-act`, `.pair` |
  | Empty | `.empty`, `.empty-mark` |
  | Error | `.banner.banner--fail` (and `.banner--ok`, `.banner--busy`) |
  | Sign-in | `.login` > `.login-card` (`.wordmark`, `h1`, `.banner.banner--fail`, `.actions` or `.btn--primary.btn--wide`), then `.legal-links` > `a.linkish`. Three states: signed out, no access, login failed. |

The host must give `.login` its available width through block/stretch layout or an explicit width. `.login` is an inline-size container, so in a shrink-to-fit parent (flex row, inline-block, float) it collapses. `.actions` stacks when `.login`'s content box (its width minus side padding) is 520px or less.

`grammar.html` is the fixture of those skeletons: a zero-action title, the
five state shapes, empty, a fail banner, Settings General (title plus tabs),
Sources (state, pill, row action), sources-empty, a fail banner as on a
failed source check, a narrow Users row whose state is not clipped, and the
three sign-in states (signed out, no access, login failed) with a narrow
variant.

## What it leaves to each product

- **Wording.** Catalogs own every string. The grammar has none.
- **Page layout.** App bar, deck page, Pico forms, and the
  column tracks `.row--src` / `.row--user` stay in the product (or later in
  webauth Users/Account and gitmirror Sources).
- **Components and JavaScript.** No Svelte, no Jinja macros, no htmx. Markup
  is the product's.
- **Fonts.** No `@font-face`, no Google Fonts, no IBM Plex. The type tokens
  default to system stacks. A product that wants Plex loads it and assigns
  `--sans` / `--cond` / `--mono`.
- **Pico.** The Pico bridge and leftover selectors (`main > header`,
  `[data-state]`, `[role="alert"]`, …) stay in the product. This file does
  not reset Pico; a Pico host that puts `class="btn"` on a `button` resets
  Pico in its own leftover CSS.
- **Meaning that differs.** State words (reachable vs ready vs active),
  accent hue, which `.state--*` a domain uses.
- **Not in v0.1.** `.info` / `.pop`, `.toast`, `.block`, `.radios` / `.dot`,
  `.later`. The picture has them; no second product has asked yet.

## Override

Reassign custom properties after this file, on the same three selectors.
The accent ships as the picture's teal; a product may reassign `--accent`,
`--accent-soft`, and `--on-accent`. State colour is a token the product
sets, never `--accent`. Shape plus word carry the meaning, so a different
accent cannot break the grammar.

Atelier-2's ink-only state vocabulary:

```css
:root, :root[data-theme="dark"] {
  --ok: var(--ink); --ok-soft: var(--canvas-2);
  --busy: var(--ink); --busy-soft: var(--canvas-2);
  --fail: var(--ink); --fail-soft: var(--canvas-2);
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --ok: var(--ink); --ok-soft: var(--canvas-2);
    --busy: var(--ink); --busy-soft: var(--canvas-2);
    --fail: var(--ink); --fail-soft: var(--canvas-2);
  }
}
```

## First caller in agent-presentator

This package is vendored there as a visual no-op. The lobby still renders
with Pico leftover classes (`main > header`, `[data-tabs]`, `[data-state]`).
The first surface that adopts the grammar classes is Settings Users
([overnightworks/agent-presentator#61](https://github.com/overnightworks/agent-presentator/issues/61)),
which also restyles the shared Settings tab strip and Account onto
`.list-head` / `nav.tabs` / `.rows`. Until that item lands, the grammar CSS
in the vendored file has no markup caller in that product.

## Release

Tags are never moved. Publish a tag and attach the stylesheet as the release
asset, the same recipe webauth uses:

```sh
git tag v0.3.0
git push origin v0.3.0
gh release create v0.3.0 ui-console.css --title v0.3.0 --generate-notes
```

Consumers pin that asset URL. A broken release gets the next patch tag.
