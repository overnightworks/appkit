import { mount, tick, unmount } from 'svelte';
import { afterEach, describe, expect, it, vi } from 'vitest';
import SignInPage from './SignInPage.svelte';
import type { SignInPageProps } from './types.ts';
import { loadWords } from './words/index.ts';

const en = await loadWords('en');
const de = await loadWords('de');

const mounted: { target: HTMLElement; component: ReturnType<typeof mount> }[] = [];

async function render(overrides: Partial<SignInPageProps> = {}): Promise<HTMLElement> {
	const target = document.createElement('div');
	document.body.append(target);
	const props: SignInPageProps = {
		appName: 'Hallucinai',
		state: { page: 'signed-out', signInHref: '/auth/login' },
		legalLinks: [],
		words: en,
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
		expect(page.querySelector('h1')?.textContent).toBe(en['signIn.loggedOut']);
		const actions = page.querySelectorAll('a, button');
		expect(actions).toHaveLength(1);
		expect(actions[0].tagName).toBe('A');
		expect(actions[0].textContent).toBe(en['signIn.logIn']);
		expect(actions[0].getAttribute('href')).toBe('/auth/login');
		expect(actions[0].hasAttribute('data-sveltekit-reload')).toBe(true);
	});
});

function click(element: Element, init: MouseEventInit = {}): MouseEvent {
	const event = new MouseEvent('click', { bubbles: true, cancelable: true, button: 0, ...init });
	element.dispatchEvent(event);
	return event;
}

describe('signed-out with onSignIn', () => {
	it('calls onSignIn once and keeps the page from navigating on a plain click', async () => {
		const onSignIn = vi.fn();
		const page = await render({ state: { page: 'signed-out', signInHref: '/auth/login', onSignIn } });
		const link = page.querySelector('a')!;
		const event = click(link);
		expect(onSignIn).toHaveBeenCalledTimes(1);
		expect(event.defaultPrevented).toBe(true);
		expect(link.getAttribute('href')).toBe('/auth/login');
		expect(link.hasAttribute('data-sveltekit-reload')).toBe(true);
	});
});

describe('signed-out with onSignIn, a click that keeps the browser its own way', () => {
	it.each([
		['Ctrl', { ctrlKey: true }],
		['Meta', { metaKey: true }],
		['Shift', { shiftKey: true }],
		['Alt', { altKey: true }],
		['a non-primary button', { button: 1 }]
	])('calls nothing and does not prevent the default on %s', async (_name, init) => {
		const onSignIn = vi.fn();
		const page = await render({ state: { page: 'signed-out', signInHref: '/auth/login', onSignIn } });
		const event = click(page.querySelector('a')!, init);
		expect(onSignIn).not.toHaveBeenCalled();
		expect(event.defaultPrevented).toBe(false);
	});
});

describe('signed-out, unfinished', () => {
	it('shows the banner as an alert above the one Log in action and keeps the heading', async () => {
		const onSignIn = vi.fn();
		const page = await render({
			state: { page: 'signed-out', signInHref: '/auth/login', unfinished: true, onSignIn }
		});
		expect(page.querySelector('h1')?.textContent).toBe(en['signIn.loggedOut']);
		const alert = page.querySelector('[role="alert"]')!;
		expect(alert.textContent).toContain(en['signIn.signInUnfinished']);
		const actions = page.querySelectorAll('a, button');
		expect(actions).toHaveLength(1);
		expect(alert.compareDocumentPosition(actions[0]) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
		click(actions[0]);
		expect(onSignIn).toHaveBeenCalledTimes(1);
	});
});

describe('signing-in', () => {
	it('names the wait, hides its shape and offers only a link that opens the app in a tab', async () => {
		const page = await render({ state: { page: 'signing-in', tabHref: '/app' } });
		expect(page.querySelector('h1')?.textContent).toBe(en['signIn.signingIn']);
		expect(page.textContent).toContain(en['signIn.inOtherWindow']);
		expect(page.querySelector('[role="alert"]')).toBeNull();
		const shape = page.querySelector('main [aria-hidden="true"]:not(a *)');
		expect(shape).not.toBeNull();
		const actions = page.querySelectorAll('a, button');
		expect(actions).toHaveLength(1);
		expect(actions[0].textContent?.trim()).toBe(en['signIn.openInTab']);
		expect(actions[0].getAttribute('href')).toBe('/app');
		expect(actions[0].getAttribute('target')).toBe('_blank');
		expect(actions[0].getAttribute('rel')).toBe('noopener');
	});
});

describe('window-blocked', () => {
	it('says the window was blocked, shows no wait and offers only a link that opens the app in a tab', async () => {
		const page = await render({ state: { page: 'window-blocked', tabHref: '/app' } });
		expect(page.querySelector('h1')?.textContent).toBe(en['signIn.windowBlocked']);
		expect(page.textContent).toContain(en['signIn.windowBlockedSentence']);
		expect(page.querySelector('main [aria-hidden="true"]:not(a *)')).toBeNull();
		expect(page.querySelector('[role="alert"], button')).toBeNull();
		const actions = page.querySelectorAll('a, button');
		expect(actions).toHaveLength(1);
		expect(actions[0].textContent?.trim()).toBe(en['signIn.openInTab']);
		expect(actions[0].getAttribute('href')).toBe('/app');
		expect(actions[0].getAttribute('target')).toBe('_blank');
		expect(actions[0].getAttribute('rel')).toBe('noopener');
	});
});

describe('login-failed', () => {
	it('shows the failure banner as an alert and offers one Try again link that reloads the page', async () => {
		const page = await render({ state: { page: 'login-failed', signInHref: '/auth/login?retry' } });
		expect(page.querySelector('h1')?.textContent).toBe(en['signIn.loginFailed']);
		expect(page.querySelector('[role="alert"]')?.textContent).toContain(en['signIn.loginFailedBanner']);
		const actions = page.querySelectorAll('a, button');
		expect(actions).toHaveLength(1);
		expect(actions[0].textContent).toBe(en['signIn.tryAgain']);
		expect(actions[0].getAttribute('href')).toBe('/auth/login?retry');
		expect(actions[0].hasAttribute('data-sveltekit-reload')).toBe(true);
	});
});

describe('no-access', () => {
	it('names the app, shows no alert, and offers one Log out button that calls onLogOut once', async () => {
		const onLogOut = vi.fn();
		const page = await render({ state: { page: 'no-access', onLogOut } });
		expect(page.querySelector('h1')?.textContent).toBe(en['signIn.noAccess']);
		expect(page.textContent).toContain(en['signIn.noAccessSentence']({ appName: 'Hallucinai' }));
		expect(page.querySelector('[role="alert"]')).toBeNull();
		const actions = page.querySelectorAll('a, button');
		expect(actions).toHaveLength(1);
		const button = actions[0] as HTMLButtonElement;
		expect(button.tagName).toBe('BUTTON');
		expect(button.type).toBe('button');
		expect(button.textContent).toBe(en['signIn.logOut']);
		expect(page.textContent).not.toContain('Back');
		button.click();
		expect(onLogOut).toHaveBeenCalledTimes(1);
	});

	it('shows only the heading and the sentence when the app passes no log-out form', async () => {
		const page = await render({ state: { page: 'no-access' } });
		expect(page.querySelector('h1')?.textContent).toBe(en['signIn.noAccess']);
		expect(page.textContent).toContain(en['signIn.noAccessSentence']({ appName: 'Hallucinai' }));
		expect(page.querySelector('form, button, a, [role="alert"]')).toBeNull();
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
		for (const anchor of page.querySelectorAll('nav a')) {
			expect(anchor.hasAttribute('target')).toBe(false);
			expect(anchor.hasAttribute('rel')).toBe(false);
		}
	});

	it.each<[string, SignInPageProps['state']]>([
		['signed-out', { page: 'signed-out', signInHref: '/auth/login' }],
		['signing-in', { page: 'signing-in', tabHref: '/app' }],
		['window-blocked', { page: 'window-blocked', tabHref: '/app' }],
		['login-failed', { page: 'login-failed', signInHref: '/auth/login' }],
		['no-access', { page: 'no-access', onLogOut: () => {} }]
	])('opens every legal link in a new tab with legalLinksNewTab on the %s state', async (_name, state) => {
		const page = await render({
			state,
			legalLinksNewTab: true,
			legalLinks: [
				{ label: 'Impressum', href: '/impressum' },
				{ label: 'Datenschutz', href: '/datenschutz' }
			]
		});
		const anchors = [...page.querySelectorAll('nav a')];
		expect(anchors).toHaveLength(2);
		for (const anchor of anchors) {
			expect(anchor.getAttribute('target')).toBe('_blank');
			expect(anchor.getAttribute('rel')).toBe('noopener');
		}
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

describe('words from the app', () => {
	const appName = 'Hallucinai';
	const noAccessSentence = de['signIn.noAccessSentence']({ appName });

	function visibleTexts(page: HTMLElement): string[] {
		return [...page.querySelectorAll('h1, p, a, button, [role="alert"]')].map(
			(element) => element.textContent?.trim() ?? ''
		);
	}

	it.each([
		['signed-out', { page: 'signed-out', signInHref: '/auth/login' }, ['Du bist abgemeldet.', 'Anmelden']],
		[
			'signed-out, unfinished',
			{ page: 'signed-out', signInHref: '/auth/login', unfinished: true },
			['Du bist abgemeldet.', de['signIn.signInUnfinished'], 'Anmelden']
		],
		[
			'signing-in',
			{ page: 'signing-in', tabHref: '/app' },
			[de['signIn.signingIn'], de['signIn.inOtherWindow'], de['signIn.openInTab']]
		],
		[
			'window-blocked',
			{ page: 'window-blocked', tabHref: '/app' },
			[de['signIn.windowBlocked'], de['signIn.windowBlockedSentence'], de['signIn.openInTab']]
		],
		[
			'login-failed',
			{ page: 'login-failed', signInHref: '/auth/login' },
			['Anmeldung fehlgeschlagen', de['signIn.loginFailedBanner'], 'Erneut versuchen']
		],
		[
			'no-access with a callback',
			{ page: 'no-access', onLogOut: () => {} },
			['Kein Zugang', noAccessSentence, 'Abmelden']
		],
		[
			'no-access with a form action',
			{ page: 'no-access', logOutAction: '/logout' },
			['Kein Zugang', noAccessSentence, 'Abmelden']
		],
		['no-access without a log-out form', { page: 'no-access' }, ['Kein Zugang', noAccessSentence]]
	] as const)('shows the given words and no en word in %s', async (_name, state, shown) => {
		const page = await render({ words: de, state });
		expect(visibleTexts(page)).toEqual(shown);
		const text = page.textContent ?? '';
		for (const enText of visibleTexts(await render({ state }))) expect(text).not.toContain(enText);
		const alert = page.querySelector('[role="alert"]');
		if (state.page === 'login-failed') expect(alert?.textContent?.trim()).toBe(de['signIn.loginFailedBanner']);
		else if ('unfinished' in state) expect(alert?.textContent?.trim()).toBe(de['signIn.signInUnfinished']);
		else expect(alert).toBeNull();
	});
});

describe('en words', () => {
	it.each([
		['signed-out', { page: 'signed-out', signInHref: '/auth/login' }, ['You are logged out.', 'Log in']],
		[
			'signed-out, unfinished',
			{ page: 'signed-out', signInHref: '/auth/login', unfinished: true },
			['You are logged out.', 'Sign-in did not finish.', 'Log in']
		],
		[
			'signing-in',
			{ page: 'signing-in', tabHref: '/app' },
			['Signing in', 'In the other window', 'Open in a tab']
		],
		[
			'window-blocked',
			{ page: 'window-blocked', tabHref: '/app' },
			['Window blocked', 'Your browser blocked the sign-in window.', 'Open in a tab']
		],
		[
			'login-failed',
			{ page: 'login-failed', signInHref: '/auth/login' },
			['Login failed', 'Sign-in did not work. Please try again.', 'Try again']
		],
		[
			'no-access with a callback',
			{ page: 'no-access', onLogOut: () => {} },
			['No access', 'You are signed in, but this account has no access to Hallucinai.', 'Log out']
		],
		[
			'no-access with a form action',
			{ page: 'no-access', logOutAction: '/logout' },
			['No access', 'You are signed in, but this account has no access to Hallucinai.', 'Log out']
		]
	] as const)('renders the en texts of the kit in %s', async (_name, state, shown) => {
		const page = await render({ state });
		const texts = [...page.querySelectorAll('h1, p, [role="alert"] span:last-child, a, button')].map((element) =>
			element.textContent?.trim()
		);
		expect(texts).toEqual(shown);
	});
});
