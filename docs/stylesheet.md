# appkit stylesheet reference

Reference of `appkit.css` and the components' words, for an engineer writing
markup against the kit. The family picture is [`family.html`](family.html).

## What `appkit.css` owns

The wheel's `appkit.css` owns the family tokens (`--bg`, `--bg-deep`,
`--surface`, `--surface-hover`, `--border`, `--text`, `--text-muted`,
`--card-bg`, `--header-bg`, `--ok`, `--ok-soft`, `--busy`, `--busy-soft`, `--fail`,
`--fail-soft`, `--font-display`, `--font-body`) and the
`@font-face` rules for Oswald and Open Sans, with songmaker's names and values.
Light is under `:root`; dark sits under the device media query guarded by
`:root:not([data-theme='light'])` and under `:root[data-theme='dark']`, so with
no choice the page follows the device and either attribute forces its theme.
Each theme sets `color-scheme`, so an app sets none. The app colour (`--primary`, `--accent`, `--on-accent`)
and everything domain-specific stay with the app.

It also owns two classes. The first, `as-typed`, turns the case transform and the
letter-spacing off. Text the app writes keeps the family's uppercase. Text a
person typed (a name, slug or address) keeps its case, also in `h1`, `h2` and
the page head's `h3`. An app marks such text with `as-typed` on the element that
holds only the typed text: a `span` inside the heading, because a heading's own
selector may outrank a single class on the heading itself. The second, `legal`, is the look of the legal row, described under "Where the legal links stand".

```html
<h3>Source <span class="as-typed">talks</span></h3>
```

Sign-in wording is identical in every app. Each catalog carries these strings verbatim (operator ruling 19.10.2026, ui-console#6); no button names Keycloak:

- en: "Log in", "Log out", "You are logged out.", "No access", "Login failed", "Try again", "Legal"
- de: "Anmelden", "Abmelden", "Du bist abgemeldet.", "Kein Zugang", "Anmeldung fehlgeschlagen", "Erneut versuchen"

The tarball's `SignInPage` component takes its words from the app's catalog through the `words` prop; the kit holds no language and no de string. The list above binds the sign-in words in every catalog. Without `words` it renders the en strings and two sentences from the family picture: "Sign-in did not work. Please try again." (login failed) and "You are signed in, but this account has no access to <app name>." (no access). The de strings of those two sentences are not ruled.

The tarball's `AccountMenu` component takes its words from the app's catalog through the `words` prop: "Theme", "Follow system", "Light", "Dark" and "Log out". Without `words` it renders those en words of the family picture's account menu. The de strings of the theme rows are not ruled. `LegalLinks` names its `<nav>` "Legal" (an accessible name, not printed) in every app.

Each state has one way out: Signed out shows "Log in" and never redirects by itself; No access shows "Log out" (no "Back": the page is reached through the Keycloak redirect chain, so going back returns to Keycloak, which sends a live session straight back here); Login failed shows "Try again".

Which refusal shows which page, and the redirect rule, are in webauth's [Signed out and refused](https://github.com/overnightworks/webauth/blob/main/docs/host-contract.md#signed-out-and-refused).

## Where the legal links stand

The legal links stand in the same three places in every app (operator ruling 05.11.2026, appkit#82), and no app writes its own legal-row markup:

- On every signed-in page, in the legal row of `AccountMenu`. A signed-in page carries no footer of legal links.
- On the `SignInPage` states, in the row under the card.
- On a page without the account menu (a public or session-less page), in `LegalLinks` with `place='page'`.

Every legal row lists Impressum, Datenschutz and Nutzungsbedingungen, in that order (operator ruling 05.11.2026, appkit#86). Each link carries the app's section anchor `#<app>`, as in `https://hallucinai.de/impressum#songmaker`. A page that belongs to no single app, such as the central sign-in, links the address the central legal pages give it.

Two kinds of page show no legal links: full-screen presentation views (presenter and projector), and pages that send themselves on, such as webauth's end-session page.

An app's page that cannot render Svelte writes the same row by hand: `<nav class="legal" aria-label="Legal">` holding one `<a href>` per link in that order, with no separator characters. The accessible name is the literal "Legal". The row then gets its look from `appkit.css`, as the component's does; the menu form (`legal menu`) is the kit's own and is not offered. The page keeps the row's spacing and placement relative to its neighbours.

```html
<nav class="legal" aria-label="Legal"><a href="https://hallucinai.de/impressum#songmaker">Impressum</a><a href="https://hallucinai.de/datenschutz#songmaker">Datenschutz</a><a href="https://hallucinai.de/nutzungsbedingungen#songmaker">Nutzungsbedingungen</a></nav>
```

A shared page, such as Keycloak's login pages, writes the same row with the addresses the central legal pages give it.

hopin and hal deviate by name:

- hopin (operator ruling 05.11.2026, hopin#494): a running call shows no account menu, so its links stand in `LegalLinks` with `place='menu'` in the call's More menu.
- hal (hal#1024, lines 1 and 2): its account console shows no legal links, and its central sign-in pages show the row inside the card, in Keycloak's card-footer slot. hal's [docs/keycloak.md](https://github.com/overnightworks/hal/blob/main/docs/keycloak.md#theme-and-language) gives the reasons.

## What it leaves to each product

- **Wording.** Catalogs carry every string; the stylesheet has none. Only the sign-in wording list above is ruled here.
- **Page layout and markup.** App bar, page structure, forms and any markup outside the three components stay in the product, as do the legal row's spacing and placement around it. A product keeps its own selectors off the legal row: a rule that reaches the row or its links through an ancestor (`.top nav a`, say) can change the kit's look.
- **The app colour.** `--primary`, `--accent` and `--on-accent`; `appkit.css` defines none of them.
- **Meaning that differs.** State words (reachable vs ready vs active) and which state a domain shows.
