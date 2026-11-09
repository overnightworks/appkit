import { render } from 'svelte/server';
import { describe, expect, it } from 'vitest';
import SignInPage from './SignInPage.svelte';

describe('SignInPage server-rendered', () => {
	it('logs out through a script-free post form when the no-access state has a logOutAction', () => {
		const { body, head } = render(SignInPage, {
			props: {
				appName: 'Hopin',
				state: { page: 'no-access', logOutAction: '/logout' },
				legalLinks: []
			}
		});
		const form = /<form\b([^>]*)>(.*?)<\/form>/s.exec(body);
		expect(form?.[1]).toMatch(/method="post"/);
		expect(form?.[1]).toMatch(/action="\/logout"/);
		expect(form?.[2]).toMatch(/<button\b[^>]*type="submit"[^>]*>Log out<\/button>/);
		expect(form?.[2]).not.toMatch(/<input\b/);
		expect(body).not.toMatch(/<script\b/);
		expect(head).not.toMatch(/<script\b/);
		expect(body).not.toMatch(/role="alert"/);
	});

	it('renders the Log in link with its address and no handler when the app starts the sign-in itself', () => {
		const { body } = render(SignInPage, {
			props: {
				appName: 'Skat',
				state: { page: 'signed-out', signInHref: '/auth/login', onSignIn: () => {} },
				legalLinks: []
			}
		});
		const anchor = /<a\b([^>]*)>\s*Log in\s*<\/a>/s.exec(body);
		expect(anchor?.[1]).toMatch(/href="\/auth\/login"/);
		expect(anchor?.[1]).toMatch(/data-sveltekit-reload/);
		expect(body).not.toMatch(/onclick/);
	});
});
