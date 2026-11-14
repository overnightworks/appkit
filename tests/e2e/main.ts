import './app.css';
import { mount } from 'svelte';
import { SvelteMap } from 'svelte/reactivity';
import {
	AccountMenu,
	AgentControl,
	EarMark,
	HearingSwitch,
	LegalLinks,
	SignInPage,
	TurnState,
	loadKitWords,
	type AgentControlOutcome,
	type AgentRow,
	type HearingKind,
	type KitLanguage,
	type KitWords,
	type SignInState,
	type ThemeChoice,
	type TurnOutcome
} from 'overnightworks-design';
import HelperChatStub from './HelperChatStub.svelte';
import MarkedSentence from './MarkedSentence.svelte';

declare global {
	interface Window {
		/** Every report the menu, the agent control, the hearing switch, the helper chat's stub app or the sign-in page made, in order. */
		reports: string[];
	}
}

const legalLinks = [
	{ label: 'Imprint', href: '/imprint' },
	{ label: 'Privacy', href: '/privacy' }
];

/** Long enough that the row wraps in the 256 px panel, as an app's real labels do. */
const menuLegalLinks = [
	{ label: 'Impressum', href: '/imprint' },
	{ label: 'Datenschutz', href: '/privacy' },
	{ label: 'Nutzungsbedingungen', href: '/terms' }
];

/** The app's side of the theme: it keeps the choice in memory and sets data-theme, as an app would. */
function themeHolder(takesChoice: boolean) {
	const held = new SvelteMap<string, ThemeChoice>([['choice', 'follow-system']]);
	const apply = (choice: ThemeChoice): void => {
		if (choice === 'follow-system') document.documentElement.removeAttribute('data-theme');
		else document.documentElement.setAttribute('data-theme', choice);
	};
	return {
		get choice() {
			return held.get('choice')!;
		},
		onChange(choice: ThemeChoice) {
			window.reports.push(`theme:${choice}`);
			if (!takesChoice) return;
			held.set('choice', choice);
			apply(choice);
		}
	};
}

function mountMenu(variant: string, words: KitWords): void {
	window.reports = [];
	const report = (what: string) => () => void window.reports.push(what);
	const common = {
		name: 'Felix mcDonald',
		accountHref: '/account',
		onAccountOpen: report('account'),
		appRows: [{ label: 'Settings', onSelect: report('settings') }] as const,
		legalLinks: menuLegalLinks
	};
	const logOut =
		variant === 'action' ? { logOutAction: '/logout' } : { onLogOut: report('logout') };
	const theme = variant === 'no-theme' ? undefined : themeHolder(variant !== 'ignore');
	mount(AccountMenu, { target: document.body, props: { ...common, ...logOut, theme, words } });
}

/** A long name shows how a row keeps its action in the panel. */
const agentRows: AgentRow[] = [
	{ key: 'key-mozart', name: 'Mozart', state: 'available' },
	{ key: 'key-bach', name: 'Bach', state: 'inviting' },
	{ key: 'key-leonardo', name: 'Leonardo da Vinci, the long-named painter and inventor', state: 'here' }
];

/** The variants that end Mozart's call, by the outcome the page passes. */
const endedVariants: Record<string, AgentControlOutcome> = {
	'ended-no-answer': 'no-answer',
	'ended-busy': 'busy',
	'ended-owner-absent': 'owner-absent'
};

function rowsOfVariant(variant: string): AgentRow[] {
	if (variant === 'empty' || variant === 'empty-full') return [];
	const outcome = endedVariants[variant];
	return outcome ? [{ key: 'key-mozart', name: 'Mozart', state: 'ended', outcome }, ...agentRows.slice(1)] : agentRows;
}

function mountAgentControl(variant: string, words: KitWords): void {
	window.reports = [];
	mount(AgentControl, {
		target: document.body,
		props: {
			rows: rowsOfVariant(variant),
			full: variant === 'empty-full',
			refusal: variant === 'refusal' ? 'owner-absent' : undefined,
			onCall: (key: string) => void window.reports.push(`call:${key}`),
			onSendAway: (key: string) => void window.reports.push(`leave:${key}`),
			words
		}
	});
}

/**
 * Both chips on a stand-in for the video they always sit on, held by the app as a controlled switch is:
 * `off` starts them off, `ignore` is an app that never takes the change.
 */
function mountHearingSwitches(variant: string, words: KitWords): void {
	window.reports = [];
	const held = new SvelteMap<HearingKind, boolean>([
		['hear', variant !== 'off'],
		['listen', variant !== 'off']
	]);
	const stage = document.createElement('div');
	stage.className = 'hearing-stage';
	document.body.append(stage);
	for (const kind of ['hear', 'listen'] as const satisfies HearingKind[]) {
		mount(HearingSwitch, {
			target: stage,
			props: {
				kind,
				get on() {
					return held.get(kind)!;
				},
				onChange(on: boolean) {
					window.reports.push(`${kind}:${on}`);
					if (variant !== 'ignore') held.set(kind, on);
				},
				words
			}
		});
	}
}

/**
 * Ear marks stacked in a column on a stand-in for a tile, as an app places them: `one` shows a single mark
 * on one's own tile, `two` stacks two agents' marks on another person's tile, `long` shows an agent whose
 * name does not fit.
 */
function mountEarMarks(variant: string, words: KitWords): void {
	const stage = document.createElement('div');
	stage.className = 'ear-stage';
	document.body.append(stage);
	const agents =
		variant === 'long'
			? ['Leonardo da Vinci, the long-named painter and inventor']
			: variant === 'two'
				? ['Mozart', 'Bach']
				: ['Mozart'];
	for (const agent of agents) {
		mount(EarMark, { target: stage, props: { agent, person: variant === 'two' ? 'Anna' : undefined, words } });
	}
}

/**
 * The turn-state part: `alone` stacks the four outcomes and an unstated one, `here` shows it in the here
 * row of an agent control beside a short and a long agent name.
 */
function mountTurnState(variant: string, words: KitWords): void {
	const outcomes: (TurnOutcome | undefined)[] = ['not_enabled', 'busy', 'budget_spent', 'unavailable', undefined];
	if (variant === 'here') {
		mount(AgentControl, {
			target: document.body,
			props: {
				rows: [
					{ key: 'key-mozart', name: 'Mozart', state: 'here', turnState: 'busy' },
					{ key: 'key-leonardo', name: 'Leonardo da Vinci, the long-named painter and inventor', state: 'here', turnState: 'unavailable' },
					{ key: 'key-bach', name: 'Bach', state: 'here' }
				],
				onCall: () => {},
				onSendAway: () => {},
				words
			}
		});
		return;
	}
	const stage = document.createElement('div');
	stage.className = 'turn-stage';
	document.body.append(stage);
	for (const outcome of outcomes) {
		const row = document.createElement('div');
		stage.append(row);
		mount(TurnState, { target: row, props: { outcome, words } });
	}
}

/** The languages this page offers; the type check fails when the kit lacks one. */
const pageLanguages = ['de', 'en'] as const satisfies readonly KitLanguage[];

const query = new URLSearchParams(location.search);
/** The app's side of the kit's words: the loader called with the language the page names, `?lang=`, or en. */
const pageLanguage = pageLanguages.find((candidate) => candidate === query.get('lang')) ?? 'en';
document.documentElement.lang = pageLanguage;

if (query.has('words')) {
	const tag = query.get('words');
	const language = pageLanguages.find((candidate) => candidate === tag) ?? pageLanguages[0];
	document.documentElement.lang = language;
	void loadKitWords(language).then((words) => {
		document.body.innerHTML = `<p role="status">${words['account.logOut']}</p>`;
	});
} else if (query.has('typed')) {
	// A person typed the name; the app wrote the words around it.
	document.body.innerHTML = '<main><h1>Source <span class="as-typed">talks</span></h1></main>';
} else if (query.has('legal')) {
	// The markup contract of a page that cannot render Svelte, beside the component's own row.
	const words = await loadKitWords(pageLanguage);
	document.body.innerHTML = `<div id="written"><nav class="legal" aria-label="${words['legalLinks.name']}">${legalLinks
		.map((link) => `<a href="${link.href}">${link.label}</a>`)
		.join('')}</nav></div><div id="component"></div>`;
	mount(LegalLinks, {
		target: document.getElementById('component')!,
		props: { links: legalLinks, words }
	});
} else if (query.has('marked')) {
	mount(MarkedSentence, { target: document.body });
} else if (query.has('helper')) {
	window.reports = [];
	mount(HelperChatStub, {
		target: document.body,
		props: { variant: query.get('helper') ?? '', words: await loadKitWords(pageLanguage) }
	});
} else if (query.has('turn')) {
	mountTurnState(query.get('turn') ?? '', await loadKitWords(pageLanguage));
} else if (query.has('ear')) {
	mountEarMarks(query.get('ear') ?? '', await loadKitWords(pageLanguage));
} else if (query.has('hearing')) {
	mountHearingSwitches(query.get('hearing') ?? '', await loadKitWords(pageLanguage));
} else if (query.has('agents')) {
	mountAgentControl(query.get('agents') ?? '', await loadKitWords(pageLanguage));
} else if (query.has('menu')) {
	mountMenu(query.get('menu') ?? '', await loadKitWords(pageLanguage));
} else {
	window.reports = [];
	const state: SignInState = query.has('signing-in')
		? { page: 'signing-in', tabHref: '/app' }
		: query.has('window-blocked')
			? { page: 'window-blocked', tabHref: '/app' }
			: query.has('unfinished')
				? { page: 'signed-out', signInHref: '/login', unfinished: true }
				: query.has('login-failed')
					? { page: 'login-failed', signInHref: '/login' }
					: query.has('no-access')
						? { page: 'no-access', logOutAction: '/logout' }
						: query.has('on-sign-in')
							? { page: 'signed-out', signInHref: '/login', onSignIn: () => void window.reports.push('sign-in') }
							: { page: 'signed-out', signInHref: '/login' };
	mount(SignInPage, {
		target: document.body,
		props: {
			appName: 'Probe',
			state,
			legalLinks: legalLinks.slice(0, 2),
			words: await loadKitWords(pageLanguage)
		}
	});
}
