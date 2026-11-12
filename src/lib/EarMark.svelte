<script lang="ts">
	import type { EarMarkProps } from './types.ts';

	let { agent, person, words }: EarMarkProps = $props();

	const name = $derived(
		person === undefined
			? words['hearing.agentHearsYou']({ agent })
			: words['hearing.agentHearsPerson']({ agent, name: person })
	);
</script>

<span class="ear-mark" role="img" aria-label={name} title={name}>
	<span class="disc">
		<svg viewBox="0 0 24 24" aria-hidden="true">
			<path d="M6 10a6 6 0 1 1 12 0c0 3.2-3 4-3 7a3 3 0 0 1-6 0" />
			<path d="M9.5 10a2.5 2.5 0 0 1 5 0" />
		</svg>
	</span>
	<span class="pill">{agent}</span>
</span>

<style>
	.ear-mark {
		display: flex;
		align-items: center;
		gap: 6px;
		width: fit-content;
		max-width: 100%;
	}
	.disc,
	.pill {
		background: rgba(12, 14, 17, 0.55);
		/* The standard property comes last: lightningcss keeps only the last of the pair. */
		-webkit-backdrop-filter: blur(12px);
		backdrop-filter: blur(12px);
	}
	.disc {
		display: grid;
		place-items: center;
		flex: none;
		width: 30px;
		height: 30px;
		border-radius: 50%;
		color: var(--accent);
		box-shadow: inset 0 0 0 1.5px var(--accent);
	}
	.disc svg {
		width: 18px;
		height: 18px;
		fill: none;
		stroke: currentColor;
		stroke-width: 2;
		stroke-linecap: round;
		stroke-linejoin: round;
	}
	.pill {
		min-width: 0;
		overflow: hidden;
		padding: 0 10px;
		border-radius: 999px;
		color: #f4f6f8;
		font-family: var(--font-body);
		font-size: 12.5px;
		font-weight: 600;
		line-height: 22px;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
</style>
