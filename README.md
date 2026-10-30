# appkit

This package carries the design tokens and the console-page grammar that
overnightworks products share: lists of things with states, facts and fields,
and the family tokens and fonts every product wears. It refuses components,
product-specific page layout and JavaScript, with one exception: the tarball
carries the Svelte components `SignInPage`, `AccountMenu` and `LegalLinks`. A
product renders everything else through this grammar with its own markup.

`appkit.css` and every shared part follow the family picture
[`docs/family.html`](docs/family.html). `ui-style.css` and `grammar.html` stay
frozen under agent-presentator's picture `docs/mockups/m0-lobby.html` at revision
`cf31929d328b000be8db5da0d8765d48109c4376` until #30 removes them.

Distribution is a GitHub release. Tags are never moved; a broken release gets
the next patch tag. A release carries:

- the wheel `overnightworks_appkit-<version>-py3-none-any.whl` (import
  `appkit`): `appkit/static/appkit.css`, the family tokens (light under `:root`,
  dark under the device media query and `[data-theme='dark']`), the `@font-face` rules and the class `as-typed`, which keeps the case of text a person typed; and
  `appkit/static/fonts/`, Oswald 400 and 700 and Open Sans 400 and 600, latin
  and latin-ext, woff2, with each family's OFL licence;
- `overnightworks-appkit-<version>.tgz`, the npm form of the same stylesheet and
  fonts, plus the components `SignInPage`, `AccountMenu` and `LegalLinks` (`package.json` is `private`; the
  tarball is the only npm distribution): `import 'overnightworks-appkit/appkit.css'`,
  the fonts resolving through the CSS's relative `url()`, and
  `import { SignInPage } from 'overnightworks-appkit'` (`exports` `.` with
  `types` and `svelte`). `svelte` ^5.20 is its only, peer, dependency; the wheel
  holds no `.svelte`;
- `ui-style.css`, frozen, as before;
- `appkit-<version>-tokens.txt`, the sorted custom-property names `appkit.css`
  defines.

Every pull request passes the shared quality gate (`quality / verdict`, from
`overnightworks/quality`): secret scan, workflow-security scan and SonarCloud analysis of the CSS, HTML, Python and TypeScript. SonarCloud does not analyse `.svelte` files; `svelte-check`, `vitest` and the size ratchet check the component.

Pin the wheel by URL with its hash (`scripts/publish_release` prints the sha256):

```
https://github.com/overnightworks/appkit/releases/download/v0.9.0/overnightworks_appkit-0.9.0-py3-none-any.whl#sha256=<sha256>
```

A SvelteKit app takes the tarball, pinned by URL; pnpm writes its `sha512-`
integrity into the lockfile, and `scripts/publish_release` prints the same value
to compare:

```
https://github.com/overnightworks/appkit/releases/download/v0.9.0/overnightworks-appkit-0.9.0.tgz
```

## SignInPage

```svelte
<SignInPage appName="Hallucinai" state={{ page: 'signed-out', signInHref }} legalLinks={[{ label: 'Impressum', href: '/impressum' }]} />
```

One component renders the three sign-in states of the family picture
([`docs/family.html`](docs/family.html), section 3) with the ruled words:
`signed-out` ("Log in"), `no-access` ("Log out") and `login-failed` ("Try
again", with the failure banner as an alert). The sign-in link carries
`data-sveltekit-reload`, the page title is `appName`, and the glow follows the
theme. The app passes `appName`, the state (`signInHref` for the two link
states; a `LogOut` for `no-access`, below) and `legalLinks` (an empty list shows no legal row). The row is the exported
`LegalLinks` component (`<LegalLinks links={[{ label, href }]} />`): a `<nav>` named "Legal" of
same-tab links in the given order, one per entry, even when two share an href.
`place="menu"` is the look and the new-tab links of a row inside `AccountMenu`.

`no-access` logs out in one of two forms (the exported type `LogOut`, shared with other kit
components). With a callback, the button calls it and an optional `logOutFailure` text shows as
an alert. With `logOutAction`, a URL, the button submits a plain same-origin POST form to it:
no script, no token, no alert, so it works on a page prerendered with `csr = false`.

```svelte
<SignInPage appName="Hallucinai" state={{ page: 'no-access', onLogOut, logOutFailure }} legalLinks={[]} />
<SignInPage appName="Hallucinai" state={{ page: 'no-access', logOutAction: '/logout' }} legalLinks={[]} />
```

## AccountMenu

```svelte
<AccountMenu
	name="Felix"
	accountHref={accountConsoleUrl}
	onAccountOpen={() => popover.close(false)}
	appRows={[{ label: 'Settings', icon: 'settings', onSelect: openSettings }]}
	theme={{ choice, onChange: setChoice }}
	legalLinks={[{ label: 'Impressum', href: '/impressum' }]}
	{onLogOut}
	{logOutFailure}
/>
```

The panel of the family picture ([`docs/family.html`](docs/family.html), section 4): the
name as a link to the account in a new tab, the app's rows, an optional Theme row with three
radios ("Follow system", "Light", "Dark"), "Log out" in either `LogOut` form (see
`SignInPage`) and the legal row. The kit owns the panel and its rows. The app owns the trigger,
the popover with its focus handling and closing, where the menu sits, storing the theme and
setting `data-theme`, how logging out works, and the labels, actions and visibility of its rows.
The kit stores, fetches and closes nothing.

The theme radios are controlled: `onChange` reports only a different pick, and the checked radio
always equals `theme.choice`, so an app that does not take the choice sees the radio snap back.
Without `theme`, the menu shows no Theme row and writes nothing about the theme; the effective
theme stays with the app.

The app owns
its routes, the sign-out mechanism, the wording of a sign-out failure, the legal
targets, the colour slot (`--primary`, `--accent`, `--on-accent`) and loading
`appkit.css`. The component writes no `data-theme`.

A Python app (edge, songmaker's backend) takes the wheel; an app with a
frontend takes the tarball.

`ui-style.css` is still published at
`https://github.com/overnightworks/appkit/releases/download/v0.9.0/ui-style.css`.

Writing markup against it: [stylesheet reference](docs/stylesheet.md).

## Release

```sh
scripts/publish_release v<version>
```

It builds the wheel and packs the tarball, tags `main`, pushes the tag,
attaches both, `ui-style.css` and the token list, and prints the wheel's sha256
and the tarball's sha512 integrity for pins. It refuses unless the tag equals
the version in `pyproject.toml` and `package.json`, `pnpm` is installed and `pnpm install --frozen-lockfile` has run, you are on a clean `main`
equal to `origin/main`, the tag is new and `gh` is logged in.

Tests: `pnpm install --frozen-lockfile`, `pnpm run check`,
`pnpm exec vitest run <file>`, `uv run --frozen pytest -q tests` and, after
`pnpm exec playwright install chromium`, `pnpm run test:consumer`, which
builds two production consumers from the packed tarball and paints the sign-in
page in a browser (`APPKIT_TARBALL` points it at another tarball).
