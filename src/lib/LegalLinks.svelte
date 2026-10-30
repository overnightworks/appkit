<script lang="ts">
	import type { LegalLinksProps } from './types.ts';

	let { links }: LegalLinksProps = $props();
</script>

{#if links.length > 0}
	<nav class="legal">
		{#each links as link, index (index)}
			<a href={link.href}>{link.label}</a>
		{/each}
	</nav>
{/if}

<style>
	.legal {
		position: relative;
		z-index: 1;
		display: flex;
		flex-wrap: wrap;
		justify-content: center;
		gap: 4px 16px;
		font-size: 12px;
	}
	.legal a {
		color: var(--text-muted);
		text-decoration: none;
		border-bottom: 1px solid var(--border);
	}
</style>
