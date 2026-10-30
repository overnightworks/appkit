import { mount, tick, unmount } from 'svelte';
import { SvelteMap } from 'svelte/reactivity';
import { afterEach, describe, expect, it, vi } from 'vitest';
import AccountMenu from './AccountMenu.svelte';
import type { AccountMenuProps, ThemeChoice } from './types.ts';

const mounted: { target: HTMLElement; component: ReturnType<typeof mount> }[] = [];

function baseProps(overrides: Partial<AccountMenuProps> = {}): AccountMenuProps {
	return {
		name: 'Felix',
		accountHref: 'https://account.example/me',
		onAccountOpen: () => {},
		appRows: [],
		legalLinks: [],
		onLogOut: () => {},
		...overrides
	} as AccountMenuProps;
}

async function render(overrides: Partial<AccountMenuProps> = {}): Promise<HTMLElement> {
	const target = document.createElement('div');
	document.body.append(target);
	mounted.push({ target, component: mount(AccountMenu, { target, props: baseProps(overrides) }) });
	await tick();
	return target;
}

afterEach(async () => {
	for (const { target, component } of mounted.splice(0)) {
		await unmount(component);
		target.remove();
	}
});

function radios(menu: HTMLElement): HTMLInputElement[] {
	return [...menu.querySelectorAll<HTMLInputElement>('input[type="radio"]')];
}

function checkedLabel(menu: HTMLElement): string | undefined {
	return radios(menu).find((radio) => radio.checked)?.closest('label')?.textContent?.trim();
}

describe('name row', () => {
	it('links the name to the account in a new tab, reports the activation, and hides the icon', async () => {
		const onAccountOpen = vi.fn();
		const menu = await render({ onAccountOpen });
		const link = menu.querySelector<HTMLAnchorElement>('a[href="https://account.example/me"]')!;
		expect(link.textContent?.trim()).toBe('Felix');
		expect(link.getAttribute('target')).toBe('_blank');
		expect(link.getAttribute('rel')).toBe('noopener noreferrer');
		expect(link.querySelector('svg')?.getAttribute('aria-hidden')).toBe('true');
		link.addEventListener('click', (event) => event.preventDefault());
		link.click();
		expect(onAccountOpen).toHaveBeenCalledTimes(1);
	});
});

describe('app rows', () => {
	it('renders each row as a button in order above Theme, and calls only the activated one', async () => {
		const onFirst = vi.fn();
		const onSecond = vi.fn();
		const menu = await render({
			appRows: [
				{ label: 'Settings', icon: 'settings', onSelect: onFirst },
				{ label: 'Other', icon: 'settings', onSelect: onSecond }
			],
			theme: { choice: 'light', onChange: () => {} }
		});
		const rows = [...menu.querySelectorAll<HTMLButtonElement>('button[type="button"]')].filter(
			(button) => button.textContent?.trim() !== 'Log out'
		);
		expect(rows.map((row) => row.textContent?.trim())).toEqual(['Settings', 'Other']);
		const theme = [...menu.querySelectorAll('*')].find((node) => node.textContent?.trim() === 'Theme')!;
		expect(rows[1].compareDocumentPosition(theme) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
		rows[1].click();
		expect(onSecond).toHaveBeenCalledTimes(1);
		expect(onFirst).not.toHaveBeenCalled();
	});

	it('renders no app row for an empty list', async () => {
		const menu = await render({ appRows: [] });
		expect([...menu.querySelectorAll('button')].map((button) => button.textContent?.trim())).toEqual([
			'Log out'
		]);
	});
});

describe('theme rows', () => {
	it('labels a group Theme with three radios, the passed choice checked, and reports nothing on mount', async () => {
		const onChange = vi.fn();
		const menu = await render({ theme: { choice: 'dark', onChange } });
		const group = menu.querySelector('[role="radiogroup"]')!;
		const label = document.getElementById(group.getAttribute('aria-labelledby')!);
		expect(label?.textContent?.trim()).toBe('Theme');
		expect([...group.querySelectorAll('label')].map((row) => row.textContent?.trim())).toEqual([
			'Follow system',
			'Light',
			'Dark'
		]);
		expect(radios(menu)).toHaveLength(3);
		expect(checkedLabel(menu)).toBe('Dark');
		expect(onChange).not.toHaveBeenCalled();
	});

	it('checks the new choice when the passed choice changes', async () => {
		const state = new SvelteMap<string, ThemeChoice>([['choice', 'light']]);
		const target = document.createElement('div');
		document.body.append(target);
		const theme = {
			get choice() {
				return state.get('choice')!;
			},
			onChange: () => {}
		};
		mounted.push({
			target,
			component: mount(AccountMenu, { target, props: baseProps({ theme }) })
		});
		await tick();
		expect(checkedLabel(target)).toBe('Light');
		state.set('choice', 'follow-system');
		await tick();
		expect(checkedLabel(target)).toBe('Follow system');
	});

	it('reports the picked choice once, and snaps back to the passed choice when the app does not take it', async () => {
		const onChange = vi.fn();
		const menu = await render({ theme: { choice: 'light', onChange } });
		const dark = radios(menu)[2];
		dark.click();
		await tick();
		expect(onChange).toHaveBeenCalledExactlyOnceWith('dark');
		expect(checkedLabel(menu)).toBe('Light');
	});

	it('reports nothing when the checked radio is clicked again', async () => {
		const onChange = vi.fn();
		const menu = await render({ theme: { choice: 'light', onChange } });
		radios(menu)[1].click();
		await tick();
		expect(onChange).not.toHaveBeenCalled();
	});

	it('renders no Theme row and no radios without theme rows', async () => {
		const menu = await render();
		expect(radios(menu)).toHaveLength(0);
		expect(menu.querySelector('[role="radiogroup"]')).toBeNull();
		expect(menu.textContent).not.toContain('Theme');
	});

	it('keeps two mounted menus in separate radio groups', async () => {
		const first = await render({ theme: { choice: 'light', onChange: () => {} } });
		const second = await render({ theme: { choice: 'dark', onChange: () => {} } });
		const names = new Set([...radios(first), ...radios(second)].map((radio) => radio.name));
		expect(names.size).toBe(2);
		expect(checkedLabel(first)).toBe('Light');
		expect(checkedLabel(second)).toBe('Dark');
	});
});

describe('log out', () => {
	it('is a type=button that calls onLogOut once and shows no alert without a failure', async () => {
		const onLogOut = vi.fn();
		const menu = await render({ onLogOut });
		const button = [...menu.querySelectorAll('button')].find((candidate) =>
			candidate.textContent?.includes('Log out')
		)!;
		expect(button.type).toBe('button');
		expect(menu.querySelector('[role="alert"]')).toBeNull();
		expect(menu.querySelector('form')).toBeNull();
		button.click();
		expect(onLogOut).toHaveBeenCalledTimes(1);
	});

	it('shows the failure as an alert after the button', async () => {
		const menu = await render({ onLogOut: () => {}, logOutFailure: 'Logging out failed.' });
		const alert = menu.querySelector('[role="alert"]')!;
		expect(alert.textContent).toContain('Logging out failed.');
		const button = [...menu.querySelectorAll('button')].find((candidate) =>
			candidate.textContent?.includes('Log out')
		)!;
		expect(button.compareDocumentPosition(alert) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
	});
});

describe('legal row', () => {
	it('opens the links in a new tab in the given order inside a nav named Legal', async () => {
		const menu = await render({
			legalLinks: [
				{ label: 'Privacy', href: '/privacy' },
				{ label: 'Imprint', href: '/imprint' }
			]
		});
		const nav = menu.querySelector('nav')!;
		expect(nav.getAttribute('aria-label')).toBe('Legal');
		const anchors = [...nav.querySelectorAll('a')];
		expect(anchors.map((anchor) => anchor.textContent)).toEqual(['Privacy', 'Imprint']);
		for (const anchor of anchors) {
			expect(anchor.getAttribute('target')).toBe('_blank');
			expect(anchor.getAttribute('rel')).toBe('noopener');
		}
	});

	it('renders no legal row for an empty list', async () => {
		const menu = await render({ legalLinks: [] });
		expect(menu.querySelector('nav')).toBeNull();
	});
});
