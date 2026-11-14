import { mount, tick, unmount } from 'svelte';
import { afterEach, describe, expect, it } from 'vitest';
import TurnState from './TurnState.svelte';
import type { TurnOutcome } from './types.ts';
import { loadWords, type Language } from './words/index.ts';

const mounted: { target: HTMLElement; component: ReturnType<typeof mount> }[] = [];

async function render(outcome: TurnOutcome | undefined, language: Language = 'en'): Promise<HTMLElement> {
	const target = document.createElement('div');
	document.body.append(target);
	mounted.push({ target, component: mount(TurnState, { target, props: { outcome, words: await loadWords(language) } }) });
	await tick();
	return target;
}

afterEach(async () => {
	for (const { target, component } of mounted.splice(0)) {
		await unmount(component);
		target.remove();
	}
});

const wordKeys = [
	['not_enabled', 'turnState.notEnabled'],
	['busy', 'turnState.busy'],
	['budget_spent', 'turnState.budgetSpent'],
	['unavailable', 'turnState.unavailable']
] as const;

describe('TurnState', () => {
	it('renders nothing, not even a wrapper, without an outcome', async () => {
		const target = await render(undefined);
		expect(target.innerHTML).not.toContain('turn-state');
		expect(target.textContent).toBe('');
	});

	describe.each(['en', 'de'] as const)('in the %s words', (language) => {
		it.each(wordKeys)('shows the word of the %s outcome beside a decorative mark', async (outcome, key) => {
			const target = await render(outcome, language);
			const part = target.querySelector<HTMLElement>('.turn-state')!;
			expect(part.textContent).toBe((await loadWords(language))[key]);
			expect(part.querySelector('svg')!.getAttribute('aria-hidden')).toBe('true');
		});
	});

	it('is a standing state with no role and no live region', async () => {
		const part = (await render('busy')).querySelector<HTMLElement>('.turn-state')!;
		expect(part.hasAttribute('role')).toBe(false);
		expect(part.hasAttribute('aria-live')).toBe(false);
	});
});
