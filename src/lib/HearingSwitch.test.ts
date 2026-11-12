import { mount, tick, unmount } from 'svelte';
import { afterEach, describe, expect, it, vi } from 'vitest';
import HearingSwitch from './HearingSwitch.svelte';
import type { HearingKind, HearingSwitchProps } from './types.ts';
import { loadWords } from './words/index.ts';

const en = await loadWords('en');
const de = await loadWords('de');

const labelKeys = { hear: 'hearing.agentMayHearMe', listen: 'hearing.iWantToHearAgent' } as const satisfies Record<
	HearingKind,
	keyof typeof en
>;

const mounted: { target: HTMLElement; component: ReturnType<typeof mount> }[] = [];

function baseProps(overrides: Partial<HearingSwitchProps> = {}): HearingSwitchProps {
	return { kind: 'hear', on: true, onChange: () => {}, words: en, ...overrides };
}

async function render(overrides: Partial<HearingSwitchProps> = {}): Promise<HTMLButtonElement> {
	const target = document.createElement('div');
	document.body.append(target);
	mounted.push({ target, component: mount(HearingSwitch, { target, props: baseProps(overrides) }) });
	await tick();
	return target.querySelector('button')!;
}

afterEach(async () => {
	for (const { target, component } of mounted.splice(0)) {
		await unmount(component);
		target.remove();
	}
});

describe('the chip', () => {
	it.each<[HearingKind, boolean]>([
		['hear', true],
		['hear', false],
		['listen', true],
		['listen', false]
	])('is one switch button that shows %s as on=%s in aria-checked', async (kind, on) => {
		const chip = await render({ kind, on });
		expect(chip.parentElement?.querySelectorAll('button')).toHaveLength(1);
		expect(chip.type).toBe('button');
		expect(chip.getAttribute('role')).toBe('switch');
		expect(chip.getAttribute('aria-checked')).toBe(String(on));
	});

	it.each<[HearingKind]>([['hear'], ['listen']])('names the %s chip by its visible label', async (kind) => {
		const chip = await render({ kind });
		expect(chip.textContent?.trim()).toBe(en[labelKeys[kind]]);
		expect(chip.hasAttribute('aria-label')).toBe(false);
		expect(chip.hasAttribute('aria-labelledby')).toBe(false);
	});

	it('hides the icons and the track from assistive technology', async () => {
		const chip = await render();
		for (const svg of chip.querySelectorAll('svg')) expect(svg.getAttribute('aria-hidden')).toBe('true');
		const tracks = chip.querySelectorAll('span[aria-hidden="true"]');
		expect(tracks).toHaveLength(1);
		expect(tracks[0].textContent).toBe('');
		expect(chip.textContent?.trim()).toBe(en[labelKeys.hear]);
	});

	it.each<[HearingKind]>([['hear'], ['listen']])('draws the %s icon differently when off', async (kind) => {
		const on = await render({ kind, on: true });
		const off = await render({ kind, on: false });
		expect(on.querySelector('svg')).not.toBeNull();
		expect(on.querySelector('svg')!.innerHTML).not.toBe(off.querySelector('svg')!.innerHTML);
	});
});

describe('control', () => {
	it.each<[boolean]>([[true], [false]])('calls onChange with the negated value when on is %s', async (on) => {
		const onChange = vi.fn();
		const chip = await render({ on, onChange });
		chip.click();
		expect(onChange).toHaveBeenCalledExactlyOnceWith(!on);
	});

	it('keeps aria-checked at the prop after a press, until the app changes it', async () => {
		const chip = await render({ on: true });
		chip.click();
		await tick();
		expect(chip.getAttribute('aria-checked')).toBe('true');
	});
});

describe('words', () => {
	it.each<[HearingKind]>([['hear'], ['listen']])('names the %s chip with the de words', async (kind) => {
		const chip = await render({ kind, words: de });
		expect(chip.textContent?.trim()).toBe(de[labelKeys[kind]]);
	});
});
