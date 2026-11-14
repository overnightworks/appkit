import { render } from 'svelte/server';
import { describe, expect, it } from 'vitest';
import TurnState from './TurnState.svelte';
import { loadWords, type Language } from './words/index.ts';

const languages: Language[] = ['en', 'de'];

describe.each(languages)('TurnState server-rendered in the %s words', (language) => {
	it('renders no markup without an outcome', async () => {
		const { body } = render(TurnState, { props: { outcome: undefined, words: await loadWords(language) } });
		expect(body).not.toContain('turn-state');
	});

	it('renders the word and a hidden mark without a script', async () => {
		const words = await loadWords(language);
		const { body } = render(TurnState, { props: { outcome: 'budget_spent', words } });
		expect(body).toMatch(/class="turn-state\b/);
		expect(body).toContain(words['turnState.budgetSpent']);
		expect(body).toMatch(/<svg\b[^>]*aria-hidden="true"/);
		expect(body).not.toMatch(/<script\b/);
	});
});
