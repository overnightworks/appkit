import { mount, tick, unmount } from 'svelte';
import { SvelteMap } from 'svelte/reactivity';
import { afterEach, describe, expect, it, vi } from 'vitest';
import AgentControl, { outcomeMilliseconds } from './AgentControl.svelte';
import type { AgentControlOutcome, AgentControlProps, AgentControlRefusal } from './types.ts';
import { loadWords } from './words/index.ts';

const en = await loadWords('en');
const de = await loadWords('de');

const mounted: { target: HTMLElement; component: ReturnType<typeof mount> }[] = [];

function baseProps(overrides: Partial<AgentControlProps> = {}): AgentControlProps {
	return { rows: [], onCall: () => {}, onSendAway: () => {}, words: en, ...overrides };
}

async function render(overrides: Partial<AgentControlProps> = {}): Promise<HTMLElement> {
	const target = document.createElement('div');
	document.body.append(target);
	mounted.push({ target, component: mount(AgentControl, { target, props: baseProps(overrides) }) });
	await tick();
	return target;
}

afterEach(async () => {
	vi.useRealTimers();
	for (const { target, component } of mounted.splice(0)) {
		await unmount(component);
		target.remove();
	}
});

const rowsOf = (control: HTMLElement) => [...control.querySelectorAll('li')];
const buttonsOf = (control: HTMLElement) => [...control.querySelectorAll('button')];

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
		expect(buttons[0].textContent?.trim()).toBe(en['agent.call']);
		expect(buttons[0].getAttribute('aria-label')).toBe(en['agent.callLabel']({ name: 'Mozart' }));
		expect(buttons[0].type).toBe('button');
	});

	it('shows an inviting agent the waiting text announced as a status and no button', async () => {
		const control = await render({ rows: [{ key: 'k1', name: 'Mozart', state: 'inviting' }] });
		expect(buttonsOf(control)).toHaveLength(0);
		const status = control.querySelector('[role="status"]')!;
		expect(status.textContent?.trim()).toBe(en['agent.calling']);
	});

	it('offers an agent that is here one Ask to leave button named after the agent', async () => {
		const control = await render({ rows: [{ key: 'k1', name: 'Mozart', state: 'here' }] });
		const buttons = buttonsOf(control);
		expect(buttons).toHaveLength(1);
		expect(buttons[0].textContent?.trim()).toBe(en['agent.askToLeave']);
		expect(buttons[0].getAttribute('aria-label')).toBe(en['agent.askToLeaveLabel']({ name: 'Mozart' }));
	});

	it('shows a here row without the send-away handler as the mark and the name, with no action', async () => {
		const control = await render({ rows: [{ key: 'k1', name: 'Mozart', state: 'here' }], onSendAway: undefined });
		expect(buttonsOf(control)).toHaveLength(0);
		const row = rowsOf(control)[0];
		expect(row.firstElementChild?.textContent).toBe('AI');
		expect(row.children[1].textContent).toBe('Mozart');
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

describe('ended rows', () => {
	const outcomeWords: [AgentControlOutcome, keyof typeof en][] = [
		['no-answer', 'agent.noAnswer'],
		['busy', 'agent.busy'],
		['owner-absent', 'agent.ownerAbsent']
	];
	const ended = (outcome: AgentControlOutcome): AgentControlProps['rows'][number] => ({
		key: 'k1',
		name: 'Mozart',
		state: 'ended',
		outcome
	});
	const statusOf = (control: HTMLElement) => control.querySelector('[role="status"]');

	async function renderWithTimers(overrides: Partial<AgentControlProps>) {
		vi.useFakeTimers();
		return render(overrides);
	}

	async function renderChangingRows(initial: AgentControlProps['rows']) {
		vi.useFakeTimers();
		const state = new SvelteMap([['rows', initial]]);
		const target = document.createElement('div');
		document.body.append(target);
		const props = {
			...baseProps(),
			get rows() {
				return state.get('rows')!;
			}
		};
		mounted.push({ target, component: mount(AgentControl, { target, props }) });
		await tick();
		return {
			control: target,
			setRows: async (rows: AgentControlProps['rows']) => {
				state.set('rows', rows);
				await tick();
			}
		};
	}

	it.each(outcomeWords)(
		'shows the %s outcome as a muted status with an icon and no key',
		async (outcome, key) => {
			const control = await render({ rows: [ended(outcome)] });
			expect(buttonsOf(control)).toHaveLength(0);
			const status = statusOf(control)!;
			expect(status.textContent?.trim()).toBe(en[key]);
			expect(status.querySelector('svg[aria-hidden="true"]')).not.toBeNull();
			expect(status.querySelector('.dots')).toBeNull();
		}
	);

	it.each(outcomeWords)('shows the %s outcome in the words of the page language', async (outcome, key) => {
		const control = await render({ rows: [ended(outcome)], words: de });
		expect(statusOf(control)?.textContent?.trim()).toBe(de[key]);
	});

	it('draws the row like an available row once the duration has passed', async () => {
		const onCall = vi.fn();
		const control = await renderWithTimers({ rows: [ended('busy')], onCall });
		await vi.advanceTimersByTimeAsync(outcomeMilliseconds - 1);
		expect(statusOf(control)).not.toBeNull();
		await vi.advanceTimersByTimeAsync(1);
		expect(statusOf(control)).toBeNull();
		const buttons = buttonsOf(control);
		expect(buttons).toHaveLength(1);
		expect(buttons[0].textContent?.trim()).toBe(en['agent.call']);
		expect(buttons[0].getAttribute('aria-label')).toBe(en['agent.callLabel']({ name: 'Mozart' }));
		buttons[0].click();
		expect(onCall).toHaveBeenCalledExactlyOnceWith('k1');
	});

	it('keeps the row callable until the app changes it', async () => {
		const control = await renderWithTimers({ rows: [ended('no-answer')] });
		await vi.advanceTimersByTimeAsync(outcomeMilliseconds * 5);
		expect(buttonsOf(control)).toHaveLength(1);
		expect(statusOf(control)).toBeNull();
	});

	it('restarts the duration when the app passes a new ended state for the row', async () => {
		const { control, setRows } = await renderChangingRows([ended('no-answer')]);
		await vi.advanceTimersByTimeAsync(outcomeMilliseconds - 1);
		await setRows([{ key: 'k1', name: 'Mozart', state: 'inviting' }]);
		await setRows([ended('busy')]);
		await vi.advanceTimersByTimeAsync(outcomeMilliseconds - 1);
		expect(statusOf(control)?.textContent?.trim()).toBe(en['agent.busy']);
		await vi.advanceTimersByTimeAsync(1);
		expect(statusOf(control)).toBeNull();
	});

	it('restarts the duration when the outcome of an ended row changes', async () => {
		const { control, setRows } = await renderChangingRows([ended('no-answer')]);
		await vi.advanceTimersByTimeAsync(outcomeMilliseconds - 1);
		await setRows([ended('busy')]);
		await vi.advanceTimersByTimeAsync(outcomeMilliseconds - 1);
		expect(statusOf(control)?.textContent?.trim()).toBe(en['agent.busy']);
	});

	it('shows the outcome again when the app ends the call anew after the row lapsed', async () => {
		const { control, setRows } = await renderChangingRows([ended('no-answer')]);
		await vi.advanceTimersByTimeAsync(outcomeMilliseconds);
		expect(statusOf(control)).toBeNull();
		await setRows([{ key: 'k1', name: 'Mozart', state: 'inviting' }]);
		await setRows([ended('no-answer')]);
		expect(statusOf(control)?.textContent?.trim()).toBe(en['agent.noAnswer']);
	});

	it('leaves other rows and their timers untouched', async () => {
		const { control, setRows } = await renderChangingRows([
			ended('no-answer'),
			{ key: 'k2', name: 'Bach', state: 'inviting' }
		]);
		await vi.advanceTimersByTimeAsync(outcomeMilliseconds - 1);
		await setRows([ended('no-answer'), { key: 'k2', name: 'Bach', state: 'here' }]);
		await vi.advanceTimersByTimeAsync(1);
		expect(rowsOf(control).map((row) => row.lastElementChild?.textContent?.trim())).toEqual([
			en['agent.call'],
			en['agent.askToLeave']
		]);
	});

	it('does not restart the duration when the app passes the same ended row again', async () => {
		const { control, setRows } = await renderChangingRows([ended('busy')]);
		await vi.advanceTimersByTimeAsync(outcomeMilliseconds - 1);
		await setRows([ended('busy')]);
		await vi.advanceTimersByTimeAsync(1);
		expect(statusOf(control)).toBeNull();
	});

	it('clears its timer when the row changes or the control unmounts', async () => {
		const { setRows } = await renderChangingRows([ended('busy')]);
		expect(vi.getTimerCount()).toBe(1);
		await setRows([{ key: 'k1', name: 'Mozart', state: 'here' }]);
		expect(vi.getTimerCount()).toBe(0);
		await setRows([ended('busy')]);
		expect(vi.getTimerCount()).toBe(1);
		for (const { target, component } of mounted.splice(0)) {
			await unmount(component);
			target.remove();
		}
		expect(vi.getTimerCount()).toBe(0);
	});
});

describe('refusal', () => {
	const rows: AgentControlProps['rows'] = [{ key: 'k1', name: 'Mozart', state: 'available' }];

	it('draws no alert while no refusal is set', async () => {
		const control = await render({ rows });
		expect(control.querySelector('[role="alert"]')).toBeNull();
	});

	it.each<[AgentControlRefusal, keyof typeof en]>([
		['not-allowed', 'agent.notAllowed'],
		['owner-absent', 'agent.ownerAbsent'],
		['place-full', 'agent.placeFull'],
		['agent-unavailable', 'agent.agentUnavailable'],
		['try-again', 'agent.tryAgain']
	])('draws the %s sentence as an alert above the rows', async (refusal, key) => {
		const control = await render({ rows, refusal });
		const alert = control.querySelector('[role="alert"]')!;
		expect(alert.textContent?.trim()).toBe(en[key]);
		const list = control.querySelector('ul')!;
		expect(alert.compareDocumentPosition(list) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
	});

	it('leaves the rows and their buttons in place under a refusal', async () => {
		const control = await render({ rows, refusal: 'place-full' });
		expect(buttonsOf(control)).toHaveLength(1);
	});
});

describe('empty face', () => {
	it('draws only the empty sentence when there are no rows', async () => {
		const control = await render({ rows: [] });
		expect(control.textContent?.trim()).toBe(en['agent.empty']);
		expect(control.querySelector('ul, li, button, [role="alert"]')).toBeNull();
	});

	it('draws the empty sentence and the refusal when both apply', async () => {
		const control = await render({ rows: [], refusal: 'agent-unavailable' });
		expect(control.querySelector('[role="alert"]')?.textContent?.trim()).toBe(
			en['agent.agentUnavailable']
		);
		expect(control.textContent).toContain(en['agent.empty']);
		expect(control.querySelector('ul, li, button')).toBeNull();
	});

	it('draws the place-full sentence instead of the empty sentence when full is set', async () => {
		const control = await render({ rows: [], full: true });
		expect(control.textContent?.trim()).toBe(en['agent.placeFull']);
		expect(control.textContent).not.toContain(en['agent.empty']);
	});

	it('draws the empty sentence when full is unset or false', async () => {
		const control = await render({ rows: [], full: false });
		expect(control.textContent?.trim()).toBe(en['agent.empty']);
	});

	it('draws no empty sentence while rows exist', async () => {
		const control = await render({ rows: [{ key: 'k1', name: 'Mozart', state: 'here' }] });
		expect(control.textContent).not.toContain(en['agent.empty']);
	});
});

describe('words', () => {
	it('draws every word of the de words: the ruled list, the names and none of the en words', async () => {
		const control = await render({
			rows: [
				{ key: 'k1', name: 'Mozart', state: 'available' },
				{ key: 'k2', name: 'Bach', state: 'inviting' },
				{ key: 'k3', name: 'Leonardo', state: 'here' }
			],
			words: de
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

	it('draws the empty sentence of the de words', async () => {
		const control = await render({ rows: [], words: de });
		expect(control.textContent?.trim()).toBe('Gerade ist kein Agent erreichbar.');
	});

	it.each<[AgentControlRefusal, string]>([
		['not-allowed', 'Du darfst diesen Agenten nicht rufen.'],
		['owner-absent', 'Sein Besitzer ist nicht hier.'],
		['place-full', 'Hier ist kein Platz für einen weiteren Agenten.'],
		['agent-unavailable', 'Der Agent ist gerade nicht erreichbar.'],
		['try-again', 'Das hat nicht geklappt. Versuch es noch einmal.']
	])('draws the %s sentence of the de words as an alert', async (refusal, sentence) => {
		const control = await render({ rows: [], refusal, words: de });
		expect(control.querySelector('[role="alert"]')?.textContent?.trim()).toBe(sentence);
	});
});

describe('en words', () => {
	it('renders the en texts of every row state and the empty sentence', async () => {
		const control = await render({
			rows: [
				{ key: 'k1', name: 'Mozart', state: 'available' },
				{ key: 'k2', name: 'Bach', state: 'inviting' },
				{ key: 'k3', name: 'Leonardo', state: 'here' }
			]
		});
		expect(rowsOf(control).map((row) => row.lastElementChild?.textContent?.trim())).toEqual([
			'Call',
			'Calling…',
			'Ask to leave'
		]);
		expect(buttonsOf(control).map((button) => button.getAttribute('aria-label'))).toEqual([
			'Call Mozart',
			'Ask Leonardo to leave'
		]);
		expect((await render({ rows: [] })).textContent?.trim()).toBe('No agent is reachable right now.');
	});

	it.each<[AgentControlRefusal, string]>([
		['not-allowed', 'You may not call this agent.'],
		['owner-absent', 'Its owner is not here.'],
		['place-full', 'There is no room here for another agent.'],
		['agent-unavailable', 'The agent is not reachable right now.'],
		['try-again', 'That did not work. Please try again.']
	])('renders the %s refusal in the en words', async (refusal, sentence) => {
		const control = await render({ rows: [], refusal });
		expect(control.querySelector('[role="alert"]')?.textContent?.trim()).toBe(sentence);
	});
});
