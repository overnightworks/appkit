import { render } from 'svelte/server';
import { describe, expect, it } from 'vitest';
import EarMark from './EarMark.svelte';
import { loadWords, type Language } from './words/index.ts';

const languages: Language[] = ['en', 'de'];

describe.each(languages)('EarMark server-rendered in the %s words', (language) => {
	it('renders the image with its name, title and pill on one own tile without a script', async () => {
		const words = await loadWords(language);
		const { body } = render(EarMark, { props: { agent: 'Mozart', words } });
		const name = words['hearing.agentHearsYou']({ agent: 'Mozart' });
		expect(body).toMatch(/role="img"/);
		expect(body).toContain(`aria-label="${name}"`);
		expect(body).toContain(`title="${name}"`);
		expect(body).toContain('>Mozart<');
		expect(body).not.toMatch(/<script\b/);
	});

	it('renders the name of the other person on another tile', async () => {
		const words = await loadWords(language);
		const { body } = render(EarMark, { props: { agent: 'Mozart', person: 'Anna', words } });
		expect(body).toContain(`aria-label="${words['hearing.agentHearsPerson']({ agent: 'Mozart', name: 'Anna' })}"`);
	});
});
