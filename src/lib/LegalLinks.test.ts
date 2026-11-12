import { mount, tick, unmount } from 'svelte';
import { afterEach, describe, expect, it } from 'vitest';
import LegalLinks from './LegalLinks.svelte';
import type { LegalLink } from './types.ts';
import { loadWords, type Language } from './words/index.ts';

const words = { en: await loadWords('en'), de: await loadWords('de') };

const mounted: { target: HTMLElement; component: ReturnType<typeof mount> }[] = [];

async function render(
	links: readonly LegalLink[],
	options: { place?: 'page'; newTab?: boolean } | { place: 'menu' } = {},
	language: Language = 'en'
): Promise<HTMLElement> {
	const target = document.createElement('div');
	document.body.append(target);
	mounted.push({ target, component: mount(LegalLinks, { target, props: { links, words: words[language], ...options } }) });
	await tick();
	return target;
}

afterEach(async () => {
	for (const { target, component } of mounted.splice(0)) {
		await unmount(component);
		target.remove();
	}
});

describe('LegalLinks', () => {
	it('renders one link per entry in the given order with its label and href', async () => {
		const page = await render([
			{ label: 'Privacy', href: '/privacy' },
			{ label: 'Imprint', href: '/imprint' },
			{ label: 'Terms', href: '/terms' }
		]);
		const anchors = [...page.querySelectorAll('nav > a')];
		expect(anchors.map((anchor) => anchor.textContent)).toEqual(['Privacy', 'Imprint', 'Terms']);
		expect(anchors.map((anchor) => anchor.getAttribute('href'))).toEqual(['/privacy', '/imprint', '/terms']);
		expect(anchors.some((anchor) => anchor.hasAttribute('target'))).toBe(false);
	});

	it('renders nothing for an empty list', async () => {
		const page = await render([]);
		expect(page.querySelector('nav')).toBeNull();
	});

	it('renders both entries that share one href', async () => {
		const page = await render([
			{ label: 'Imprint', href: '/legal' },
			{ label: 'Privacy', href: '/legal' }
		]);
		expect([...page.querySelectorAll('a')].map((anchor) => anchor.textContent)).toEqual(['Imprint', 'Privacy']);
	});

	it.each<Language>(['en', 'de'])('is named in the %s words on a page and opens links in the same tab', async (language) => {
		const page = await render([{ label: 'Imprint', href: '/imprint' }], {}, language);
		expect(page.querySelector('nav')?.getAttribute('aria-label')).toBe(words[language]['legalLinks.name']);
		const anchor = page.querySelector('a')!;
		expect(anchor.hasAttribute('target')).toBe(false);
		expect(anchor.hasAttribute('rel')).toBe(false);
	});

	it.each<Language>(['en', 'de'])('is named in the %s words in a menu and opens links in a new tab', async (language) => {
		const page = await render([{ label: 'Imprint', href: '/imprint' }], { place: 'menu' }, language);
		expect(page.querySelector('nav')?.getAttribute('aria-label')).toBe(words[language]['legalLinks.name']);
		const anchor = page.querySelector('a')!;
		expect(anchor.getAttribute('target')).toBe('_blank');
		expect(anchor.getAttribute('rel')).toBe('noopener');
	});

	it('opens every link of a page in a new tab with newTab and keeps the page look', async () => {
		const page = await render(
			[
				{ label: 'Imprint', href: '/imprint' },
				{ label: 'Privacy', href: '/privacy' }
			],
			{ newTab: true }
		);
		const anchors = [...page.querySelectorAll('a')];
		expect(anchors).toHaveLength(2);
		for (const anchor of anchors) {
			expect(anchor.getAttribute('target')).toBe('_blank');
			expect(anchor.getAttribute('rel')).toBe('noopener');
		}
		const menu = await render([{ label: 'Imprint', href: '/imprint' }], { place: 'menu' });
		expect(page.querySelector('nav')?.className).not.toBe(menu.querySelector('nav')?.className);
	});

	it('opens links of a page in the same tab with newTab false', async () => {
		const page = await render([{ label: 'Imprint', href: '/imprint' }], { newTab: false });
		const anchor = page.querySelector('a')!;
		expect(anchor.hasAttribute('target')).toBe(false);
		expect(anchor.hasAttribute('rel')).toBe(false);
	});
});
