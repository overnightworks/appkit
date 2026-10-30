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

export interface LegalLinksProps {
	links: readonly LegalLink[];
}

export interface SignInPageProps {
	appName: string;
	state: SignInState;
	legalLinks: readonly LegalLink[];
}
