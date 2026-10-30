import { mount, tick, unmount } from 'svelte';
import { afterEach, describe, expect, it, vi } from 'vitest';
import SignInPage from './SignInPage.svelte';
import type { SignInPageProps } from './types.ts';

const mounted: { target: HTMLElement; component: ReturnType<typeof mount> }[] = [];

async function render(overrides: Partial<SignInPageProps> = {}): Promise<HTMLElement> {
	const target = document.createElement('div');
	document.body.append(target);
	const props: SignInPageProps = {
		appName: 'Hallucinai',
		state: { page: 'signed-out', signInHref: '/auth/login' },
		legalLinks: [],
		...overrides
	};
	mounted.push({ target, component: mount(SignInPage, { target, props }) });
	await tick();
	return target;
}

afterEach(async () => {
	for (const { target, component } of mounted.splice(0)) {
		await unmount(component);
		target.remove();
	}
	document.title = '';
});

describe('signed-out', () => {
	it('tells the user they are logged out and offers one Log in link that reloads the page', async () => {
		const page = await render();
		expect(page.querySelector('h1')?.textContent).toBe('You are logged out.');
		const actions = page.querySelectorAll('a, button');
		expect(actions).toHaveLength(1);
		expect(actions[0].tagName).toBe('A');
		expect(actions[0].textContent).toBe('Log in');
		expect(actions[0].getAttribute('href')).toBe('/auth/login');
		expect(actions[0].hasAttribute('data-sveltekit-reload')).toBe(true);
	});
});

describe('login-failed', () => {
	it('shows the failure banner as an alert and offers one Try again link that reloads the page', async () => {
		const page = await render({ state: { page: 'login-failed', signInHref: '/auth/login?retry' } });
		expect(page.querySelector('h1')?.textContent).toBe('Login failed');
		expect(page.querySelector('[role="alert"]')?.textContent).toContain(
			'Sign-in did not work. Please try again.'
		);
		const actions = page.querySelectorAll('a, button');
		expect(actions).toHaveLength(1);
		expect(actions[0].textContent).toBe('Try again');
		expect(actions[0].getAttribute('href')).toBe('/auth/login?retry');
		expect(actions[0].hasAttribute('data-sveltekit-reload')).toBe(true);
	});
});

describe('no-access', () => {
	it('names the app, shows no alert, and offers one Log out button that calls onLogOut once', async () => {
		const onLogOut = vi.fn();
		const page = await render({ state: { page: 'no-access', onLogOut } });
		expect(page.querySelector('h1')?.textContent).toBe('No access');
		expect(page.textContent).toContain(
			'You are signed in, but this account has no access to Hallucinai.'
		);
		expect(page.querySelector('[role="alert"]')).toBeNull();
		const actions = page.querySelectorAll('a, button');
		expect(actions).toHaveLength(1);
		const button = actions[0] as HTMLButtonElement;
		expect(button.tagName).toBe('BUTTON');
		expect(button.type).toBe('button');
		expect(button.textContent).toBe('Log out');
		expect(page.textContent).not.toContain('Back');
		button.click();
		expect(onLogOut).toHaveBeenCalledTimes(1);
	});

	it('shows the log out failure in an alert when the app gives one', async () => {
		const page = await render({
			state: { page: 'no-access', onLogOut: () => {}, logOutFailure: 'Logging out failed.' }
		});
		expect(page.querySelector('[role="alert"]')?.textContent).toContain('Logging out failed.');
	});

	it('shows no alert when the app gives no log out failure', async () => {
		const page = await render({ state: { page: 'no-access', onLogOut: () => {} } });
		expect(page.querySelector('[role="alert"]')).toBeNull();
	});
});

describe('page frame', () => {
	it('sets the document title to the app name over a title set before', async () => {
		document.title = 'Something else';
		await render({ appName: 'Presentator' });
		expect(document.title).toBe('Presentator');
	});

	it('shows one legal link per entry in the given order with its label and href', async () => {
		const links = [
			{ label: 'Impressum', href: '/impressum' },
			{ label: 'Datenschutz', href: '/datenschutz' }
		];
		const page = await render({ legalLinks: links });
		const shown = [...page.querySelectorAll('nav a')].map((anchor) => ({
			label: anchor.textContent,
			href: anchor.getAttribute('href')
		}));
		expect(shown).toEqual(links);
	});

	it('shows no legal row when the list is empty', async () => {
		const page = await render({ legalLinks: [] });
		expect(page.querySelector('nav')).toBeNull();
	});

	it('writes the app name as the wordmark text and its data-text and sets no data-theme', async () => {
		const page = await render({ appName: 'HopIn' });
		const wordmark = page.querySelector('[data-text]');
		expect(wordmark?.textContent).toBe('HopIn');
		expect(wordmark?.getAttribute('data-text')).toBe('HopIn');
		expect(document.querySelector('[data-theme]')).toBeNull();
	});
});

describe('state shape', () => {
	it('rejects a sign-in link on the no-access state at type level', () => {
		const props: SignInPageProps = {
			appName: 'X',
			legalLinks: [],
			// @ts-expect-error no-access carries no signInHref
			state: { page: 'no-access', onLogOut: () => {}, signInHref: '/x' }
		};
		expect(props.state.page).toBe('no-access');
	});
});
