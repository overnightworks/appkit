import { render } from 'svelte/server';
import { describe, expect, it } from 'vitest';
import AgentControl from './AgentControl.svelte';
import { loadWords, type Language } from './words/index.ts';

const languages: Language[] = ['en', 'de'];

describe.each(languages)('AgentControl server-rendered in the %s words', (language) => {
	it('renders the rows and their buttons without a script', async () => {
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
		expect(body).toContain(words['agent.call']);
		expect(body).toContain(words['agent.askToLeave']);
		expect(body).not.toMatch(/<script\b/);
	});

	it('renders the stated turn outcome of a here row beside its name without a script', async () => {
		const words = await loadWords(language);
		const { body } = render(AgentControl, {
			props: {
				rows: [{ key: 'k1', name: 'Mozart', state: 'here', turnState: 'unavailable' }],
				onCall: () => {},
				words
			}
		});
		expect(body).toContain(words['turnState.unavailable']);
		expect(body).not.toMatch(/<script\b/);
	});

	it.each([
		['no-answer', 'agent.noAnswer'],
		['busy', 'agent.busy'],
		['owner-absent', 'agent.ownerAbsent']
	] as const)('renders the %s outcome of an ended row as a status without a script', async (outcome, key) => {
		const words = await loadWords(language);
		const { body } = render(AgentControl, {
			props: {
				rows: [{ key: 'k1', name: 'Mozart', state: 'ended', outcome }],
				onCall: () => {},
				onSendAway: () => {},
				words
			}
		});
		expect(body).toMatch(new RegExp(`role="status"[^>]*>.*${words[key]}`, 's'));
		expect(body).not.toMatch(/<script\b|<button\b/);
	});

	it.each([
		['not-allowed', 'agent.notAllowed'],
		['owner-absent', 'agent.ownerAbsent'],
		['place-full', 'agent.placeFull'],
		['agent-unavailable', 'agent.agentUnavailable'],
		['try-again', 'agent.tryAgain']
	] as const)('renders the %s refusal as an alert without a script', async (refusal, key) => {
		const words = await loadWords(language);
		const { body } = render(AgentControl, {
			props: { rows: [], onCall: () => {}, onSendAway: () => {}, refusal, words }
		});
		expect(body).toMatch(new RegExp(`role="alert"[^>]*>.*${words[key]}`, 's'));
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

	it('renders the place-full sentence in place of the empty sentence when full is set', async () => {
		const words = await loadWords(language);
		const { body } = render(AgentControl, {
			props: { rows: [], full: true, onCall: () => {}, onSendAway: () => {}, words }
		});
		expect(body).toContain(words['agent.placeFull']);
		expect(body).not.toContain(words['agent.empty']);
	});
});
