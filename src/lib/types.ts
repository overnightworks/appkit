/** How a kit component logs out: through the app's callback, or through a plain same-origin POST form that needs no script. */
export type LogOut =
	| { onLogOut: () => void; logOutFailure?: string; logOutAction?: never }
	| { logOutAction: string; onLogOut?: never; logOutFailure?: never };

export type SignInState =
	| { page: 'signed-out'; signInHref: string }
	| ({ page: 'no-access' } & LogOut)
	| { page: 'login-failed'; signInHref: string };

export interface LegalLink {
	label: string;
	href: string;
}

export type LegalLinksPlace = 'page' | 'menu';

export type LegalLinksProps =
	| { links: readonly LegalLink[]; place?: 'page'; newTab?: boolean }
	| { links: readonly LegalLink[]; place: 'menu'; newTab?: never };

/** The effective choice, never the resolved colour. */
export type ThemeChoice = 'follow-system' | 'light' | 'dark';

export interface ThemeRows {
	choice: ThemeChoice;
	/** Called only when a different radio is selected. */
	onChange: (choice: ThemeChoice) => void;
}

export type AppRowIcon = 'settings';

export interface AppRow {
	label: string;
	icon: AppRowIcon;
	onSelect: () => void;
}

export type AccountMenuProps = {
	name: string;
	accountHref: string;
	/** The name link was activated. */
	onAccountOpen: () => void;
	/** Rendered above Theme; an empty list renders none. */
	appRows: readonly AppRow[];
	/** Absent renders no theme rows. */
	theme?: ThemeRows;
	legalLinks: readonly LegalLink[];
} & LogOut;

export interface SignInPageProps {
	appName: string;
	state: SignInState;
	legalLinks: readonly LegalLink[];
}
