import { mount, tick, unmount } from 'svelte';
import { afterEach, describe, expect, it } from 'vitest';
import EarMark from './EarMark.svelte';
import type { EarMarkProps } from './types.ts';
import { loadWords } from './words/index.ts';

const en = await loadWords('en');
const de = await loadWords('de');

const mounted: { target: HTMLElement; component: ReturnType<typeof mount> }[] = [];

function baseProps(overrides: Partial<EarMarkProps> = {}): EarMarkProps {
	return { agent: 'Mozart', words: en, ...overrides };
}

async function render(overrides: Partial<EarMarkProps> = {}): Promise<HTMLElement> {
	const target = document.createElement('div');
	document.body.append(target);
	mounted.push({ target, component: mount(EarMark, { target, props: baseProps(overrides) }) });
	await tick();
	return target.querySelector<HTMLElement>('[role="img"]')!;
}

afterEach(async () => {
	for (const { target, component } of mounted.splice(0)) {
		await unmount(component);
		target.remove();
	}
});

describe('the mark', () => {
	it('is one image, named and titled alike', async () => {
		const mark = await render();
		expect(mark.parentElement?.querySelectorAll('[role="img"]')).toHaveLength(1);
		expect(mark.getAttribute('aria-label')).toBe(mark.getAttribute('title'));
		expect(mark.hasAttribute('aria-labelledby')).toBe(false);
	});

	it('names the agent as hearing the person on their own tile', async () => {
		const mark = await render({ agent: 'Mozart' });
		expect(mark.getAttribute('aria-label')).toBe(en['hearing.agentHearsYou']({ agent: 'Mozart' }));
	});

	it('names the agent as hearing the other person on another tile', async () => {
		const mark = await render({ agent: 'Mozart', person: 'Anna' });
		expect(mark.getAttribute('aria-label')).toBe(en['hearing.agentHearsPerson']({ agent: 'Mozart', name: 'Anna' }));
	});

	it('shows the agent name as a pill and no other text', async () => {
		const mark = await render({ agent: 'Mozart', person: 'Anna' });
		expect(mark.textContent?.trim()).toBe('Mozart');
	});

	it('hides the ear drawing from assistive technology', async () => {
		const mark = await render();
		const drawings = mark.querySelectorAll('svg');
		expect(drawings).toHaveLength(1);
		expect(drawings[0].getAttribute('aria-hidden')).toBe('true');
	});

	it('gives each of two marks its own agent name', async () => {
		const first = await render({ agent: 'Mozart' });
		const second = await render({ agent: 'Bach' });
		expect(first.getAttribute('aria-label')).toContain('Mozart');
		expect(second.getAttribute('aria-label')).toContain('Bach');
	});
});

describe('words', () => {
	it.each<[string, Partial<EarMarkProps>, string]>([
		['on one tile of its own', {}, de['hearing.agentHearsYou']({ agent: 'Mozart' })],
		['on another person tile', { person: 'Anna' }, de['hearing.agentHearsPerson']({ agent: 'Mozart', name: 'Anna' })]
	])('names the mark with the de words %s', async (_scenario, overrides, expected) => {
		const mark = await render({ ...overrides, words: de });
		expect(mark.getAttribute('aria-label')).toBe(expected);
		expect(mark.getAttribute('title')).toBe(expected);
	});

	it('takes an agent name that holds a gap marker as plain text', async () => {
		const mark = await render({ agent: '{name}', person: 'Anna' });
		expect(mark.getAttribute('aria-label')).toBe(en['hearing.agentHearsPerson']({ agent: '{name}', name: 'Anna' }));
	});
});
