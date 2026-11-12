import { render } from 'svelte/server';
import { describe, expect, it } from 'vitest';
import SignInPage from './SignInPage.svelte';
import { loadWords, type Language } from './words/index.ts';

const languages: Language[] = ['en', 'de'];
const words = { en: await loadWords('en'), de: await loadWords('de') };

describe.each(languages)('SignInPage server-rendered in the %s words', (language) => {
	const kit = words[language];

	it('logs out through a script-free post form when the no-access state has a logOutAction', () => {
		const { body, head } = render(SignInPage, {
			props: {
				appName: 'Hopin',
				state: { page: 'no-access', logOutAction: '/logout' },
				legalLinks: [],
				words: kit
			}
		});
		const form = /<form\b([^>]*)>(.*?)<\/form>/s.exec(body);
		expect(form?.[1]).toMatch(/method="post"/);
		expect(form?.[1]).toMatch(/action="\/logout"/);
		expect(form?.[2]).toMatch(
			new RegExp(`<button\\b[^>]*type="submit"[^>]*>${kit['signIn.logOut']}</button>`)
		);
		expect(form?.[2]).not.toMatch(/<input\b/);
		expect(body).not.toMatch(/<script\b/);
		expect(head).not.toMatch(/<script\b/);
		expect(body).not.toMatch(/role="alert"/);
	});

	it('renders the no-access face with no form, no button and no alert when the app passes no log-out form', () => {
		const { body } = render(SignInPage, {
			props: { appName: 'Hopin', state: { page: 'no-access' }, legalLinks: [], words: kit }
		});
		expect(body).toMatch(new RegExp(`<h1\\b[^>]*>${kit['signIn.noAccess']}</h1>`));
		expect(body).toContain(kit['signIn.noAccessSentence']({ appName: 'Hopin' }));
		expect(body).not.toMatch(/<form\b|<button\b|role="alert"/);
	});

	it('renders the Log in link with its address and no handler when the app starts the sign-in itself', () => {
		const { body } = render(SignInPage, {
			props: {
				appName: 'Skat',
				state: { page: 'signed-out', signInHref: '/auth/login', onSignIn: () => {} },
				legalLinks: [],
				words: kit
			}
		});
		const anchor = /<a\b([^>]*)>\s*([^<]*?)\s*<\/a>/s.exec(body);
		expect(anchor?.[1]).toMatch(/href="\/auth\/login"/);
		expect(anchor?.[1]).toMatch(/data-sveltekit-reload/);
		expect(anchor?.[2]).toBe(kit['signIn.logIn']);
		expect(body).not.toMatch(/onclick/);
	});

	it('names the legal row and renders nothing for an empty list', () => {
		const props = { appName: 'Hopin', state: { page: 'no-access' }, words: kit } as const;
		const named = render(SignInPage, { props: { ...props, legalLinks: [{ label: 'Imprint', href: '/imprint' }] } });
		expect(named.body).toContain(`<nav class="legal" aria-label="${kit['legalLinks.name']}">`);
		expect(render(SignInPage, { props: { ...props, legalLinks: [] } }).body).not.toMatch(/<nav\b/);
	});

	it.each([
		[
			'signed-out, unfinished',
			{ page: 'signed-out', signInHref: '/auth/login', unfinished: true },
			['signIn.loggedOut', 'signIn.signInUnfinished', 'signIn.logIn']
		],
		['signing-in', { page: 'signing-in', tabHref: '/app' }, ['signIn.signingIn', 'signIn.inOtherWindow', 'signIn.openInTab']],
		[
			'window-blocked',
			{ page: 'window-blocked', tabHref: '/app' },
			['signIn.windowBlocked', 'signIn.windowBlockedSentence', 'signIn.openInTab']
		],
		[
			'login-failed',
			{ page: 'login-failed', signInHref: '/auth/login' },
			['signIn.loginFailed', 'signIn.loginFailedBanner', 'signIn.tryAgain']
		],
		[
			'no-access with a callback',
			{ page: 'no-access', onLogOut: () => {} },
			['signIn.noAccess', 'signIn.logOut']
		]
	] as const)('renders the words of %s in the page', (_name, state, keys) => {
		const { body } = render(SignInPage, { props: { appName: 'Hopin', state, legalLinks: [], words: kit } });
		for (const key of keys) expect(body).toContain(kit[key]);
	});
});
