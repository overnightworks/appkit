import { render } from 'svelte/server';
import { describe, expect, it } from 'vitest';
import HelperChat from './HelperChat.svelte';
import { loadWords, type Language } from './words/index.ts';

const languages: Language[] = ['en', 'de'];

describe.each(languages)('HelperChat server-rendered in the %s words', (language) => {
	it('renders the messages, the composer and the kit words without a script', async () => {
		const words = await loadWords(language);
		const { body } = render(HelperChat, {
			props: {
				messages: [
					{ role: 'user', text: 'Rewrite it' },
					{ role: 'assistant', text: 'Done', toolCalls: [{ name: 'rewrite', input: {} }] }
				],
				running: false,
				history: { state: 'ready' },
				helperName: 'Mozart',
				emptyHint: 'Ask me anything',
				placeholder: 'Ask for a rewrite…',
				draft: 'A draft',
				onDraft: () => {},
				onSend: () => {},
				words
			}
		});
		expect(body).toContain('Rewrite it');
		expect(body).toContain('Done');
		expect(body).toContain(words['helperChat.ranTool']({ tool: 'rewrite' }));
		expect(body).toContain(words['helperChat.send']);
		expect(body).toContain(words['helperChat.composerLabel']({ name: 'Mozart' }));
		expect(body).toMatch(/<textarea\b[^>]*>/);
		expect(body).toMatch(/role="status"/);
		expect(body).not.toMatch(/<script\b/);
	});

	it('renders the loading word and no list while the history loads', async () => {
		const words = await loadWords(language);
		const { body } = render(HelperChat, {
			props: {
				messages: [],
				running: false,
				history: { state: 'loading' },
				helperName: 'Mozart',
				emptyHint: 'Ask me anything',
				placeholder: '',
				draft: '',
				onDraft: () => {},
				onSend: () => {},
				words
			}
		});
		expect(body).toContain(words['helperChat.loading']);
		expect(body).not.toContain('Ask me anything');
	});
});
