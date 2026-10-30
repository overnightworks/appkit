export type SignInState =
	| { page: 'signed-out'; signInHref: string }
	| { page: 'no-access'; onLogOut: () => void; logOutFailure?: string }
	| { page: 'login-failed'; signInHref: string };

export interface LegalLink {
	label: string;
	href: string;
}

export interface SignInPageProps {
	appName: string;
	state: SignInState;
	legalLinks: readonly LegalLink[];
}
