<script lang="ts">
	import type { HearingKind, HearingSwitchProps } from './types.ts';
	import type { Words as KitWords } from './words/de.ts';

	const labelKeys = {
		hear: 'hearing.agentMayHearMe',
		listen: 'hearing.iWantToHearAgent',
		see: 'hearing.seeShort'
	} satisfies Record<HearingKind, keyof KitWords>;

	let { kind, on, onChange, words, compact = false }: HearingSwitchProps = $props();
</script>

<button
	class="hearing-switch"
	class:compact
	type="button"
	role="switch"
	aria-checked={on}
	aria-label={kind === 'see' ? words['hearing.agentMaySeeMe'] : undefined}
	onclick={() => onChange(!on)}
>
	<span class="icon">
		<svg viewBox="0 0 24 24" aria-hidden="true">
			{#if kind === 'hear'}
				<path d="M6 10a6 6 0 1 1 12 0c0 3.2-3 4-3 7a3 3 0 0 1-6 0" />
				<path d="M9.5 10a2.5 2.5 0 0 1 5 0" />
				{#if !on}<path d="M4 4l16 16" />{/if}
			{:else if kind === 'see'}
				<path d="M2 12s3.6-6.5 10-6.5S22 12 22 12s-3.6 6.5-10 6.5S2 12 2 12z" />
				<circle cx="12" cy="12" r="2.8" />
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
		min-width: 0;
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
		/* The standard property comes last: lightningcss keeps only the last of the pair. */
		-webkit-backdrop-filter: blur(12px);
		backdrop-filter: blur(12px);
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
	.compact {
		flex: none;
		width: 26px;
		padding: 0;
		gap: 0;
		justify-content: center;
	}
	.compact .track {
		width: 26px;
	}
	.compact[aria-checked='true'] .track::after {
		transform: translateX(6px);
	}
	.compact .icon {
		position: absolute;
		top: 50%;
		left: 4px;
		z-index: 1;
		margin-top: -6px;
		color: #0d1013;
		pointer-events: none;
	}
	.compact .icon svg {
		width: 12px;
		height: 12px;
	}
	.compact[aria-checked='true'] .icon {
		transform: translateX(6px);
	}
	.compact .label {
		position: absolute;
		width: 1px;
		height: 1px;
		clip-path: inset(50%);
	}
	@media (any-pointer: coarse) {
		.hearing-switch::before {
			content: '';
			position: absolute;
			top: 50%;
			left: 50%;
			width: max(100%, 44px);
			height: 44px;
			transform: translate(-50%, -50%);
		}
	}
	@media (prefers-reduced-motion: no-preference) {
		.compact .icon {
			transition: transform 0.2s;
		}
		.track {
			transition: background 0.2s;
		}
		.track::after {
			transition: transform 0.2s;
		}
	}
</style>
