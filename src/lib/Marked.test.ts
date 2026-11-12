import { mount, tick, unmount } from 'svelte';
import { afterEach, describe, expect, it } from 'vitest';
import Page, { sentences } from './Marked.test.svelte';

const mounted: { target: HTMLElement; component: ReturnType<typeof mount> }[] = [];

async function render(parts: (typeof sentences)[number]['parts']): Promise<HTMLElement> {
	const target = document.createElement('div');
	document.body.append(target);
	mounted.push({ target, component: mount(Page, { target, props: { parts } }) });
	await tick();
	return target.querySelector('p')!;
}

afterEach(async () => {
	for (const { target, component } of mounted.splice(0)) {
		await unmount(component);
		target.remove();
	}
});

describe('Marked', () => {
	it.each(sentences)('reads as the sentence and puts each marked part in its snippet’s element (%#)', async ({
		parts,
		text,
		elements
	}) => {
		const sentence = await render(parts);
		expect(sentence.textContent).toBe(text);
		expect(
			[...sentence.children].map((child) => `${child.tagName.toLowerCase()}:${child.textContent}`)
		).toEqual(elements);
	});

	it('adds no wrapper element and no markup of its own around the parts', async () => {
		const sentence = await render(['Nur ', { marker: 'strong', text: 'wichtig' }]);
		expect(sentence.innerHTML.replace(/<!--.*?-->/g, '')).toBe('Nur <strong>wichtig</strong>');
	});

	it('gives a marked part the element its snippet chose, with that element’s attributes', async () => {
		const sentence = await render(['See ', { marker: 'link', text: 'more' }]);
		expect(sentence.querySelector('a')!.getAttribute('href')).toBe('/more');
	});
});
