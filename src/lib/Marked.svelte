<script lang="ts" generics="Marker extends string">
	import type { MarkedProps } from './types.ts';

	let { parts, marked }: MarkedProps<Marker> = $props();
</script>

{#each parts as part, index (index)}{#if typeof part === 'string'}{part}{:else}{@render marked[part.marker](part)}{/if}{/each}
