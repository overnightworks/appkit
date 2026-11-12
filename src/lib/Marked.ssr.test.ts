import { render } from 'svelte/server';
import { describe, expect, it } from 'vitest';
import Page, { type sentences } from './Marked.test.svelte';

const markup = (parts: (typeof sentences)[number]['parts']) => render(Page, { props: { parts } }).body;
const withoutAnchors = (body: string) => body.replace(/<!--.*?-->/g, '');

describe('Marked server-rendered', () => {
	it('writes the parts in order without a wrapper element or a space of its own', () => {
		const body = markup(['Nur ', { marker: 'strong', text: 'wichtig' }, ' und ', { marker: 'link', text: 'mehr' }]);
		expect(withoutAnchors(body)).toBe('<p>Nur <strong>wichtig</strong> und <a href="/more">mehr</a></p>');
	});

	it('escapes the text of a marked part', () => {
		const body = markup([{ marker: 'strong', text: '<b>{#x}</b>' }]);
		expect(withoutAnchors(body)).toContain('<strong>&lt;b>{#x}&lt;/b></strong>');
	});
});
