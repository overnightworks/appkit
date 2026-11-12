<script lang="ts">
	import type { HearingKind, HearingSwitchProps } from './types.ts';
	import type { Words as KitWords } from './words/de.ts';

	const labelKeys = {
		hear: 'hearing.agentMayHearMe',
		listen: 'hearing.iWantToHearAgent'
	} satisfies Record<HearingKind, keyof KitWords>;

	let { kind, on, onChange, words }: HearingSwitchProps = $props();
</script>

<button class="hearing-switch" type="button" role="switch" aria-checked={on} onclick={() => onChange(!on)}>
	<span class="icon">
		<svg viewBox="0 0 24 24" aria-hidden="true">
			{#if kind === 'hear'}
				<path d="M6 10a6 6 0 1 1 12 0c0 3.2-3 4-3 7a3 3 0 0 1-6 0" />
				<path d="M9.5 10a2.5 2.5 0 0 1 5 0" />
				{#if !on}<path d="M4 4l16 16" />{/if}
			{:else}
				<path d="M4 9.5h3l4.5-3.7v12.4L7 14.5H4z" />
				{#if on}
					<path d="M15.5 9a4.2 4.2 0 0 1 0 6M18 6.5a7.6 7.6 0 0 1 0 11" />
				{:else}
					<path d="M15.5 9.5l5 5M20.5 9.5l-5 5" />
				{/if}
			{/if}
		</svg>
	</span>
	<span class="label">{words[labelKeys[kind]]}</span>
	<span class="track" aria-hidden="true"></span>
</button>

<style>
	.hearing-switch {
		position: relative;
		display: inline-flex;
		align-items: center;
		gap: 8px;
		max-width: 100%;
		height: 28px;
		padding: 0 5px 0 10px;
		border: 0;
		border-radius: 999px;
		background: rgba(12, 14, 17, 0.55);
		color: #f4f6f8;
		font-family: var(--font-body);
		font-size: 12.5px;
		font-weight: 600;
		white-space: nowrap;
		cursor: pointer;
		backdrop-filter: blur(12px);
		-webkit-backdrop-filter: blur(12px);
	}
	.hearing-switch:hover {
		background: rgba(255, 255, 255, 0.15);
	}
	.hearing-switch:focus-visible {
		outline: 2.5px solid var(--accent);
		outline-offset: 2px;
	}
	.icon {
		display: inline-flex;
		color: rgba(244, 246, 248, 0.72);
	}
	.icon svg {
		width: 16px;
		height: 16px;
		fill: none;
		stroke: currentColor;
		stroke-width: 2;
		stroke-linecap: round;
		stroke-linejoin: round;
	}
	.label {
		overflow: hidden;
		text-overflow: ellipsis;
		color: rgba(244, 246, 248, 0.72);
	}
	.track {
		position: relative;
		flex: none;
		width: 34px;
		height: 20px;
		border-radius: 999px;
		background: rgba(255, 255, 255, 0.15);
	}
	.track::after {
		content: '';
		position: absolute;
		top: 3px;
		left: 3px;
		width: 14px;
		height: 14px;
		border-radius: 50%;
		background: #f4f6f8;
	}
	.hearing-switch[aria-checked='true'] .icon {
		color: var(--accent);
	}
	.hearing-switch[aria-checked='true'] .label {
		color: inherit;
	}
	.hearing-switch[aria-checked='true'] .track {
		background: var(--accent);
	}
	.hearing-switch[aria-checked='true'] .track::after {
		transform: translateX(14px);
		background: #0d1013;
	}
	@media (prefers-reduced-motion: no-preference) {
		.track {
			transition: background 0.2s;
		}
		.track::after {
			transition: transform 0.2s;
		}
	}
	@media (any-pointer: coarse) {
		.hearing-switch::after {
			content: '';
			position: absolute;
			inset: -8px -4px;
		}
	}
</style>
