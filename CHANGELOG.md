# Changelog

## v0.7.0

The release also attaches `overnightworks-appkit-0.7.0.tgz`, the npm form of
`appkit.css` and the fonts (overnightworks/appkit#40, slice of #38). Not
breaking: the wheel's content is unchanged.

- `import 'overnightworks-appkit/appkit.css'` resolves to the stylesheet; the
  fonts resolve through its relative `url()`.
- Pin the tarball by URL; pnpm records its `sha512-` integrity.

## v0.6.0 (Breaking)

`appkit.css` follows the device when an app makes no theme choice, and carries
the family state set (overnightworks/appkit#32, slice of #25; rulings of
28.10.2026 in #31).

- With no `data-theme`, light applies, and dark applies under
  `prefers-color-scheme: dark`. `data-theme='light'` and `data-theme='dark'`
  force a theme. Each theme sets `color-scheme`.
- `--glow-primary` is gone.
- New: `--ok`, `--busy`, `--fail` and their `-soft` partners, light and dark,
  with the values of `docs/family.html`.

Migration:

- An app that wants always dark sets `data-theme='dark'` on `<html>`.
- An app that reads `--glow-primary` defines its own value from its colour at 3
  to 4 percent.
- An app drops its own `color-scheme`; the kit sets it with each theme.
- The state tokens are available; an app may move its own success, busy and
  danger colours onto them.

## v0.5.0

The `overnightworks-appkit` wheel (import `appkit`) carries `appkit.css`, the
family tokens (songmaker's names and values, dark and light) with the
`@font-face` rules, and the Oswald and Open Sans files of `@fontsource` 5.3.0
with their licences. The release also attaches `ui-style.css` (frozen,
unchanged) and the token list `appkit-<version>-tokens.txt`
(overnightworks/appkit#28, slice K1a of #25). songmaker and edge keep their
copies until K1b and K1c.


Repository renamed to `appkit` (overnightworks/appkit#25, card 2; naming rule
in edge `docs/naming.md`). No CSS change. The release asset keeps the name
`ui-style.css` until the file is retired, so the pin's path changes and the
file name does not. Older releases and their URLs redirect to the new
repository. The Sonar project key is now `overnightworks_appkit`.

## v0.4.0

Repository renamed to `ui-style` and the release asset to `ui-style.css`
(edge#24; naming rule in edge `docs/naming.md`). No CSS change except the
header comment naming the repository. Consumers change their pin's path and
file name when they bump. Existing releases keep their original asset names
(v0.1.0 `ui-tokens.css`, v0.2.0 to v0.3.1 `ui-console.css`), and their URLs
redirect.

## v0.3.1

No access shows only "Log out": "Back" is dropped because the page is reached
through the Keycloak redirect chain, so going back lands on Keycloak, which
returns a live session straight here. `.actions` stacks at a 520px viewport
again (a media query, as in the picture). `.login` is no longer a size
container and needs no width of its own, so it works in every parent.

## v0.3.0

Sign-in states: `.login`, `.login-card`, `.wordmark`, `.actions`,
`.btn--wide`, `.legal-links` and `.linkish`, coloured only through the
tokens, for the signed-out, no-access and login-failed pages. `grammar.html`
shows the three states and a narrow variant. The wordmark text, icons and
wording stay in the product. `.actions`, `.wordmark` and `.linkish` are global,
generic class names: a product that already has its own should check at
cutover. `.login` takes the full width of its parent (inside an inline-block or float parent, which has no width of its own, it collapses), and `.actions` stacks when `.login`'s content box is 520px or less.

## v0.2.0

Renamed from `ui-tokens` to `ui-console`: the package carries design tokens
AND the grammar of a console page, and `ui-tokens` no longer named that.
Package renamed, stylesheet renamed to `ui-console.css`, boundary sentence
added to the README. No CSS change except the header comment naming the
package.

## v0.1.0

Shared design tokens and the settings grammar, first release.
