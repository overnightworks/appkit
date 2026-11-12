<script lang="ts">
	import AiMark from './AiMark.svelte';
	import type { AgentControlProps, AgentControlRefusal } from './types.ts';
	import type { Words as KitWords } from './words/de.ts';

	const refusalKeys = {
		'not-allowed': 'agent.notAllowed',
		'owner-absent': 'agent.ownerAbsent',
		'place-full': 'agent.placeFull',
		'agent-unavailable': 'agent.agentUnavailable',
		'try-again': 'agent.tryAgain'
	} satisfies Record<AgentControlRefusal, keyof KitWords>;

	let { rows, onCall, onSendAway, refusal, words }: AgentControlProps = $props();
</script>

<div class="agent-control">
	{#if refusal}
		<div class="banner" role="alert">
			<span class="fail-shape"><i></i></span>
			<span>{words[refusalKeys[refusal]]}</span>
		</div>
	{/if}
	{#if rows.length === 0}
		<p class="empty">{words['agent.empty']}</p>
	{:else}
		<ul>
			{#each rows as row (row.key)}
				<li class="agent">
					<AiMark />
					<span class="name">{row.name}</span>
					{#if row.state === 'available'}
						<button
							class="act"
							type="button"
							aria-label={words['agent.callLabel']({ name: row.name })}
							onclick={() => onCall(row.key)}
						>
							<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14" /></svg>{words['agent.call']}
						</button>
					{:else if row.state === 'inviting'}
						<span class="pending" role="status">
							<span class="dots" aria-hidden="true"><i></i><i></i><i></i></span>{words['agent.calling']}
						</span>
					{:else if onSendAway}
						{@const sendAway = onSendAway}
						<button
							class="act"
							type="button"
							aria-label={words['agent.askToLeaveLabel']({ name: row.name })}
							onclick={() => sendAway(row.key)}
						>
							<svg viewBox="0 0 24 24" aria-hidden="true"
								><path d="M14 4h4a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-4M9 16l-4-4 4-4M5 12h10" /></svg
							>{words['agent.askToLeave']}
						</button>
					{/if}
				</li>
			{/each}
		</ul>
	{/if}
</div>

<style>
	.agent-control {
		padding-bottom: 4px;
		color: var(--text);
		font-family: var(--font-body);
		font-size: 14px;
	}
	ul {
		margin: 0;
		padding: 0;
		list-style-type: none;
	}
	.agent {
		display: flex;
		align-items: center;
		gap: 10px;
		min-height: 40px;
		padding: 0 8px 0 14px;
	}
	.agent > :global(.ai-mark) {
		color: var(--text-muted);
	}
	.name {
		flex: 1;
		min-width: 0;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
	.act {
		position: relative;
		display: inline-flex;
		align-items: center;
		gap: 6px;
		min-height: 32px;
		padding: 0 12px 0 10px;
		border: 1px solid var(--border);
		border-radius: 999px;
		background: transparent;
		color: var(--text);
		font: inherit;
		font-size: 13px;
		font-weight: 600;
		white-space: nowrap;
		cursor: pointer;
	}
	.act svg {
		width: 15px;
		height: 15px;
		flex: none;
		fill: none;
		stroke: currentColor;
		stroke-width: 2;
		stroke-linecap: round;
		stroke-linejoin: round;
		color: var(--text-muted);
	}
	.act:hover {
		background: var(--surface-hover);
	}
	.act:focus-visible {
		outline: 2px solid currentColor;
		outline-offset: 2px;
	}
	.pending {
		display: inline-flex;
		align-items: center;
		gap: 8px;
		padding-right: 6px;
		color: var(--text-muted);
		font-size: 13px;
		white-space: nowrap;
	}
	.dots {
		display: inline-flex;
		align-items: center;
		gap: 4px;
	}
	.dots i {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		background: currentColor;
		opacity: 0.6;
	}
	@media (prefers-reduced-motion: no-preference) {
		.dots i {
			animation: hop 1.2s ease-in-out infinite;
		}
		.dots i:nth-child(2) {
			animation-delay: 0.12s;
		}
		.dots i:nth-child(3) {
			animation-delay: 0.24s;
		}
	}
	@keyframes hop {
		0%,
		60%,
		100% {
			translate: 0 0;
			opacity: 0.45;
		}
		30% {
			translate: 0 -5px;
			opacity: 1;
		}
	}
	.banner {
		display: flex;
		gap: 10px;
		align-items: flex-start;
		margin: 6px 14px 4px;
		padding: 10px 12px;
		border: 1px solid var(--fail);
		border-left-width: 3px;
		border-radius: 4px;
		background: var(--fail-soft);
		font-size: 13.5px;
		text-align: left;
		color: var(--text);
	}
	.fail-shape {
		margin-top: 3px;
		display: inline-flex;
		color: var(--fail);
	}
	.fail-shape i {
		width: 12px;
		height: 12px;
		flex: none;
		display: inline-block;
		background: var(--fail);
		clip-path: polygon(50% 0%, 100% 100%, 0% 100%);
	}
	.empty {
		margin: 0;
		padding: 10px 14px 12px;
		color: var(--text-muted);
		font-size: 13.5px;
		line-height: 1.4;
	}
	@media (any-pointer: coarse) {
		.agent {
			min-height: 44px;
		}
		.act::after {
			content: '';
			position: absolute;
			inset: -6px -2px;
		}
	}
</style>
