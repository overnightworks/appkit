import { render } from 'svelte/server';
import { describe, expect, it } from 'vitest';
import AccountMenu from './AccountMenu.svelte';
import { loadWords, type Language } from './words/index.ts';

describe('AccountMenu server-rendered', () => {
	it.each<Language>(['en', 'de'])(
		'logs out through a script-free post form in the %s words when it has a logOutAction',
		async (language) => {
			const words = await loadWords(language);
			const { body, head } = render(AccountMenu, {
				props: {
					name: 'Felix',
					accountHref: 'https://account.example/me',
					onAccountOpen: () => {},
					appRows: [],
					legalLinks: [],
					logOutAction: '/logout',
					theme: { choice: 'dark', onChange: () => {} },
					words
				}
			});
			const form = /<form\b([^>]*)>(.*?)<\/form>/s.exec(body);
			expect(form?.[1]).toMatch(/method="post"/);
			expect(form?.[1]).toMatch(/action="\/logout"/);
			expect(form?.[2]).toMatch(
				new RegExp(`<button\\b[^>]*type="submit"[^>]*>.*${words['account.logOut']}</button>`, 's')
			);
			expect(form?.[2]).not.toMatch(/<input\b/);
			expect(body).toContain(words['account.theme']);
			expect(body).not.toMatch(/<script\b|onclick/);
			expect(head).not.toMatch(/<script\b/);
			expect(body).not.toMatch(/role="alert"/);
		}
	);
});
