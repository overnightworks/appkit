import { mount, tick, unmount } from 'svelte';
import { afterEach, describe, expect, it } from 'vitest';
import AiMark from './AiMark.svelte';

const mounted: { target: HTMLElement; component: ReturnType<typeof mount> }[] = [];

async function render(props: Record<string, string> = {}, place?: HTMLElement): Promise<HTMLElement> {
	const target = place ?? document.createElement('div');
	if (!place) document.body.append(target);
	mounted.push({ target, component: mount(AiMark, { target, props }) });
	await tick();
	return target;
}

afterEach(async () => {
	for (const { target, component } of mounted.splice(0)) {
		await unmount(component);
		target.remove();
	}
});

describe('AiMark', () => {
	it.each<Record<string, string>>([{}, { text: 'Agent', label: 'KI' }])(
		'renders the text AI and nothing else, whatever props a caller passes (%o)',
		async (props) => {
			const page = await render(props);
			expect(page.textContent).toBe('AI');
		},
	);

	it('leaves its text visible to assistive technology', async () => {
		const page = await render();
		expect(page.querySelector('[aria-hidden]')).toBeNull();
	});

	it('outlines itself in the colour of its place', async () => {
		const place = document.createElement('div');
		place.style.color = 'rgb(10, 20, 30)';
		document.body.append(place);
		const page = await render({}, place);
		const mark = page.querySelector('span')!;
		expect(getComputedStyle(mark).borderTopColor).toBe('rgb(10, 20, 30)');
	});
});
