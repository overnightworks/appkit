import { render } from 'svelte/server';
import { describe, expect, it } from 'vitest';
import AgentControl from './AgentControl.svelte';
import { loadWords, type Language } from './words/index.ts';

const languages: Language[] = ['en', 'de'];

describe.each(languages)('AgentControl server-rendered in the %s words', (language) => {
	it('renders the rows, their buttons and a refusal without a script', async () => {
		const words = await loadWords(language);
		const { body } = render(AgentControl, {
			props: {
				rows: [
					{ key: 'k1', name: 'Mozart', state: 'available' },
					{ key: 'k2', name: 'Bach', state: 'inviting' },
					{ key: 'k3', name: 'Leonardo', state: 'here' }
				],
				onCall: () => {},
				onSendAway: () => {},
				refusal: 'try-again',
				words
			}
		});
		expect(body).toMatch(
			new RegExp(`<button\\b[^>]*aria-label="${words['agent.callLabel']({ name: 'Mozart' })}"[^>]*>`)
		);
		expect(body).toMatch(
			new RegExp(`<button\\b[^>]*aria-label="${words['agent.askToLeaveLabel']({ name: 'Leonardo' })}"[^>]*>`)
		);
		expect(body).toMatch(new RegExp(`role="status"[^>]*>.*${words['agent.calling']}`, 's'));
		expect(body).toMatch(new RegExp(`role="alert"[^>]*>.*${words['agent.tryAgain']}`, 's'));
		expect(body).toContain(words['agent.call']);
		expect(body).toContain(words['agent.askToLeave']);
		expect(body).not.toMatch(/<script\b/);
	});

	it('renders only the empty sentence when there are no rows', async () => {
		const words = await loadWords(language);
		const { body } = render(AgentControl, {
			props: { rows: [], onCall: () => {}, onSendAway: () => {}, words }
		});
		expect(body).toContain(words['agent.empty']);
		expect(body).not.toMatch(/<ul\b|<li\b|<button\b|role="alert"/);
	});
});
