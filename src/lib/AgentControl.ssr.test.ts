import { render } from 'svelte/server';
import { describe, expect, it } from 'vitest';
import AgentControl from './AgentControl.svelte';

describe('AgentControl server-rendered', () => {
	it('renders the rows, their buttons and a refusal without a script', () => {
		const { body } = render(AgentControl, {
			props: {
				rows: [
					{ key: 'k1', name: 'Mozart', state: 'available' },
					{ key: 'k2', name: 'Bach', state: 'inviting' },
					{ key: 'k3', name: 'Leonardo', state: 'here' }
				],
				onCall: () => {},
				onSendAway: () => {},
				refusal: 'try-again'
			}
		});
		expect(body).toMatch(/<button\b[^>]*aria-label="Call Mozart"[^>]*>/);
		expect(body).toMatch(/<button\b[^>]*aria-label="Ask Leonardo to leave"[^>]*>/);
		expect(body).toMatch(/role="status"[^>]*>.*Calling…/s);
		expect(body).toMatch(/role="alert"[^>]*>.*That did not work\. Please try again\./s);
		expect(body).not.toMatch(/<script\b/);
	});

	it('renders only the empty sentence when there are no rows', () => {
		const { body } = render(AgentControl, {
			props: { rows: [], onCall: () => {}, onSendAway: () => {} }
		});
		expect(body).toContain('No agent is reachable right now.');
		expect(body).not.toMatch(/<ul\b|<li\b|<button\b|role="alert"/);
	});
});
