import { mount, tick, unmount } from 'svelte';
import { afterEach, describe, expect, it, vi } from 'vitest';
import AgentControl from './AgentControl.svelte';
import type { AgentControlProps, AgentControlRefusal, AgentControlWords } from './types.ts';

const mounted: { target: HTMLElement; component: ReturnType<typeof mount> }[] = [];

function baseProps(overrides: Partial<AgentControlProps> = {}): AgentControlProps {
	return { rows: [], onCall: () => {}, onSendAway: () => {}, ...overrides };
}

async function render(overrides: Partial<AgentControlProps> = {}): Promise<HTMLElement> {
	const target = document.createElement('div');
	document.body.append(target);
	mounted.push({ target, component: mount(AgentControl, { target, props: baseProps(overrides) }) });
	await tick();
	return target;
}

afterEach(async () => {
	for (const { target, component } of mounted.splice(0)) {
		await unmount(component);
		target.remove();
	}
});

const rowsOf = (control: HTMLElement) => [...control.querySelectorAll('li')];
const buttonsOf = (control: HTMLElement) => [...control.querySelectorAll('button')];

const german: AgentControlWords = {
	call: 'Rufen',
	calling: 'Wird gerufen…',
	askToLeave: 'Bitten zu gehen',
	callLabel: (name) => `${name} rufen`,
	askToLeaveLabel: (name) => `${name} bitten zu gehen`,
	empty: 'Gerade ist kein Agent erreichbar.',
	refusals: {
		'not-allowed': 'Du darfst diesen Agenten nicht rufen.',
		'owner-absent': 'Sein Besitzer ist nicht hier.',
		'place-full': 'Hier ist kein Platz für einen weiteren Agenten.',
		'agent-unavailable': 'Der Agent ist gerade nicht erreichbar.',
		'try-again': 'Das hat nicht geklappt. Versuch es noch einmal.'
	}
};

describe('rows', () => {
	it('leads every row with the AI mark and shows the name as given', async () => {
		const control = await render({
			rows: [
				{ key: 'k1', name: 'mozart', state: 'available' },
				{ key: 'k2', name: 'Leonardo da Vinci', state: 'here' }
			]
		});
		const rows = rowsOf(control);
		expect(rows).toHaveLength(2);
		expect(rows.map((row) => row.firstElementChild?.textContent)).toEqual(['AI', 'AI']);
		expect(rows.map((row) => row.children[1].textContent)).toEqual(['mozart', 'Leonardo da Vinci']);
	});

	it('offers an available agent one Call button named after the agent', async () => {
		const control = await render({ rows: [{ key: 'k1', name: 'Mozart', state: 'available' }] });
		const buttons = buttonsOf(control);
		expect(buttons).toHaveLength(1);
		expect(buttons[0].textContent?.trim()).toBe('Call');
		expect(buttons[0].getAttribute('aria-label')).toBe('Call Mozart');
		expect(buttons[0].type).toBe('button');
	});

	it('shows an inviting agent the waiting text announced as a status and no button', async () => {
		const control = await render({ rows: [{ key: 'k1', name: 'Mozart', state: 'inviting' }] });
		expect(buttonsOf(control)).toHaveLength(0);
		const status = control.querySelector('[role="status"]')!;
		expect(status.textContent?.trim()).toBe('Calling…');
	});

	it('offers an agent that is here one Ask to leave button named after the agent', async () => {
		const control = await render({ rows: [{ key: 'k1', name: 'Mozart', state: 'here' }] });
		const buttons = buttonsOf(control);
		expect(buttons).toHaveLength(1);
		expect(buttons[0].textContent?.trim()).toBe('Ask to leave');
		expect(buttons[0].getAttribute('aria-label')).toBe('Ask Mozart to leave');
	});

	it('shows the rows in the given order', async () => {
		const control = await render({
			rows: [
				{ key: 'b', name: 'B', state: 'here' },
				{ key: 'a', name: 'A', state: 'available' }
			]
		});
		expect(rowsOf(control).map((row) => row.children[1].textContent)).toEqual(['B', 'A']);
	});
});

describe('actions', () => {
	const rows: AgentControlProps['rows'] = [
		{ key: 'key-1', name: 'Mozart', state: 'available' },
		{ key: 'key-2', name: 'Leonardo', state: 'here' },
		{ key: 'key-3', name: 'Bach', state: 'inviting' }
	];

	it('calls onCall with the key of an available row and nothing else', async () => {
		const onCall = vi.fn();
		const onSendAway = vi.fn();
		const control = await render({ rows, onCall, onSendAway });
		buttonsOf(control)[0].click();
		expect(onCall).toHaveBeenCalledExactlyOnceWith('key-1');
		expect(onSendAway).not.toHaveBeenCalled();
	});

	it('calls onSendAway with the key of a here row at once, with no confirm step', async () => {
		const onCall = vi.fn();
		const onSendAway = vi.fn();
		const control = await render({ rows, onCall, onSendAway });
		buttonsOf(control)[1].click();
		expect(onSendAway).toHaveBeenCalledExactlyOnceWith('key-2');
		expect(onCall).not.toHaveBeenCalled();
		expect(control.querySelector('[role="dialog"], [role="alertdialog"]')).toBeNull();
	});
});

describe('refusal', () => {
	const rows: AgentControlProps['rows'] = [{ key: 'k1', name: 'Mozart', state: 'available' }];

	it('draws no alert while no refusal is set', async () => {
		const control = await render({ rows });
		expect(control.querySelector('[role="alert"]')).toBeNull();
	});

	it.each<[AgentControlRefusal, string]>([
		['not-allowed', 'You may not call this agent.'],
		['owner-absent', 'Its owner is not here.'],
		['place-full', 'There is no room here for another agent.'],
		['agent-unavailable', 'The agent is not reachable right now.'],
		['try-again', 'That did not work. Please try again.']
	])('draws the %s sentence as an alert above the rows', async (refusal, sentence) => {
		const control = await render({ rows, refusal });
		const alert = control.querySelector('[role="alert"]')!;
		expect(alert.textContent?.trim()).toBe(sentence);
		const list = control.querySelector('ul')!;
		expect(alert.compareDocumentPosition(list) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
	});

	it('leaves the rows and their buttons in place under a refusal', async () => {
		const control = await render({ rows, refusal: 'place-full' });
		expect(buttonsOf(control)).toHaveLength(1);
	});

	it('draws the refusal sentence from the given words', async () => {
		const control = await render({ rows, refusal: 'owner-absent', words: german });
		expect(control.querySelector('[role="alert"]')?.textContent?.trim()).toBe('Sein Besitzer ist nicht hier.');
	});
});

describe('empty face', () => {
	it('draws only the empty sentence when there are no rows', async () => {
		const control = await render({ rows: [] });
		expect(control.textContent?.trim()).toBe('No agent is reachable right now.');
		expect(control.querySelector('ul, li, button, [role="alert"]')).toBeNull();
	});

	it('draws the empty sentence and the refusal when both apply', async () => {
		const control = await render({ rows: [], refusal: 'agent-unavailable' });
		expect(control.querySelector('[role="alert"]')?.textContent?.trim()).toBe(
			'The agent is not reachable right now.'
		);
		expect(control.textContent).toContain('No agent is reachable right now.');
		expect(control.querySelector('ul, li, button')).toBeNull();
	});

	it('draws no empty sentence while rows exist', async () => {
		const control = await render({ rows: [{ key: 'k1', name: 'Mozart', state: 'here' }] });
		expect(control.textContent).not.toContain('No agent is reachable');
	});
});

describe('words', () => {
	it('draws every word of the given language and none of the en defaults', async () => {
		const control = await render({
			rows: [
				{ key: 'k1', name: 'Mozart', state: 'available' },
				{ key: 'k2', name: 'Bach', state: 'inviting' },
				{ key: 'k3', name: 'Leonardo', state: 'here' }
			],
			words: german
		});
		expect(rowsOf(control).map((row) => row.lastElementChild?.textContent?.trim())).toEqual([
			'Rufen',
			'Wird gerufen…',
			'Bitten zu gehen'
		]);
		expect(buttonsOf(control).map((button) => button.getAttribute('aria-label'))).toEqual([
			'Mozart rufen',
			'Leonardo bitten zu gehen'
		]);
		expect(control.textContent).not.toMatch(/Call|Ask to leave/);
	});

	it('draws the empty sentence from the given words', async () => {
		const control = await render({ rows: [], words: german });
		expect(control.textContent?.trim()).toBe('Gerade ist kein Agent erreichbar.');
	});
});
