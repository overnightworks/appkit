import { render } from 'svelte/server';
import { describe, expect, it } from 'vitest';
import LegalLinks from './LegalLinks.svelte';
import { loadWords, type Language } from './words/index.ts';

const links = [{ label: 'Imprint', href: '/imprint' }];

describe.each<Language>(['en', 'de'])('LegalLinks server-rendered in the %s words', (language) => {
	it('names the row on a page and in a menu', async () => {
		const words = await loadWords(language);
		const page = render(LegalLinks, { props: { links, words } }).body;
		const menu = render(LegalLinks, { props: { links, words, place: 'menu' } }).body;
		expect(page).toContain(`<nav class="legal" aria-label="${words['legalLinks.name']}">`);
		expect(menu).toContain(`<nav class="legal menu" aria-label="${words['legalLinks.name']}">`);
	});

	it('renders nothing for an empty list', async () => {
		const words = await loadWords(language);
		expect(render(LegalLinks, { props: { links: [], words } }).body).not.toMatch(/<nav\b/);
	});
});
