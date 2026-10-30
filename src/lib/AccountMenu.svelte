<script lang="ts">
	import { flushSync } from 'svelte';
	import LegalLinks from './LegalLinks.svelte';
	import type { AccountMenuProps, ThemeChoice } from './types.ts';

	let {
		name,
		accountHref,
		onAccountOpen,
		appRows,
		theme,
		legalLinks,
		onLogOut,
		logOutFailure,
		logOutAction
	}: AccountMenuProps = $props();

	const group = $props.id();
	const choices: readonly { value: ThemeChoice; label: string }[] = [
		{ value: 'follow-system', label: 'Follow system' },
		{ value: 'light', label: 'Light' },
		{ value: 'dark', label: 'Dark' }
	];
	let radios: HTMLInputElement[] = [];

	// The radios are controlled: once the app's update settles, the checked one equals theme.choice.
	function report(choice: ThemeChoice): void {
		theme?.onChange(choice);
		flushSync();
		radios.forEach((radio, index) => {
			// The app's update may have removed the rows or unmounted the menu.
			if (radio) radio.checked = choices[index].value === theme?.choice;
		});
	}
</script>

{#snippet logOutRow(type: 'button' | 'submit')}
	<button class="row" {type} onclick={type === 'button' ? onLogOut : undefined}>
		<svg viewBox="0 0 24 24" aria-hidden="true"
			><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><path d="m16 17 5-5-5-5" /><path
				d="M21 12H9"
			/></svg
		>Log out
	</button>
{/snippet}

<div class="menu">
	<a class="row name" href={accountHref} target="_blank" rel="noopener noreferrer" onclick={onAccountOpen}>
		<span class="grow as-typed">{name}</span>
		<svg viewBox="0 0 24 24" aria-hidden="true"
			><path d="M15 3h6v6" /><path d="M10 14 21 3" /><path
				d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"
			/></svg
		>
	</a>
	{#each appRows as row, index (index)}
		<button class="row" type="button" onclick={row.onSelect}>
			<!-- AppRowIcon has one member; a second icon turns this into a lookup. -->
			<svg viewBox="0 0 24 24" aria-hidden="true"
				><circle cx="12" cy="12" r="3" /><path
					d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"
				/></svg
			>{row.label}
		</button>
	{/each}
	{#if theme}
		<div class="row" id="{group}-theme">
			<svg viewBox="0 0 24 24" aria-hidden="true"
				><circle cx="12" cy="12" r="9" /><path d="M12 3v18" /><path
					d="M12 3a9 9 0 0 1 0 18"
					fill="currentColor"
				/></svg
			>Theme
		</div>
		<div role="radiogroup" aria-labelledby="{group}-theme">
			{#each choices as choice, index (choice.value)}
				<label class="row sub">
					<input
						bind:this={radios[index]}
						type="radio"
						name={group}
						value={choice.value}
						checked={theme.choice === choice.value}
						onchange={() => report(choice.value)}
					/>{choice.label}
				</label>
			{/each}
		</div>
	{/if}
	<div class="out">
		{#if logOutAction !== undefined}
			<form method="post" action={logOutAction}>{@render logOutRow('submit')}</form>
		{:else}
			{@render logOutRow('button')}
			{#if logOutFailure}
				<p role="alert">{logOutFailure}</p>
			{/if}
		{/if}
	</div>
	<LegalLinks links={legalLinks} place="menu" />
</div>

<style>
	.menu {
		width: 256px;
		max-width: 100%;
		box-sizing: border-box;
		padding: 4px 0;
		background: var(--surface);
		color: var(--text);
		border: 1px solid var(--border);
		border-radius: 6px;
		box-shadow: 0 6px 24px rgba(0, 0, 0, 0.14);
		font-family: 'Open Sans', system-ui, sans-serif;
		font-size: 14px;
	}
	.row {
		display: flex;
		align-items: center;
		gap: 10px;
		box-sizing: border-box;
		width: 100%;
		min-height: 40px;
		margin: 0;
		padding: 0 14px;
		border: none;
		background: none;
		color: inherit;
		font: inherit;
		text-align: left;
		text-decoration: none;
	}
	a.row,
	button.row,
	label.row {
		cursor: pointer;
	}
	a.row:hover,
	button.row:hover,
	label.row:hover {
		background: var(--surface-hover);
	}
	.row svg {
		width: 16px;
		height: 16px;
		flex: none;
		fill: none;
		stroke: currentColor;
		stroke-width: 2;
		stroke-linecap: round;
		stroke-linejoin: round;
		color: var(--text-muted);
	}
	.row:focus-visible,
	input:focus-visible {
		outline: 2px solid var(--accent);
		outline-offset: -2px;
	}
	.name {
		min-height: 48px;
		font-weight: 600;
	}
	.grow {
		flex: 1;
		min-width: 0;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
	.sub {
		min-height: 34px;
		padding-left: 40px;
	}
	input[type='radio'] {
		appearance: none;
		width: 16px;
		height: 16px;
		flex: none;
		margin: 0;
		border: 2px solid var(--text-muted);
		border-radius: 50%;
		background: transparent;
	}
	input[type='radio']:focus-visible {
		outline-offset: 2px;
	}
	input[type='radio']:checked {
		border-color: var(--accent);
		background: radial-gradient(circle, var(--accent) 0 3.5px, transparent 4.5px);
	}
	.out {
		margin-top: 4px;
		padding-top: 4px;
		border-top: 1px solid var(--border);
	}
	.out .row {
		/* 40px row height minus the wrapper's 4px padding and 1px border. */
		min-height: 35px;
	}
	form {
		margin: 0;
	}
	p {
		margin: 0;
		padding: 6px 14px;
		color: var(--fail);
		font-size: 13px;
		overflow-wrap: anywhere;
	}
</style>
