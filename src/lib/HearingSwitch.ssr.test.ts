import { render } from 'svelte/server';
import { describe, expect, it } from 'vitest';
import HearingSwitch from './HearingSwitch.svelte';
import type { HearingKind } from './types.ts';
import { loadWords, type Language } from './words/index.ts';

const languages: Language[] = ['en', 'de'];

describe.each(languages)('HearingSwitch server-rendered in the %s words', (language) => {
	it.each<[HearingKind, 'hearing.agentMayHearMe' | 'hearing.iWantToHearAgent' | 'hearing.seeShort']>([
		['hear', 'hearing.agentMayHearMe'],
		['listen', 'hearing.iWantToHearAgent'],
		['see', 'hearing.seeShort']
	])('renders the %s switch with its label and state without a script', async (kind, key) => {
		const words = await loadWords(language);
		const { body } = render(HearingSwitch, { props: { kind, on: true, onChange: () => {}, words } });
		expect(body).toMatch(/<button\b[^>]*role="switch"[^>]*>/);
		expect(body).toMatch(/<button\b[^>]*aria-checked="true"[^>]*>/);
		expect(body).toContain(words[key]);
		expect(body).not.toMatch(/<script\b/);
	});

	it('renders the see switch with the full words as its name', async () => {
		const words = await loadWords(language);
		const { body } = render(HearingSwitch, { props: { kind: 'see', on: true, onChange: () => {}, words } });
		expect(body).toMatch(new RegExp(`<button\\b[^>]*aria-label="${words['hearing.agentMaySeeMe']}"`));
	});

	it.each<[HearingKind]>([['hear'], ['listen'], ['see']])('renders the compact %s switch', async (kind) => {
		const words = await loadWords(language);
		const { body } = render(HearingSwitch, { props: { kind, on: true, onChange: () => {}, words, compact: true } });
		expect(body).toMatch(/<button\b[^>]*class="[^"]*\bcompact\b/);
	});

	it('renders aria-checked false for an off switch', async () => {
		const words = await loadWords(language);
		const { body } = render(HearingSwitch, { props: { kind: 'hear', on: false, onChange: () => {}, words } });
		expect(body).toMatch(/<button\b[^>]*aria-checked="false"[^>]*>/);
	});
});
