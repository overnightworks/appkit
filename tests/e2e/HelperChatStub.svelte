<script lang="ts">
	import { untrack } from 'svelte';
	import { HelperChat, type HelperHistory, type HelperMessage, type KitWords } from 'overnightworks-design';

	/** What an app keeps beside the part's own fields: whether its last turn failed. */
	interface AppMessage extends HelperMessage {
		readonly failed?: boolean;
	}

	let { variant, words }: { variant: string; words: KitWords } = $props();

	const people = ['Anna', 'Bach', 'Clara'];
	const toolCalls = [
		{ name: 'rewrite_section', input: { title: 'Verse 2', foreign: false } },
		{ name: 'add_line', input: { title: 'Bridge of a long-named shared song that does not fit a narrow screen', foreign: true } }
	];
	const conversation: AppMessage[] = [
		{ role: 'user', text: 'Make the second verse shorter.\nKeep the rhyme.' },
		{ role: 'assistant', text: 'I shortened it to four lines.', toolCalls },
		{ role: 'user', text: 'Thanks' },
		{ role: 'assistant', text: 'Anytime.' }
	];
	const longConversation: AppMessage[] = Array.from({ length: 30 }, (_, index) => ({
		role: index % 2 === 0 ? 'user' : 'assistant',
		text: `Message number ${index + 1} of a long conversation`
	}));

	function startingMessages(): AppMessage[] {
		if (variant === 'empty') return [];
		if (variant === 'scroll') return longConversation;
		if (variant === 'running') return [conversation[0], { role: 'assistant', text: '' }];
		if (variant === 'problem') return [conversation[0], { role: 'assistant', text: 'I got as far as', failed: true }];
		return conversation;
	}

	const history: HelperHistory = untrack(() =>
		variant === 'loading'
			? { state: 'loading' }
			: variant === 'failed'
				? { state: 'failed', failure: 'The conversation could not be loaded.' }
				: { state: 'ready' }
	);

	let messages: AppMessage[] = $state(untrack(startingMessages));
	let running = $state(untrack(() => variant === 'running'));
	let draft = $state(untrack(() => (variant === 'draft' ? 'A first line\nA second line' : '')));
	let caret = $state(0);
	let pickIndex = $state(0);
	let tags: string[] = $state([]);
	let list: HTMLElement | undefined = $state();

	const mention = $derived(/@(\w*)$/.exec(draft.slice(0, caret)));
	const candidates = $derived(mention ? people.filter((person) => person.startsWith(mention[1])) : []);

	function report(what: string): void {
		window.reports.push(what);
	}

	function pick(person: string): void {
		const typed = mention![0];
		draft = draft.slice(0, caret - typed.length) + draft.slice(caret);
		tags.push(person);
		report(`pick:${person}`);
	}

	function handleKeydown(event: KeyboardEvent): void {
		if (candidates.length === 0) return;
		if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
			pickIndex = (pickIndex + (event.key === 'ArrowDown' ? 1 : candidates.length - 1)) % candidates.length;
			event.preventDefault();
		} else if (event.key === 'Enter') {
			pick(candidates[pickIndex]);
			event.preventDefault();
		}
	}

	$effect(() => {
		if (variant === 'scroll' && list) list.scrollTop = list.scrollHeight;
	});
</script>

<div class="helper-stage">
	<HelperChat
		{messages}
		{running}
		{history}
		helperName="Mozart"
		emptyHint="Ask Mozart about your song."
		placeholder="Ask for a rewrite…"
		{draft}
		onDraft={(text, position) => {
			draft = text;
			caret = position;
			pickIndex = 0;
		}}
		onSend={(text) => {
			report(`send:${text}`);
			messages.push({ role: 'user', text });
			draft = '';
		}}
		onComposerKeydown={handleKeydown}
		readOnly={variant === 'archived' ? archived : undefined}
		problemLine={problem}
		toolCallTarget={target}
		toolCallTitle={(call) => JSON.stringify(call.input)}
		composerPopup={candidates.length > 0 ? pickList : undefined}
		composerTop={tags.length > 0 ? tagBar : undefined}
		bind:list
		onListScroll={() => report(`scroll:${list!.scrollTop > 0}`)}
		{words}
	/>
	<div class="stub-controls">
		<button type="button" id="grow" onclick={() => (messages[messages.length - 1] = { role: 'assistant', text: 'Here is a shorter verse.' })}>
			Grow
		</button>
		<button type="button" id="finish" onclick={() => (running = false)}>Finish</button>
	</div>
</div>

{#snippet archived()}
	This song is archived. <button type="button" onclick={() => report('restore')}>Restore it</button> to write again.
{/snippet}

{#snippet problem({ message }: { message: AppMessage })}
	{#if message.failed}
		<p class="problem" role="alert">Mozart stopped. <button type="button" onclick={() => report('retry')}>Try again</button></p>
	{/if}
{/snippet}

{#snippet target({ call }: { call: { readonly input: Readonly<Record<string, unknown>> } })}
	<span class="target">in {String(call.input.title)}</span>
	{#if call.input.foreign}<span class="foreign" title="Someone else's song">↗</span>{/if}
{/snippet}

{#snippet pickList()}
	<div class="pick-list" role="listbox" aria-label="People">
		{#each candidates as person, index (person)}
			<button type="button" role="option" aria-selected={index === pickIndex} onclick={() => pick(person)}>{person}</button>
		{/each}
	</div>
{/snippet}

{#snippet tagBar()}
	<div class="tag-bar">
		{#each tags as person (person)}
			<button
				type="button"
				onclick={() => {
					tags = tags.filter((tag) => tag !== person);
					report(`untag:${person}`);
				}}>{person} ×</button
			>
		{/each}
	</div>
{/snippet}

<style>
	.helper-stage {
		display: flex;
		flex-direction: column;
		gap: 8px;
		box-sizing: border-box;
		width: 100%;
		max-width: 480px;
		height: 560px;
		margin: 0 auto;
		padding: 8px;
	}
	.helper-stage :global(.helper-chat) {
		flex: 1 1 auto;
		min-height: 0;
		border: 1px solid var(--border);
	}
	.pick-list {
		position: absolute;
		right: 0;
		bottom: 100%;
		left: 0;
		display: flex;
		flex-direction: column;
		border: 1px solid var(--border);
		background: var(--surface);
	}
	.pick-list [aria-selected='true'] {
		background: var(--surface-hover);
	}
	.tag-bar {
		display: flex;
		flex-wrap: wrap;
		gap: 4px;
	}
	.foreign {
		color: var(--busy);
	}
	.problem {
		margin: 0;
		color: var(--fail);
	}
</style>
