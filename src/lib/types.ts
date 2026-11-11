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
 * The five sign-in states: `signed-out` and `login-failed` link to `signInHref`
 * (`login-failed` adds a failure banner, as an alert); `no-access` logs out in either `LogOut` form,
 * or shows no log-out action when the app passes none (inside a call's frame).
 * `signed-out` may carry `onSignIn`, called by a plain click on "Log in" instead of following the link
 * (an app opens the sign-in in a separate window), and `unfinished`, which shows that a sign-in did not finish.
 * `signing-in` shows that the sign-in runs in the other window and links to `tabHref`, which opens the app in a tab.
 * `window-blocked` shows that the browser blocked that window and offers only the same link to `tabHref`.
 * Their words are listed in docs/stylesheet.md.
 */
export type SignInState =
	| { page: 'signed-out'; signInHref: string; onSignIn?: () => void; unfinished?: true }
	| { page: 'signing-in'; tabHref: string }
	| { page: 'window-blocked'; tabHref: string }
	| ({ page: 'no-access' } & LogOut)
	| { page: 'no-access'; onLogOut?: never; logOutAction?: never; logOutFailure?: never }
	| { page: 'login-failed'; signInHref: string };

/** One entry of the legal row; the row keeps the given order and renders one link per entry, even when two share an href. */
export interface LegalLink {
	label: string;
	href: string;
}

/** `page` links open in the same tab unless `newTab` is set; `menu` is the row inside `AccountMenu`, whose links open in a new tab. */
export type LegalLinksPlace = 'page' | 'menu';

/**
 * Props of `LegalLinks`, a `<nav>` of the given links; an empty list renders nothing.
 * `newTab` opens a `page` row's links in a new tab with the same look.
 * The look comes from `design.css`, not from the component.
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
	signingIn: string;
	inOtherWindow: string;
	openInTab: string;
	windowBlocked: string;
	windowBlockedSentence: string;
	signInUnfinished: string;
}

/**
 * The account panel: the name as a link to the account, the app's rows, an optional theme row,
 * the log-out button and the legal row. The kit owns the panel and its rows, which are taller
 * on a touch screen. It stores, fetches and closes nothing.
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
 * It stores, fetches and closes nothing.
 */
export interface SignInPageProps {
	/** The page title. */
	appName: string;
	state: SignInState;
	/** An empty list shows no legal row. */
	legalLinks: readonly LegalLink[];
	/** Opens the legal row's links in a new tab, for a page shown inside another app's frame. */
	legalLinksNewTab?: boolean;
	/** Absent renders the en words. */
	words?: SignInPageWords;
}

/** One row of the agent control. */
export interface AgentRow {
	/** Opaque and minted by the app; the kit hands it back to `onCall` and `onSendAway`. */
	key: string;
	/** Shown as given. */
	name: string;
	/** `inviting` is a call under way, `here` an agent in the place. */
	state: 'available' | 'inviting' | 'here';
}

/** Why a call or a send-away was refused; the same five reasons serve both actions. */
export type AgentControlRefusal =
	| 'not-allowed'
	| 'owner-absent'
	| 'place-full'
	| 'agent-unavailable'
	| 'try-again';

/**
 * The control's own words, in the app's language. Whole or absent: an app cannot pass half a language.
 * The two labels are the accessible names of the action buttons, which include the agent's name.
 */
export interface AgentControlWords {
	call: string;
	calling: string;
	askToLeave: string;
	callLabel: (name: string) => string;
	askToLeaveLabel: (name: string) => string;
	/** The sentence shown when no agent is listed. */
	empty: string;
	refusals: Record<AgentControlRefusal, string>;
}

/**
 * The panel of rows with which a person calls an agent into a place and asks it to leave again:
 * each row leads with `AiMark`, then the name, then one action or the waiting text.
 * Trigger and popover stay with the app. The control holds no state of the call: the app sets
 * `rows` and `refusal` and clears them. Asking to leave takes effect at once, with no confirm step.
 */
export interface AgentControlProps {
	/** An empty list draws only the `words.empty` sentence, and the refusal when one is set. */
	rows: readonly AgentRow[];
	/** Called with the row's key by the button of an `available` row. */
	onCall: (key: string) => void;
	/**
	 * Called with the row's key by the button of a `here` row. Absent, a `here` row shows the mark and the
	 * name and no action, as an `inviting` row shows no button.
	 */
	onSendAway?: (key: string) => void;
	/** Its sentence shows above the rows as an alert until the app clears it. */
	refusal?: AgentControlRefusal;
	/** Absent renders the en words. */
	words?: AgentControlWords;
}
