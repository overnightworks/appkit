# appkit

This package carries the family look that overnightworks products share: the
family tokens, the fonts and two classes: `as-typed`, which keeps the case of text a
person typed, and `legal`, the look of the legal row. It refuses product-specific page layout and JavaScript, with one
exception: the tarball carries the Svelte components `SignInPage`, `AccountMenu`
and `LegalLinks`. A product renders everything else with its own markup. The
stylesheet's classes, tokens and legal-row markup are in the
[stylesheet reference](docs/stylesheet.md).

`appkit.css` and every shared part follow the family picture
[`docs/family.html`](docs/family.html).

Distribution is a GitHub release. Tags are never moved; a broken release gets
the next patch tag. A release carries:

- the wheel `overnightworks_appkit-<version>-py3-none-any.whl` (import
  `appkit`): `appkit/static/appkit.css`, the family tokens (light under `:root`,
  dark under the device media query and `[data-theme='dark']`), the `@font-face` rules and the two classes; and
  `appkit/static/fonts/`, Oswald 400 and 700 and Open Sans 400 and 600, latin
  and latin-ext, woff2, with each family's OFL licence;
- `overnightworks-appkit-<version>.tgz`, the npm form of the same stylesheet and
  fonts, plus the components `SignInPage`, `AccountMenu` and `LegalLinks` (`package.json` is `private`; the
  tarball is the only npm distribution): `import 'overnightworks-appkit/appkit.css'`,
  the fonts resolving through the CSS's relative `url()`, and
  `import { SignInPage } from 'overnightworks-appkit'` (`exports` `.` with
  `types` and `svelte`). `svelte` ^5.20 is its only, peer, dependency; the wheel
  holds no `.svelte`;
- `appkit-<version>-tokens.txt`, the sorted custom-property names `appkit.css`
  defines.

Every pull request passes the shared quality gate (`quality / verdict`, from
`overnightworks/quality`): secret scan, workflow-security scan and SonarCloud analysis of the CSS, HTML, Python and TypeScript. SonarCloud does not analyse `.svelte` files; `svelte-check`, `vitest` and the size ratchet check the component.

An app that serves the stylesheet from Python, without a JavaScript bundler,
pins the wheel by URL with its hash (`scripts/publish_release` prints the sha256):

```
https://github.com/overnightworks/appkit/releases/download/v<version>/overnightworks_appkit-<version>-py3-none-any.whl#sha256=<sha256>
```

A SvelteKit app takes the tarball, pinned by URL. pnpm writes its `sha512-`
integrity into the lockfile only when it downloads the tarball, not on a store
hit, and a frozen install enforces it; `scripts/publish_release` prints the
value to compare or enter:

```
https://github.com/overnightworks/appkit/releases/download/v<version>/overnightworks-appkit-<version>.tgz
```

## SignInPage

```svelte
<script>
	const legalLinks = [
		{ label: 'Impressum', href: 'https://hallucinai.de/impressum#songmaker' },
		{ label: 'Datenschutz', href: 'https://hallucinai.de/datenschutz#songmaker' },
		{ label: 'Nutzungsbedingungen', href: 'https://hallucinai.de/nutzungsbedingungen#songmaker' }
	];
</script>

<SignInPage
	appName="Hallucinai"
	state={{ page: 'signed-out', signInHref }}
	{legalLinks}
/>
```

One component renders the three sign-in states of the family picture
([`docs/family.html`](docs/family.html), section 3): `signed-out`,
`no-access` and `login-failed` (with the failure banner as an alert). Their ruled
words are in the [stylesheet reference](docs/stylesheet.md#what-appkitcss-owns). The sign-in link carries
`data-sveltekit-reload`, the page title is `appName`, and the glow follows the
theme. The app passes `appName`, the state (`signInHref` for the two link
states; a `LogOut` for `no-access`, below), `legalLinks` (an empty list shows no legal row) and optionally `words` (a `SignInPageWords`: every sign-in word, the no-access sentence as a function of `appName`; absent renders the en words). The row is the exported
`LegalLinks` component (`<LegalLinks links={[{ label, href }]} />`): a `<nav>` of
same-tab links in the given order, one per entry, even when two share an href;
`newTab` opens them in a new tab with the same look.
The look comes from `appkit.css`, not from the component. Where the links stand, `place` and the hand-written row are in [Where the legal links stand](docs/stylesheet.md#where-the-legal-links-stand).

`no-access` logs out in one of two forms (the exported type `LogOut`, shared with other kit
components). With a callback, the button calls it and an optional `logOutFailure` text shows as
an alert. With `logOutAction`, a URL, the button submits a plain same-origin POST form to it:
no script, no token, no alert, so it works on a page prerendered with `csr = false`.

```svelte
<SignInPage
	appName="Hallucinai"
	state={{ page: 'no-access', onLogOut, logOutFailure }}
	{legalLinks}
/>
<SignInPage
	appName="Hallucinai"
	state={{ page: 'no-access', logOutAction: '/logout' }}
	{legalLinks}
/>
```

## AccountMenu

```svelte
<AccountMenu
	name="Felix"
	accountHref={accountConsoleUrl}
	onAccountOpen={() => popover.close(false)}
	appRows={[{ label: 'Settings', onSelect: openSettings }]}
	theme={{ choice, onChange: setChoice }}
	{legalLinks}
	{onLogOut}
	{logOutFailure}
/>
```

The panel of the family picture ([`docs/family.html`](docs/family.html), section 4): the name as
a link to the account in a new tab, the app's rows, an optional theme row with three radios,
the log-out button in either `LogOut` form (see `SignInPage`) and the
legal row. The kit owns the panel and its rows, which are taller on a touch screen. The app owns
the trigger, the popover with its focus handling and closing, where the menu sits, storing the
theme and setting `data-theme`, how logging out works, and the labels, actions and visibility of
its rows. The optional `words` prop (an `AccountMenuWords`; its words are in the [stylesheet reference](docs/stylesheet.md#what-appkitcss-owns)) carries the menu's own words in the app's language; absent renders the en words. The kit stores, fetches and closes nothing.

The theme radios are controlled: `onChange` reports only a different pick, and the checked radio
always equals `theme.choice`, so an app that does not take the choice sees the radio snap back.
Without `theme`, the menu shows no Theme row and writes nothing about the theme; the effective
theme stays with the app.

The app owns
its routes, the sign-out mechanism, the wording of a sign-out failure, the legal
targets, the [app colour](docs/stylesheet.md#what-it-leaves-to-each-product) and loading
`appkit.css`. The component writes no `data-theme`.

## Release

```sh
scripts/publish_release v<version>
```

It builds the wheel and packs the tarball, tags `main`, pushes the tag,
attaches both and the token list, and prints the wheel's sha256
and the tarball's sha512 integrity for pins. It needs installed dependencies
(`pnpm install --frozen-lockfile`) and refuses unless the tag equals the version
in `pyproject.toml` and `package.json`, `pnpm` is installed, you are on a clean `main`
equal to `origin/main`, the tag is new and `gh` is logged in.

Tests: `pnpm install --frozen-lockfile`, `pnpm run check`,
`pnpm exec vitest run <file>`, `uv run --frozen pytest -q tests` and, after
`pnpm exec playwright install chromium`, `pnpm run test:consumer`, which
builds two production consumers from the packed tarball and paints the sign-in
page in a browser (`APPKIT_TARBALL` points it at another tarball).
