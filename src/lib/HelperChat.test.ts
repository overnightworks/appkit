import { createRawSnippet, mount, tick, unmount } from 'svelte';
import { SvelteMap } from 'svelte/reactivity';
import { afterEach, describe, expect, it, vi } from 'vitest';
import HelperChat from './HelperChat.svelte';
import type { HelperChatProps, HelperMessage } from './types.ts';
import { loadWords } from './words/index.ts';

const en = await loadWords('en');
const de = await loadWords('de');

const mounted: { target: HTMLElement; component: ReturnType<typeof mount> }[] = [];

const text = (content: string) => createRawSnippet(() => ({ render: () => `<span>${content}</span>` }));
const button = (content: string) => createRawSnippet(() => ({ render: () => `<button type="button">${content}</button>` }));

function baseProps(overrides: Partial<HelperChatProps<HelperMessage>> = {}): HelperChatProps<HelperMessage> {
	return {
		messages: [],
		running: false,
		history: { state: 'ready' },
		helperName: 'Mozart',
		emptyHint: 'Ask me anything',
		placeholder: 'Ask for a rewrite…',
		draft: '',
		onDraft: () => {},
		onSend: () => {},
		words: en,
		...overrides
	};
}

async function render(overrides: Partial<HelperChatProps<HelperMessage>> = {}): Promise<HTMLElement> {
	const target = document.createElement('div');
	document.body.append(target);
	mounted.push({ target, component: mount(HelperChat, { target, props: baseProps(overrides) }) });
	await tick();
	return target;
}

const field = (root: HTMLElement) => root.querySelector('textarea')!;
const sendButton = (root: HTMLElement) => root.querySelector<HTMLButtonElement>('.send')!;
const status = (root: HTMLElement) => root.querySelector('[role="status"]');
const visibleLine = (root: HTMLElement) => root.querySelector('.list .thinking');

function press(target: HTMLElement, init: KeyboardEventInit): KeyboardEvent {
	const event = new KeyboardEvent('keydown', { bubbles: true, cancelable: true, ...init });
	target.dispatchEvent(event);
	return event;
}

afterEach(async () => {
	for (const { target, component } of mounted.splice(0)) {
		await unmount(component);
		target.remove();
	}
});

describe('the message list', () => {
	it('shows the empty hint while there is no message and no hint once there is one', async () => {
		const empty = await render();
		expect(empty.textContent).toContain('Ask me anything');
		const filled = await render({ messages: [{ role: 'user', text: 'Hello' }] });
		expect(filled.textContent).not.toContain('Ask me anything');
	});

	it('names the message list with the kit word and the helper’s name and makes each message one of its items', async () => {
		const root = await render({ messages: [{ role: 'user', text: 'Hi' }, { role: 'assistant', text: 'Hello' }], words: de });
		const lists = root.querySelectorAll('[role="list"]');
		expect(lists).toHaveLength(1);
		expect(lists[0].getAttribute('aria-label')).toBe(de['helperChat.listLabel']({ name: 'Mozart' }));
		expect([...lists[0].children].map((item) => item.tagName)).toEqual(['LI', 'LI']);
		expect(lists[0].closest('[aria-live]')).toBeNull();
	});

	it('shows only the empty hint, no list, while there is no message', async () => {
		const root = await render();
		expect(root.querySelector('[role="list"], ol, li')).toBeNull();
		expect(root.querySelector('.list')?.textContent).toBe('Ask me anything');
	});

	it('shows each message as written, with its line breaks kept', async () => {
		const root = await render({
			messages: [
				{ role: 'user', text: 'Line one\n  Line two' },
				{ role: 'assistant', text: 'Sure' }
			]
		});
		expect([...root.querySelectorAll('.text')].map((shown) => shown.textContent)).toEqual(['Line one\n  Line two', 'Sure']);
	});

	it('leads each helper message with one AiMark before its tool rows and gives the person none', async () => {
		const root = await render({
			messages: [
				{ role: 'user', text: 'Rewrite it' },
				{ role: 'assistant', text: 'Done', toolCalls: [{ name: 'rewrite', input: {} }] }
			]
		});
		const [personBubble, helperBubble] = [...root.querySelectorAll('.bubble')];
		expect(personBubble.querySelector('.ai-mark')).toBeNull();
		expect(helperBubble.querySelectorAll('.ai-mark')).toHaveLength(1);
		expect(helperBubble.firstElementChild?.querySelector('.ai-mark')).not.toBeNull();
		expect(helperBubble.querySelector('.ai-mark')!.compareDocumentPosition(helperBubble.querySelector('.tool-call')!)).toBe(
			Node.DOCUMENT_POSITION_FOLLOWING
		);
	});

	it('shows no bubble for a helper message with neither text nor tool calls', async () => {
		const root = await render({ messages: [{ role: 'user', text: 'Hi' }, { role: 'assistant', text: '' }] });
		expect(root.querySelectorAll('.bubble')).toHaveLength(1);
	});

	it('shows a tool row with the kit word for the tool, the target and the title the app gives it', async () => {
		const call = { name: 'rewrite', input: { line: 3 } };
		const root = await render({
			messages: [{ role: 'assistant', text: 'Done', toolCalls: [call] }],
			toolCallTarget: createRawSnippet((parameters) => ({
				render: () => `<span class="target">target of ${parameters().call.name}</span>`
			})),
			toolCallTitle: (shown) => JSON.stringify(shown.input)
		});
		const row = root.querySelector('.tool-call')!;
		expect(row.textContent).toContain(en['helperChat.ranTool']({ tool: 'rewrite' }));
		expect(row.querySelector('.target')?.textContent).toBe('target of rewrite');
		expect(row.getAttribute('title')).toBe('{"line":3}');
	});

	it('gives a tool row no title without a title function and no target without a target snippet', async () => {
		const root = await render({
			messages: [{ role: 'assistant', text: 'Done', toolCalls: [{ name: 'rewrite', input: {} }] }]
		});
		const row = root.querySelector('.tool-call')!;
		expect(row.hasAttribute('title')).toBe(false);
		expect(row.children).toHaveLength(1);
	});

	it('shows the app’s problem line after the message it belongs to, called with that message and index', async () => {
		const root = await render({
			messages: [
				{ role: 'user', text: 'Hi' },
				{ role: 'assistant', text: 'Oops' }
			],
			problemLine: createRawSnippet((parameters) => ({
				render: () => `<p class="problem">${parameters().message.role}@${parameters().index}</p>`
			}))
		});
		const messages = [...root.querySelectorAll('.message')];
		expect(messages.map((message) => message.querySelector('.problem')?.textContent)).toEqual(['user@0', 'assistant@1']);
	});

	it('hands the app’s own message type to its snippets', async () => {
		type AppMessage = HelperMessage & { readonly id: string };
		const target = document.createElement('div');
		document.body.append(target);
		const props: HelperChatProps<AppMessage> = {
			...baseProps(),
			messages: [{ role: 'assistant', text: 'Hi', id: 'm-7' }],
			problemLine: createRawSnippet((parameters) => ({ render: () => `<p class="problem">${parameters().message.id}</p>` }))
		};
		mounted.push({ target, component: mount(HelperChat<AppMessage>, { target, props }) });
		await tick();
		expect(target.querySelector('.problem')?.textContent).toBe('m-7');
	});
});

describe('the history', () => {
	it('shows the loading word instead of the list while it loads', async () => {
		const root = await render({ history: { state: 'loading' }, messages: [{ role: 'user', text: 'Hi' }] });
		expect(root.textContent).toContain(en['helperChat.loading']);
		expect(root.querySelector('.list')).toBeNull();
		expect(root.textContent).not.toContain('Hi');
	});

	it('shows the failure as an alert instead of the list when it failed', async () => {
		const root = await render({ history: { state: 'failed', failure: 'Chat is gone' }, messages: [{ role: 'user', text: 'Hi' }] });
		expect(root.querySelector('[role="alert"]')?.textContent).toBe('Chat is gone');
		expect(root.querySelector('.list')).toBeNull();
	});

	it('keeps the composer while the history loads or failed', async () => {
		expect(field(await render({ history: { state: 'loading' } }))).not.toBeNull();
		expect(field(await render({ history: { state: 'failed', failure: 'x' } }))).not.toBeNull();
	});
});

describe('the list element', () => {
	it('binds the message container and reports its scrolling', async () => {
		const onListScroll = vi.fn();
		const root = await render({ onListScroll });
		const list = root.querySelector<HTMLElement>('.list')!;
		list.dispatchEvent(new Event('scroll'));
		expect(onListScroll).toHaveBeenCalledOnce();
	});

	it('hands the container to the app through the bindable list prop', async () => {
		const target = document.createElement('div');
		document.body.append(target);
		const holder: { list?: HTMLElement } = {};
		const props = baseProps();
		Object.defineProperty(props, 'list', { get: () => holder.list, set: (value: HTMLElement) => (holder.list = value), enumerable: true });
		mounted.push({ target, component: mount(HelperChat, { target, props }) });
		await tick();
		expect(holder.list).toBe(target.querySelector('.list'));
		expect(holder.list?.hasAttribute('role')).toBe(false);
	});
});

describe('the thinking line', () => {
	it('is one status element that is there before, during and after a turn, with only its text changing', async () => {
		const messages: HelperMessage[] = [{ role: 'user', text: 'Hi' }, { role: 'assistant', text: '' }];
		const held = new SvelteMap<string, unknown>([
			['messages', messages],
			['running', false]
		]);
		const target = document.createElement('div');
		document.body.append(target);
		const props = Object.defineProperties(baseProps(), {
			messages: { enumerable: true, get: () => held.get('messages') as HelperMessage[] },
			running: { enumerable: true, get: () => held.get('running') as boolean }
		});
		mounted.push({ target, component: mount(HelperChat, { target, props }) });
		await tick();
		const line = status(target)!;
		expect(target.querySelectorAll('[role="status"]')).toHaveLength(1);
		expect(line.textContent).toBe('');

		held.set('running', true);
		await tick();
		expect(status(target)).toBe(line);
		expect(line.textContent).toBe(en['helperChat.thinking']({ name: 'Mozart' }));

		held.set('messages', [messages[0], { role: 'assistant', text: 'Here' }]);
		await tick();
		expect(status(target)).toBe(line);
		expect(line.textContent).toBe('');

		held.set('running', false);
		await tick();
		expect(status(target)).toBe(line);
	});

	it.each([
		['the last message is the person’s', [{ role: 'user', text: 'Hi' }] as HelperMessage[], true],
		['the last helper message already has text', [{ role: 'assistant', text: 'Here' }] as HelperMessage[], true],
		['no turn runs', [{ role: 'assistant', text: '' }] as HelperMessage[], false]
	])('is empty when %s', async (_case, messages, running) => {
		const root = await render({ messages, running });
		expect(status(root)?.textContent).toBe('');
	});

	it('says the helper is thinking, with the helper’s name, while the last helper message has no text', async () => {
		const root = await render({ messages: [{ role: 'assistant', text: '' }], running: true, words: de });
		expect(status(root)?.textContent).toBe(de['helperChat.thinking']({ name: 'Mozart' }));
	});

	it('shows the visible thinking line, hidden from assistive technology, after the tool rows in the last helper bubble', async () => {
		const root = await render({
			messages: [{ role: 'assistant', text: '', toolCalls: [{ name: 'rewrite', input: {} }] }],
			running: true
		});
		const row = root.querySelector('.tool-call')!;
		const visible = visibleLine(root)!;
		expect(root.querySelector('.bubble')!.contains(visible)).toBe(true);
		expect(visible.getAttribute('aria-hidden')).toBe('true');
		expect(visible.textContent).toBe(en['helperChat.thinking']({ name: 'Mozart' }));
		expect(row.compareDocumentPosition(visible)).toBe(Node.DOCUMENT_POSITION_FOLLOWING);
	});

	it('gives the pending helper message one AiMark and its bubble the visible thinking line while it has neither text nor tool calls', async () => {
		const root = await render({ messages: [{ role: 'user', text: 'Hi' }, { role: 'assistant', text: '' }], running: true });
		const bubbles = root.querySelectorAll('.bubble');
		expect(bubbles).toHaveLength(2);
		expect(bubbles[1].querySelectorAll('.ai-mark')).toHaveLength(1);
		expect(bubbles[1].contains(visibleLine(root))).toBe(true);
	});

	it('keeps the status element out of the list, as a direct child of the part’s root', async () => {
		const root = await render({ messages: [{ role: 'user', text: 'Hi' }, { role: 'assistant', text: '' }], running: true });
		expect(status(root)!.parentElement).toBe(root.querySelector('.helper-chat'));
	});

	it.each([
		['starts', false, true],
		['stops', true, false]
	])('keeps the one status element and shows the visible line only while thinking when a turn %s on an unchanged empty helper message', async (_case, before, after) => {
		const held = new SvelteMap<string, boolean>([['running', before]]);
		const target = document.createElement('div');
		document.body.append(target);
		const props = Object.defineProperties(baseProps({ messages: [{ role: 'user', text: 'Hi' }, { role: 'assistant', text: '' }] }), {
			running: { enumerable: true, get: () => held.get('running')! }
		});
		mounted.push({ target, component: mount(HelperChat, { target, props }) });
		await tick();
		const line = status(target)!;
		expect(visibleLine(target) !== null).toBe(before);

		held.set('running', after);
		await tick();
		expect(status(target)).toBe(line);
		expect(target.querySelectorAll('[role="status"]')).toHaveLength(1);
		expect(visibleLine(target) !== null).toBe(after);
		expect(line.textContent === '').toBe(!after);
	});

	it('keeps the one status element while the history changes, with its text empty unless the list shows, and while the list is replaced', async () => {
		const held = new SvelteMap<string, unknown>([
			['history', { state: 'ready' }],
			['messages', [{ role: 'user', text: 'Hi' }, { role: 'assistant', text: '' }]]
		]);
		const target = document.createElement('div');
		document.body.append(target);
		const props = Object.defineProperties(baseProps({ running: true }), {
			history: { enumerable: true, get: () => held.get('history') as HelperChatProps<HelperMessage>['history'] },
			messages: { enumerable: true, get: () => held.get('messages') as HelperMessage[] }
		});
		mounted.push({ target, component: mount(HelperChat, { target, props }) });
		await tick();
		const line = status(target)!;
		expect(line.textContent).toBe(en['helperChat.thinking']({ name: 'Mozart' }));

		for (const state of [{ state: 'loading' }, { state: 'failed', failure: 'Gone' }, { state: 'ready' }]) {
			held.set('history', state);
			await tick();
			expect(status(target)).toBe(line);
			expect(target.querySelectorAll('[role="status"]')).toHaveLength(1);
			expect(line.textContent === '').toBe(state.state !== 'ready');
			expect(visibleLine(target) !== null).toBe(state.state === 'ready');
		}

		held.set('messages', [{ role: 'user', text: 'Earlier' }, { role: 'assistant', text: 'Answer' }, { role: 'user', text: 'Hi' }, { role: 'assistant', text: '' }]);
		await tick();
		expect(status(target)).toBe(line);
		expect(line.textContent).toBe(en['helperChat.thinking']({ name: 'Mozart' }));
		expect(target.querySelectorAll('.bubble')[3].contains(visibleLine(target))).toBe(true);
	});
});

describe('the composer', () => {
	it('names the field by the kit word with the helper’s name and shows the app’s placeholder', async () => {
		const root = await render();
		expect(field(root).getAttribute('aria-label')).toBe(en['helperChat.composerLabel']({ name: 'Mozart' }));
		expect(field(root).placeholder).toBe('Ask for a rewrite…');
	});

	it('shows the draft in the field and reports each edit with the text and the caret', async () => {
		const onDraft = vi.fn();
		const root = await render({ draft: 'Hello', onDraft });
		const input = field(root);
		expect(input.value).toBe('Hello');
		input.value = 'Hello there';
		input.setSelectionRange(5, 5);
		input.dispatchEvent(new Event('input', { bubbles: true }));
		expect(onDraft).toHaveBeenCalledExactlyOnceWith('Hello there', 5);
	});

	it('puts the pick list first in the composer box, above the field', async () => {
		const root = await render({ composerPopup: text('Pick me') });
		const box = field(root).parentElement!;
		expect(box.textContent).toContain('Pick me');
		expect(box.firstElementChild?.textContent).toBe('Pick me');
	});

	it('puts the bar of tags between the banner and the composer box', async () => {
		const root = await render({ composerTop: text('Tag bar'), readOnly: text('Archived') });
		const composer = field(root).closest('.composer')!;
		const order = [...composer.children].map((child) =>
			child.classList.contains('read-only') ? 'banner' : child.classList.contains('composer-box') ? 'box' : child.textContent
		);
		expect(order).toEqual(['banner', 'Tag bar', 'box']);
	});

	it('keeps focus in the composer when a button inside its box is pressed', async () => {
		const root = await render({ composerPopup: button('Pick') });
		const own = new MouseEvent('mousedown', { bubbles: true, cancelable: true });
		sendButton(root).dispatchEvent(own);
		const app = new MouseEvent('mousedown', { bubbles: true, cancelable: true });
		root.querySelector('.composer-box button:not(.send)')!.dispatchEvent(app);
		const inField = new MouseEvent('mousedown', { bubbles: true, cancelable: true });
		field(root).dispatchEvent(inField);
		expect([own.defaultPrevented, app.defaultPrevented, inField.defaultPrevented]).toEqual([true, true, false]);
	});
});

describe('sending', () => {
	it('sends the trimmed draft on a plain Enter and cancels the key', async () => {
		const onSend = vi.fn();
		const root = await render({ draft: '  Hello  \n', onSend });
		const event = press(field(root), { key: 'Enter' });
		expect(onSend).toHaveBeenCalledExactlyOnceWith('Hello');
		expect(event.defaultPrevented).toBe(true);
	});

	it('sends the trimmed draft when Send is pressed', async () => {
		const onSend = vi.fn();
		const root = await render({ draft: ' Hello ', onSend });
		sendButton(root).click();
		expect(onSend).toHaveBeenCalledExactlyOnceWith('Hello');
	});

	it('leaves Shift+Enter to the field, which makes a new line', async () => {
		const onSend = vi.fn();
		const root = await render({ draft: 'Hello', onSend });
		const event = press(field(root), { key: 'Enter', shiftKey: true });
		expect(onSend).not.toHaveBeenCalled();
		expect(event.defaultPrevented).toBe(false);
	});

	it.each<[string, Partial<HelperChatProps<HelperMessage>>]>([
		['a turn runs', { draft: 'Hello', running: true }],
		['the draft is empty', { draft: '' }],
		['the draft is only white space', { draft: ' \n ' }],
		['the chat is read-only', { draft: 'Hello', readOnly: text('Archived') }]
	])('sends nothing and still cancels a plain Enter when %s', async (_case, overrides) => {
		const onSend = vi.fn();
		const root = await render({ onSend, ...overrides });
		const event = press(field(root), { key: 'Enter' });
		expect(onSend).not.toHaveBeenCalled();
		expect(event.defaultPrevented).toBe(true);
	});

	it('sends nothing and still cancels a plain Enter while an IME composes', async () => {
		const onSend = vi.fn();
		const root = await render({ draft: 'こんにち', onSend });
		const event = press(field(root), { key: 'Enter', isComposing: true });
		expect(onSend).not.toHaveBeenCalled();
		expect(event.defaultPrevented).toBe(true);
	});

	it('runs the app’s keydown before the part handles the key', async () => {
		const order: string[] = [];
		const onSend = vi.fn(() => void order.push('send'));
		const root = await render({
			draft: 'Hello',
			onSend,
			onComposerKeydown: (event) => {
				order.push('keydown');
				if (event.key === 'ArrowDown') event.preventDefault();
			}
		});
		press(field(root), { key: 'ArrowDown' });
		const picked = press(field(root), { key: 'Enter' });
		expect(onSend).toHaveBeenCalledTimes(1);
		expect(picked.defaultPrevented).toBe(true);
		expect(order).toEqual(['keydown', 'keydown', 'send']);
	});

	it('sends nothing for an Enter the app’s keydown cancelled', async () => {
		const onSend = vi.fn();
		const root = await render({ draft: 'Hello', onSend, onComposerKeydown: (event) => event.preventDefault() });
		press(field(root), { key: 'Enter' });
		expect(onSend).not.toHaveBeenCalled();
	});

	it('leaves Send on for a draft with text', async () => {
		const root = await render({ draft: 'Hello' });
		expect(sendButton(root).disabled).toBe(false);
	});

	it.each<[string, Partial<HelperChatProps<HelperMessage>>]>([
		['the draft is empty', { draft: '' }],
		['a turn runs', { draft: 'Hello', running: true }],
		['the chat is read-only', { draft: 'Hello', readOnly: text('Archived') }]
	])('turns Send off when %s', async (_case, overrides) => {
		const root = await render(overrides);
		expect(sendButton(root).disabled).toBe(true);
	});

	it('names Send by the kit word', async () => {
		const root = await render({ words: de });
		expect(sendButton(root).textContent?.trim()).toBe(de['helperChat.send']);
	});
});

describe('read-only', () => {
	it('shows the banner above the composer and disables the field and Send', async () => {
		const root = await render({ draft: 'Hello', readOnly: text('This chat is archived') });
		expect(root.querySelector('.read-only')?.textContent).toContain('This chat is archived');
		expect(field(root).disabled).toBe(true);
		expect(sendButton(root).disabled).toBe(true);
	});

	it('shows no banner and enables the field without the snippet', async () => {
		const root = await render();
		expect(root.querySelector('.read-only')).toBeNull();
		expect(field(root).disabled).toBe(false);
	});
});
