/**
 * How a kit component logs out, in one of two forms.
 * With `onLogOut`, the button calls it and an optional `logOutFailure` text shows as an alert.
 * With `logOutAction`, a URL, the button submits a plain same-origin POST form to it: no script,
 * no token, no alert, so it works on a page prerendered with `csr = false`.
 */
export type LogOut =
	| { onLogOut: () => void; logOutFailure?: string; logOutAction?: never }
	| { logOutAction: string; onLogOut?: never; logOutFailure?: never };

/**
 * The three sign-in states: `signed-out` and `login-failed` link to `signInHref`
 * (`login-failed` adds a failure banner, as an alert); `no-access` logs out in either `LogOut` form.
 * Their words are listed in docs/stylesheet.md.
 */
export type SignInState =
	| { page: 'signed-out'; signInHref: string }
	| ({ page: 'no-access' } & LogOut)
	| { page: 'login-failed'; signInHref: string };

/** One entry of the legal row; the row keeps the given order and renders one link per entry, even when two share an href. */
export interface LegalLink {
	label: string;
	href: string;
}

/** `page` links open in the same tab; `menu` is the row inside `AccountMenu`, whose links open in a new tab. */
export type LegalLinksPlace = 'page' | 'menu';

/**
 * Props of `LegalLinks`, a `<nav>` of the given links; an empty list renders nothing.
 * `newTab` opens a `page` row's links in a new tab with the same look.
 * The look comes from `appkit.css`, not from the component.
 */
export type LegalLinksProps =
	| { links: readonly LegalLink[]; place?: 'page'; newTab?: boolean }
	| { links: readonly LegalLink[]; place: 'menu'; newTab?: never };

/** The effective choice, never the resolved colour. */
export type ThemeChoice = 'follow-system' | 'light' | 'dark';

/**
 * The theme radios are controlled: the checked radio always equals `choice`,
 * so an app that does not take the reported pick sees the radio snap back.
 * The component stores nothing and writes no `data-theme`; the effective theme stays with the app.
 */
export interface ThemeRows {
	choice: ThemeChoice;
	/** Called only when a different radio is selected. */
	onChange: (choice: ThemeChoice) => void;
}

/** A row the app adds to the account panel, rendered above Theme. */
export interface AppRow {
	label: string;
	onSelect: () => void;
}

/** The menu's own words, in the app's language. Whole or absent: an app cannot pass half a language. */
export interface AccountMenuWords {
	theme: string;
	followSystem: string;
	light: string;
	dark: string;
	logOut: string;
}

/** The sign-in page's own words, in the app's language. Whole or absent. */
export interface SignInPageWords {
	loggedOut: string;
	logIn: string;
	loginFailed: string;
	loginFailedBanner: string;
	tryAgain: string;
	noAccess: string;
	noAccessSentence: (appName: string) => string;
	logOut: string;
}

/**
 * The account panel: the name as a link to the account, the app's rows, an optional theme row,
 * the log-out button and the legal row. The kit owns the panel and its rows, which are taller
 * on a touch screen. The app owns the trigger, the popover with its focus handling and closing,
 * where the menu sits, storing the theme, how logging out works, and the labels, actions and
 * visibility of its rows. The kit stores, fetches and closes nothing.
 */
export type AccountMenuProps = {
	/** The signed-in person's name; it keeps the case it was typed in. */
	name: string;
	/** The name links here and opens it in a new tab. */
	accountHref: string;
	/** The name link was activated. */
	onAccountOpen: () => void;
	/** Rendered above Theme; an empty list renders none. */
	appRows: readonly AppRow[];
	/** Absent renders no Theme row and writes nothing about the theme. */
	theme?: ThemeRows;
	/** An empty list shows no legal row. */
	legalLinks: readonly LegalLink[];
	/** Absent renders the en words. */
	words?: AccountMenuWords;
} & LogOut;

/**
 * The sign-in page. The sign-in link carries `data-sveltekit-reload`, and the glow follows the theme.
 * The app owns its routes, the sign-out mechanism, the wording of a sign-out failure, the legal
 * targets, the app colour and loading `appkit.css`.
 */
export interface SignInPageProps {
	/** The page title. */
	appName: string;
	state: SignInState;
	/** An empty list shows no legal row. */
	legalLinks: readonly LegalLink[];
	/** Absent renders the en words. */
	words?: SignInPageWords;
}
