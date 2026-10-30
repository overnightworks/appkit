import { mount, tick, unmount } from 'svelte';
import { afterEach, describe, expect, it } from 'vitest';
import LegalLinks from './LegalLinks.svelte';
import type { LegalLink } from './types.ts';

const mounted: { target: HTMLElement; component: ReturnType<typeof mount> }[] = [];

async function render(links: readonly LegalLink[]): Promise<HTMLElement> {
	const target = document.createElement('div');
	document.body.append(target);
	mounted.push({ target, component: mount(LegalLinks, { target, props: { links } }) });
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
});
