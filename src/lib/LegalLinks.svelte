<script lang="ts">
	import type { LegalLinksProps } from './types.ts';

	let { links, place = 'page', newTab = false }: LegalLinksProps = $props();
	const inMenu = $derived(place === 'menu');
	const opensNewTab = $derived(inMenu || newTab);
</script>

{#if links.length > 0}
	<nav class="legal" class:menu={inMenu} aria-label="Legal">
		{#each links as link, index (index)}
			<a
				href={link.href}
				target={opensNewTab ? '_blank' : undefined}
				rel={opensNewTab ? 'noopener' : undefined}>{link.label}</a
			>
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
	.legal.menu {
		justify-content: flex-start;
		gap: 2px 12px;
		padding: 8px 14px 6px;
		border-top: 1px solid var(--border);
		font-size: 11.5px;
	}
	.legal.menu a {
		border-bottom: none;
	}
</style>
