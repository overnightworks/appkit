<script lang="ts" module>
	type Parts = readonly (string | { readonly marker: 'strong' | 'link'; readonly text: string })[];

	/** Sentences as a generated entry returns them, with the text and the elements a page shows for them. */
	export const sentences: { parts: Parts; text: string; elements: string[] }[] = [
		{ parts: [], text: '', elements: [] },
		{ parts: ['Nur Text'], text: 'Nur Text', elements: [] },
		{
			parts: ['Nur ', { marker: 'strong', text: 'wichtig' }, ' hier'],
			text: 'Nur wichtig hier',
			elements: ['strong:wichtig']
		},
		{
			parts: [{ marker: 'strong', text: 'a' }, { marker: 'link', text: 'b' }],
			text: 'ab',
			elements: ['strong:a', 'a:b']
		},
		{
			parts: ['  eins ', { marker: 'link', text: ' zwei ' }, ' drei  '],
			text: '  eins  zwei  drei  ',
			elements: ['a: zwei ']
		},
		{
			parts: ['Wert <b>x</b> ', { marker: 'strong', text: '<i>{#strong}y{/strong}</i> & {z}' }],
			text: 'Wert <b>x</b> <i>{#strong}y{/strong}</i> & {z}',
			elements: ['strong:<i>{#strong}y{/strong}</i> & {z}']
		}
	];
</script>

<script lang="ts">
	import Marked from './Marked.svelte';

	let { parts }: { parts: Parts } = $props();
</script>

{#snippet strong(text: string)}<strong>{text}</strong>{/snippet}
{#snippet link(text: string)}<a href="/more">{text}</a>{/snippet}

<p><Marked {parts} marked={{ strong, link }} /></p>
