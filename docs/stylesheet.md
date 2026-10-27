# appkit stylesheet reference

Contract of `ui-style.css` for an engineer writing markup against it. "The
picture" is the blessed mockup the [README](../README.md) names; the README
also says how to obtain the file.

## Beside `appkit.css`

The wheel's `appkit.css` owns the family tokens (`--bg`, `--bg-deep`,
`--surface`, `--surface-hover`, `--border`, `--text`, `--text-muted`,
`--card-bg`, `--glow-primary`, `--font-display`, `--font-body`) and the
`@font-face` rules for Oswald and Open Sans, with songmaker's names and values.
Dark is under `:root`; `[data-theme='light']` switches to light; with no
choice it stays dark. The app colour (`--primary`, `--accent`, `--on-accent`)
and everything domain-specific stay with the app. `ui-style.css` is frozen and
keeps its own token names; the two files are not loaded together.

## What `ui-style.css` owns

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

Sign-in wording is identical in every app. Each catalog carries these strings verbatim (operator ruling 19.10.2026, ui-console#6); no button names Keycloak:

- en: "Log in", "Log out", "You are logged out.", "No access", "Login failed", "Try again"
- de: "Anmelden", "Abmelden", "Du bist abgemeldet.", "Kein Zugang", "Anmeldung fehlgeschlagen", "Erneut versuchen"

Each state has one way out: Signed out shows "Log in" and never redirects by itself; No access shows "Log out" (no "Back": the page is reached through the Keycloak redirect chain, so going back returns to Keycloak, which sends a live session straight back here); Login failed shows "Try again". `.actions` stacks at a viewport of 520px or less.

Which refusal shows which page, and the redirect rule, are in webauth's [Signed out and refused](https://github.com/overnightworks/webauth/blob/main/docs/host-contract.md#signed-out-and-refused).

[`grammar.html`](../grammar.html) is the fixture of those skeletons: a zero-action title, the
five state shapes, empty, a fail banner, Settings General (title plus tabs),
Sources (state, pill, row action), sources-empty, a fail banner as on a
failed source check, a narrow Users row whose state is not clipped, and the
three sign-in states (signed out, no access, login failed) with a narrow
variant.

## What it leaves to each product

- **Wording.** Catalogs carry every string; the stylesheet has none, and grammar.html's text is sample text. Only the sign-in wording list above is ruled here.
- **Page layout.** App bar, deck page, Pico forms, and the
  column tracks `.row--src` / `.row--user` stay in the product.
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
