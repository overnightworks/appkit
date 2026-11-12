import { expect, test } from '@playwright/test';
import { buildConsumer, origin, routeTo, type ConsumerName } from './build-consumer.ts';

const widths = [390, 1280] as const;
const sentence =
	'Retire 3 takes of this recording; read the full retention rules for recordings before you confirm.';
const linkName = 'the full retention rules for recordings';

for (const consumer of ['imported', 'linked'] as const satisfies ConsumerName[]) {
	test.describe(`a marked sentence in a production consumer that ${consumer === 'imported' ? 'imports' : 'statically links'} design.css`, () => {
		let outDir: string;
		test.beforeAll(async () => {
			outDir = await buildConsumer(consumer);
		});

		for (const width of widths) {
			test(`reads as running text with a reachable link at ${width} px`, async ({ page }) => {
				await page.setViewportSize({ width, height: 800 });
				await routeTo(page.context(), outDir);
				await page.goto(`${origin}/?marked`);

				const paragraph = page.locator('#sentence');
				expect(await paragraph.evaluate((node) => node.textContent)).toBe(sentence);
				await expect(paragraph.locator('strong')).toHaveText('3 takes');

				const link = page.getByRole('link', { name: linkName });
				await expect(link).toHaveAttribute('href', '/retention');
				await page.keyboard.press('Tab');
				await expect(link).toBeFocused();

				const layout = await paragraph.evaluate((node) => {
					const box = node.getBoundingClientRect();
					const inline = [...node.children].map((child) => getComputedStyle(child).display);
					return {
						inline,
						linkLines: node.querySelector('a')!.getClientRects().length,
						overflowsPage: document.documentElement.scrollWidth > document.documentElement.clientWidth,
						right: box.right,
						viewport: document.documentElement.clientWidth
					};
				});
				expect(layout.inline).toEqual(['inline', 'inline']);
				expect(layout.overflowsPage).toBe(false);
				expect(layout.right).toBeLessThanOrEqual(layout.viewport);
				if (width === widths[0]) expect(layout.linkLines).toBeGreaterThan(1);
			});
		}
	});
}
