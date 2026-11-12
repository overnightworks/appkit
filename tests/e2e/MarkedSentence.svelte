<script lang="ts">
	import { Marked } from 'overnightworks-design';

	/** What an app's generated entry returns for "Retire {#strong}3 takes{/strong} of this recording; read {#link}the full retention rules for recordings{/link} before you confirm." */
	const parts: readonly (string | { readonly marker: 'strong' | 'link'; readonly text: string })[] = [
		'Retire ',
		{ marker: 'strong', text: '3 takes' },
		' of this recording; read ',
		{ marker: 'link', text: 'the full retention rules for recordings' },
		' before you confirm.'
	];
</script>

{#snippet strong(text: string)}<strong>{text}</strong>{/snippet}
{#snippet link(text: string)}<a href="/retention">{text}</a>{/snippet}

<main>
	<p id="sentence"><Marked {parts} marked={{ strong, link }} /></p>
</main>
