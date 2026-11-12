<script lang="ts">
	import type { LegalLinksProps } from './types.ts';

	let { links, words, place = 'page', newTab = false }: LegalLinksProps = $props();
	const inMenu = $derived(place === 'menu');
	const opensNewTab = $derived(inMenu || newTab);
</script>

{#if links.length > 0}
	<nav class="legal" class:menu={inMenu} aria-label={words['legalLinks.name']}>
		{#each links as link, index (index)}
			<a
				href={link.href}
				target={opensNewTab ? '_blank' : undefined}
				rel={opensNewTab ? 'noopener' : undefined}>{link.label}</a
			>
		{/each}
	</nav>
{/if}
