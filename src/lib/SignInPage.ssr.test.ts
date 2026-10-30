import { render } from 'svelte/server';
import { describe, expect, it } from 'vitest';
import SignInPage from './SignInPage.svelte';

describe('SignInPage server-rendered', () => {
	it('logs out through a script-free post form when the no-access state has a logOutAction', () => {
		const { body } = render(SignInPage, {
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
		expect(body).not.toContain('onclick');
	});
});
