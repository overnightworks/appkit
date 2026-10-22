# Changelog

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
