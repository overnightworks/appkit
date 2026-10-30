import { join, normalize, sep } from 'node:path';
import { existsSync, statSync } from 'node:fs';
import { expect, test, type Page } from '@playwright/test';
import { buildConsumer, type ConsumerName } from './build-consumer.ts';

const origin = 'http://consumer.test';
const colorSchemes = ['light', 'dark'] as const;

/** Serves a built consumer through request routing, so no server process exists. */
async function routeTo(page: Page, outDir: string): Promise<void> {
	await page.route(`${origin}/**`, async (route) => {
		const { pathname } = new URL(route.request().url());
		const file = normalize(join(outDir, pathname === '/' ? 'index.html' : pathname));
		if (!file.startsWith(outDir + sep) || !existsSync(file) || !statSync(file).isFile()) {
			return route.fulfill({ status: 404 });
		}
		return route.fulfill({ path: file });
	});
}

for (const consumer of ['imported', 'linked'] as const satisfies ConsumerName[]) {
	test.describe(`a production consumer that ${consumer === 'imported' ? 'imports' : 'statically links'} appkit.css`, () => {
		let outDir: string;
		test.beforeAll(async () => {
			outDir = await buildConsumer(consumer);
		});

		for (const colorScheme of colorSchemes) {
			test(`paints the sign-in grid, glows and legal row in ${colorScheme}`, async ({ page }) => {
				await page.emulateMedia({ colorScheme });
				await routeTo(page, outDir);
				await page.goto(`${origin}/`);

				const card = page.getByRole('main');
				await expect(card.getByRole('heading')).toBeVisible();

				// No class names are read: the layers are the card's three earlier siblings (grid, then two
				// glows), so a decorative layer added to or removed from SignInPage must update this count.
				const layers = card.locator('xpath=preceding-sibling::*');
				await expect(layers).toHaveCount(3);
				const [grid, ...glows] = await layers.all();
				await expect(grid).toHaveCSS('background-image', /gradient/);
				for (const glow of glows) {
					await expect(glow).toBeVisible();
					await expect(glow).not.toHaveCSS('background-color', 'rgba(0, 0, 0, 0)');
				}

				const viewport = page.viewportSize()!;
				for (const name of ['Imprint', 'Privacy']) {
					const link = page.getByRole('link', { name });
					await expect(link).toBeVisible();
					const box = (await link.boundingBox())!;
					expect(box.x).toBeGreaterThanOrEqual(0);
					expect(box.y).toBeGreaterThanOrEqual(0);
					expect(box.x + box.width).toBeLessThanOrEqual(viewport.width);
					expect(box.y + box.height).toBeLessThanOrEqual(viewport.height);
				}
			});
		}

		test('keeps the case of typed text in an uppercase heading', async ({ page }) => {
			await routeTo(page, outDir);
			await page.goto(`${origin}/?typed`);

			const heading = page.getByRole('heading', { level: 1 });
			const typed = heading.locator('.as-typed');
			await expect(typed).toHaveCSS('text-transform', 'none');
			expect(await typed.innerText()).toBe('talks');
			expect(await heading.innerText()).toBe('SOURCE talks');
		});
	});
}
