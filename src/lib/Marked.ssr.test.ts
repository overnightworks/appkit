import { render } from 'svelte/server';
import { describe, expect, it } from 'vitest';
import Page, { type sentences } from './Marked.test.svelte';

type Parts = (typeof sentences)[number]['parts'];
const markup = (parts: Parts) => render(Page, { props: { parts } }).body;
function withoutAnchors(body: string): string {
	let rest = body;
	for (let start = rest.indexOf('<!--'); start !== -1; start = rest.indexOf('<!--')) {
		rest = rest.slice(0, start) + rest.slice(rest.indexOf('-->', start) + 3);
	}
	return rest;
}

describe('Marked server-rendered', () => {
	it.each([
		{
			case: 'writes the parts in order without a wrapper element or a space of its own',
			parts: ['Nur ', { marker: 'strong', text: 'wichtig' }, ' und ', { marker: 'link', text: 'mehr' }],
			expected: '<p>Nur <strong>wichtig</strong> und <a href="/more">mehr</a></p>'
		},
		{
			case: 'writes every occurrence of a marker that two parts share',
			parts: ['a ', { marker: 'strong', text: 'x' }, ' b ', { marker: 'strong', text: 'y' }],
			expected: '<p>a <strong>x</strong> b <strong>y</strong></p>'
		}
	] satisfies { case: string; parts: Parts; expected: string }[])('$case', ({ parts, expected }) => {
		expect(withoutAnchors(markup(parts))).toBe(expected);
	});

	it('escapes the text of a marked part', () => {
		const body = markup([{ marker: 'strong', text: '<b>{#x}</b>' }]);
		expect(withoutAnchors(body)).toContain('<strong>&lt;b>{#x}&lt;/b></strong>');
	});
});
