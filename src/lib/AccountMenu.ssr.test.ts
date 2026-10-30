import { render } from 'svelte/server';
import { describe, expect, it } from 'vitest';
import AccountMenu from './AccountMenu.svelte';

describe('AccountMenu server-rendered', () => {
	it('logs out through a script-free post form when it has a logOutAction', () => {
		const { body, head } = render(AccountMenu, {
			props: {
				name: 'Felix',
				accountHref: 'https://account.example/me',
				onAccountOpen: () => {},
				appRows: [],
				legalLinks: [],
				logOutAction: '/logout'
			}
		});
		const form = /<form\b([^>]*)>(.*?)<\/form>/s.exec(body);
		expect(form?.[1]).toMatch(/method="post"/);
		expect(form?.[1]).toMatch(/action="\/logout"/);
		expect(form?.[2]).toMatch(/<button\b[^>]*type="submit"[^>]*>.*Log out<\/button>/s);
		expect(form?.[2]).not.toMatch(/<input\b/);
		expect(body).not.toMatch(/<script\b|onclick/);
		expect(head).not.toMatch(/<script\b/);
		expect(body).not.toMatch(/role="alert"/);
	});
});
