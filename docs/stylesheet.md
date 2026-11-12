# design stylesheet reference

Reference of `design.css` and the components' words, for an engineer writing
markup against the kit.

## What `design.css` owns

The wheel's `design.css` owns the family tokens and the
`@font-face` rules for Oswald and Open Sans. The token names are the release's
`design-<version>-tokens.txt`, which `scripts/list_tokens` prints for any stylesheet.
Light is under `:root`; dark sits under the device media query guarded by
`:root:not([data-theme='light'])` and under `:root[data-theme='dark']`, so with
no choice the page follows the device and either attribute forces its theme.
Each theme sets `color-scheme`, so an app sets none. Everything
domain-specific stays with the app.

It also owns two classes. The first, `as-typed`, turns the case transform and the
letter-spacing off. Text the app writes keeps the family's uppercase. Text a
person typed (a name, slug or address) keeps its case, also in `h1`, `h2` and
the page head's `h3`. An app marks such text with `as-typed` on the element that
holds only the typed text: a `span` inside the heading, because a heading's own
selector may outrank a single class on the heading itself. The second, `legal`, is the look of the legal row, described under [Writing the legal row by hand](#writing-the-legal-row-by-hand).

```html
<h3>Source <span class="as-typed">talks</span></h3>
```

## What the fail colour marks

The sentences in this section are ruled.

The fail colour (`--fail` and `--fail-soft`) marks only two things: that something failed, and a control that deletes something for good. Such a control is the Delete in a menu or a toolbar and the button that confirms a deletion. A delete icon beside each row stays neutral, so the signal does not wear out.

## Sign-in wording

The sentences in this section are ruled.

Sign-in wording is identical in every app. The kit's catalogs carry these strings verbatim; no button names Keycloak:

- en: "Log in", "Log out", "You are logged out.", "No access", "Login failed", "Try again", "Legal"
- de: "Anmelden", "Abmelden", "Du bist abgemeldet.", "Kein Zugang", "Anmeldung fehlgeschlagen", "Erneut versuchen"

## The components' words

The tarball's `SignInPage`, `AccountMenu` and `AgentControl` components take their words from the kit's catalogs: the app loads them with `loadKitWords` for the page's language and passes them as the required prop `words`, see the [README](../README.md#the-kits-words); [Languages](languages.md) requires that the kit ships its words per language.

`SignInPage` shows the strings above, the failure banner of a login that failed, the sentence of no access, which names the app, the sentence of a sign-in that did not finish, the words of the signing-in state and the words of the window-blocked state. The list above binds the sign-in words in the kit's catalogs; the de strings of the other words are not ruled.

`AccountMenu` shows the name of the theme row, its three choices and "Log out". The de strings of the theme rows are not ruled.

`AgentControl` shows the three action words, the two accessible-name patterns (which include the agent's name), the empty sentence and the five refusal sentences, one for each of `not-allowed`, `owner-absent`, `place-full`, `agent-unavailable` and `try-again`. The de words are ruled: "Rufen", "Wird gerufen…", "Bitten zu gehen", "Mozart rufen", "Mozart bitten zu gehen", "Gerade ist kein Agent erreichbar." and the refusals "Du darfst diesen Agenten nicht rufen.", "Sein Besitzer ist nicht hier.", "Hier ist kein Platz für einen weiteren Agenten.", "Der Agent ist gerade nicht erreichbar." and "Das hat nicht geklappt. Versuch es noch einmal." A `here` row draws its ask-to-leave button only when the app passes `onSendAway`; without it the row shows the AI mark and the name.

The tarball's `AiMark` component takes no words: its text is "AI" in every language, so a caller passes nothing. Its size is fixed, not relative to the place it stands in.

Each state has at most one way out: Signed out shows "Log in" and never redirects by itself; No access shows "Log out" (no "Back": the page is reached through the Keycloak redirect chain, so going back returns to Keycloak, which sends a live session straight back here), unless the app passes no log-out form, as inside a call's frame; Login failed shows "Try again"; Signing in shows only "Open in a tab", a link that opens the app in a tab of its own; Window blocked, shown when the browser blocked the sign-in window, shows only the same link.

Which refusal shows which page, and the redirect rule, are in webauth's [Signed out and refused](https://github.com/overnightworks/webauth/blob/main/docs/host-contract.md#signed-out-and-refused).

## Where the legal links stand

The sentences in this section are ruled.

The legal links stand in the same three places in every app, and no app writes its own legal-row markup:

- On every signed-in page, in the legal row of `AccountMenu`. A signed-in page carries no footer of legal links.
- On the `SignInPage` states, in the row under the card.
- On a page without the account menu (a public or session-less page), in `LegalLinks` with `place='page'`.

Every legal row lists Impressum, Datenschutz and Nutzungsbedingungen, in that order. Each link carries the app's section anchor `#<app>`, as in `https://hallucinai.de/impressum#songmaker`.

Two kinds of page show no legal links: full-screen presentation views (presenter and projector), and pages that send themselves on, such as webauth's end-session page.

hopin and hal deviate by name:

- hopin: a running call shows no account menu, so its links stand in `LegalLinks` with `place='menu'` in the call's More menu.
- hal: its account console shows no legal links, and its central sign-in pages show the row inside the card, in Keycloak's card-footer slot.

## Writing the legal row by hand

An app's page that cannot render Svelte writes the same row by hand: `<nav class="legal" aria-label="Legal">` holding one `<a href>` per link in that order, with no separator characters. The accessible name, not printed, is the literal "Legal" in every app, as in `LegalLinks`'s `<nav>`. The row then gets its look from `design.css`, as the component's does; the menu form (`legal menu`) is the kit's own and is not offered. The page keeps the row's spacing and placement relative to its neighbours.

```html
<nav class="legal" aria-label="Legal"><a href="https://hallucinai.de/impressum#songmaker">Impressum</a><a href="https://hallucinai.de/datenschutz#songmaker">Datenschutz</a><a href="https://hallucinai.de/nutzungsbedingungen#songmaker">Nutzungsbedingungen</a></nav>
```

A page that belongs to no single app, such as Keycloak's central sign-in pages, writes the same row with the addresses the central legal pages give it.

`LegalLinks` takes `place`: `'page'` (the default) for a row on a page, `'menu'` for the look of a row inside a menu, whose links open in a new tab.

hal's [docs/keycloak.md](https://github.com/overnightworks/hal/blob/main/docs/keycloak.md#theme-and-language) gives the reasons for hal's deviations above.

## What it leaves to each product

- **Wording.** The kit's catalogs carry the components' words and the app's catalogs every other string; the stylesheet has none. Only the sign-in and AgentControl wording lists above are ruled here.
- **Page layout and markup.** App bar, page structure, forms and any markup outside the components stay in the product, as do the legal row's spacing and placement around it. A product keeps its own selectors off the legal row: a rule that reaches the row or its links through an ancestor (`.top nav a`, say) can change the kit's look.
- **The app colour.** `--primary`, `--accent` and `--on-accent`; `design.css` defines none of them.
- **Meaning that differs.** State words (reachable vs ready vs active) and which state a domain shows.
