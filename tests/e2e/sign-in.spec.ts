import { expect, test, type Locator } from '@playwright/test';
import { buildConsumer, origin, routeTo, type ConsumerName } from './build-consumer.ts';
import { resolveStyle } from './probe.ts';

const colorSchemes = ['light', 'dark'] as const;

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

		test('starts the app\'s own sign-in on a plain click and does not navigate', async ({ page }) => {
			await routeTo(page, outDir);
			await page.goto(`${origin}/?on-sign-in`);

			await page.getByRole('link', { name: 'Log in' }).click();
			expect(page.url()).toBe(`${origin}/?on-sign-in`);
			expect(await page.evaluate(() => window.reports)).toEqual(['sign-in']);
			await expect(page.getByRole('link')).toHaveCount(3);
		});

		for (const [name, click, navigatesThisPage] of [
			['a Ctrl-click', (link: Locator) => link.click({ modifiers: ['Control'] }), false],
			['a Meta-click', (link: Locator) => link.click({ modifiers: ['Meta'] }), true],
			['a middle click', (link: Locator) => link.click({ button: 'middle' }), false]
		] as const) {
			test(`leaves ${name} on Log in to the browser`, async ({ page }) => {
				await routeTo(page, outDir);
				await page.goto(`${origin}/?on-sign-in`);

				await click(page.getByRole('link', { name: 'Log in' }));
				// Meta on Linux is no new-tab modifier: the browser follows the link in this page.
				if (navigatesThisPage) await expect(page).toHaveURL(`${origin}/login`);
				expect((await page.evaluate(() => window.reports)) ?? []).toEqual([]);
			});
		}

		test('keeps the dots of the waiting shape still under reduced motion and moves them otherwise', async ({
			page
		}) => {
			await routeTo(page, outDir);
			await page.goto(`${origin}/?signing-in`);
			const dot = page.locator('main i').first();
			await page.emulateMedia({ reducedMotion: 'no-preference' });
			await expect(dot).not.toHaveCSS('animation-name', 'none');
			await page.emulateMedia({ reducedMotion: 'reduce' });
			await expect(dot).toHaveCSS('animation-name', 'none');
		});

		for (const width of [390, 1280]) {
			for (const colorScheme of colorSchemes) {
				for (const variant of ['signing-in', 'unfinished']) {
					test(`fits the ${variant} card at ${width} px in ${colorScheme}`, async ({ page }) => {
						await page.setViewportSize({ width, height: 800 });
						await page.emulateMedia({ colorScheme });
						await routeTo(page, outDir);
						await page.goto(`${origin}/?${variant}`);

						const card = page.getByRole('main');
						await expect(card.getByRole('heading')).toBeVisible();
						const box = (await card.boundingBox())!;
						expect(box.x).toBeGreaterThanOrEqual(0);
						expect(box.x + box.width).toBeLessThanOrEqual(width);
						expect(
							await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)
						).toBe(true);
						if (variant === 'signing-in') {
							await expect(card.locator('svg').first()).toBeVisible();
							await expect(card.locator('i').first()).toBeVisible();
						} else {
							await expect(card.getByRole('alert')).toBeVisible();
						}
					});
				}
			}
		}

		test('names the app once in the card for screen readers', async ({ page }) => {
			await routeTo(page, outDir);
			await page.goto(`${origin}/`);

			const snapshot = await page.getByRole('main').ariaSnapshot();
			expect(snapshot.match(/Probe/gi)).toHaveLength(1);
		});

		test('takes its display and body fonts from the family tokens', async ({ page }) => {
			await routeTo(page, outDir);
			await page.goto(`${origin}/`);

			const card = page.getByRole('main');
			const { 'font-family': display } = await resolveStyle(
				page,
				{ 'font-family': 'var(--font-display)' },
				['font-family']
			);
			const { 'font-family': body } = await resolveStyle(page, { 'font-family': 'var(--font-body)' }, [
				'font-family'
			]);
			await expect(card.getByRole('heading')).toBeVisible();
			await expect(card.getByText('Probe').first()).toHaveCSS('font-family', display);
			await expect(card.getByRole('link')).toHaveCSS('font-family', display);
			await expect(card).toHaveCSS('font-family', body);
		});

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
