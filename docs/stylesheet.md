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

It also owns one class, `as-typed`, which turns the case transform and the
letter-spacing off. Text the app writes keeps the family's uppercase. Text a
person typed (a name, slug or address) keeps its case, also in `h1`, `h2` and
the page head's `h3`. An app marks such text with `as-typed` on the element that
holds only the typed text: a `span` inside the heading, because a heading's own
selector may outrank a single class on the heading itself.

```html
<h3>Source <span class="as-typed">talks</span></h3>
```

Sign-in wording is identical in every app. Each catalog carries these strings verbatim (operator ruling 19.10.2026, ui-console#6); no button names Keycloak:

- en: "Log in", "Log out", "You are logged out.", "No access", "Login failed", "Try again", "Legal"
- de: "Anmelden", "Abmelden", "Du bist abgemeldet.", "Kein Zugang", "Anmeldung fehlgeschlagen", "Erneut versuchen"

The tarball's `SignInPage` component renders these en strings and two kit-owned sentences from the family picture: "Sign-in did not work. Please try again." (login failed) and "You are signed in, but this account has no access to <app name>." (no access). The de strings are not ruled for it.

The tarball's `AccountMenu` component renders the en words of the family picture's account menu: "Theme", "Follow system", "Light", "Dark" and "Log out", and `LegalLinks` names its `<nav>` "Legal" (an accessible name, not printed). The de strings are not ruled for it.

Each state has one way out: Signed out shows "Log in" and never redirects by itself; No access shows "Log out" (no "Back": the page is reached through the Keycloak redirect chain, so going back returns to Keycloak, which sends a live session straight back here); Login failed shows "Try again". `.actions` stacks at a viewport of 520px or less.

Which refusal shows which page, and the redirect rule, are in webauth's [Signed out and refused](https://github.com/overnightworks/webauth/blob/main/docs/host-contract.md#signed-out-and-refused).

## What it leaves to each product

- **Wording.** Catalogs carry every string; the stylesheet has none. Only the sign-in wording list above is ruled here.
- **Page layout and markup.** App bar, page structure, forms and any markup outside the three components stay in the product.
- **The app colour.** `--primary`, `--accent` and `--on-accent` stay with the app, which also loads `appkit.css`.
- **Meaning that differs.** State words (reachable vs ready vs active) and which state a domain shows.
