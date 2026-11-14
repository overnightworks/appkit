<script lang="ts">
	import type { TurnOutcome, TurnStateProps } from './types.ts';
	import type { Words as KitWords } from './words/de.ts';

	const wordKeys = {
		not_enabled: 'turnState.notEnabled',
		busy: 'turnState.busy',
		budget_spent: 'turnState.budgetSpent',
		unavailable: 'turnState.unavailable'
	} satisfies Record<TurnOutcome, keyof KitWords>;

	let { outcome, words }: TurnStateProps = $props();
</script>

{#if outcome}
	<span class="turn-state"
		><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 7v6M12 16.5v.5" /></svg
		>{words[wordKeys[outcome]]}</span
	>
{/if}

<style>
	.turn-state {
		display: inline-flex;
		flex: none;
		align-items: center;
		gap: 6px;
		color: var(--text-muted);
		font-family: var(--font-body);
		font-size: 13px;
		white-space: nowrap;
	}
	svg {
		width: 15px;
		height: 15px;
		flex: none;
		fill: none;
		stroke: currentColor;
		stroke-width: 2;
		stroke-linecap: round;
		stroke-linejoin: round;
	}
</style>
