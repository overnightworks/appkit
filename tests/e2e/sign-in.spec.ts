import { expect, test, type Locator } from '@playwright/test';
import type { KitLanguage, KitWords } from 'overnightworks-design';
import { buildConsumer, loadKitWordsUnderNode, origin, routeTo, type ConsumerName } from './build-consumer.ts';
import { resolveStyle } from './probe.ts';

const colorSchemes = ['light', 'dark'] as const;
const widths = [390, 1280] as const;
const languages = ['de', 'en'] as const satisfies readonly KitLanguage[];

for (const consumer of ['imported', 'linked'] as const satisfies ConsumerName[]) {
	test.describe(`a production consumer that ${consumer === 'imported' ? 'imports' : 'statically links'} design.css`, () => {
		let outDir: string;
		let en: KitWords;
		let wordsOf: Record<KitLanguage, KitWords>;
		test.beforeAll(async () => {
			outDir = await buildConsumer(consumer);
			wordsOf = { de: await loadKitWordsUnderNode('de'), en: await loadKitWordsUnderNode('en') };
			en = wordsOf.en;
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

			await page.getByRole('link', { name: en['signIn.logIn'] }).click();
			expect(page.url()).toBe(`${origin}/?on-sign-in`);
			expect(await page.evaluate(() => window.reports)).toEqual(['sign-in']);
			await expect(page.getByRole('link')).toHaveCount(3);
		});

		for (const [name, click, navigatesThisPage] of [
			['a Ctrl-click', (link: Locator) => link.click({ modifiers: ['Control'] }), false],
			['a Meta-click', (link: Locator) => link.click({ modifiers: ['Meta'] }), true],
			['a middle click', (link: Locator) => link.click({ button: 'middle' }), false]
		] as const) {
			test(`leaves ${name} on the sign-in link to the browser`, async ({ page }) => {
				await routeTo(page, outDir);
				await page.goto(`${origin}/?on-sign-in`);

				await click(page.getByRole('link', { name: en['signIn.logIn'] }));
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

		for (const language of languages) {
			for (const width of widths) {
				test(`shows every state in the ${language} words at ${width} px and keeps the page within the viewport`, async ({
					page
				}) => {
					await page.setViewportSize({ width, height: 800 });
					await routeTo(page, outDir);
					const kit = wordsOf[language];
					for (const [variant, heading, action, alert] of [
						['', kit['signIn.loggedOut'], kit['signIn.logIn'], undefined],
						['unfinished', kit['signIn.loggedOut'], kit['signIn.logIn'], kit['signIn.signInUnfinished']],
						['signing-in', kit['signIn.signingIn'], kit['signIn.openInTab'], undefined],
						['window-blocked', kit['signIn.windowBlocked'], kit['signIn.openInTab'], undefined],
						['login-failed', kit['signIn.loginFailed'], kit['signIn.tryAgain'], kit['signIn.loginFailedBanner']],
						['no-access', kit['signIn.noAccess'], kit['signIn.logOut'], undefined]
					] as const) {
						await page.goto(`${origin}/?${variant}&lang=${language}`);
						const card = page.getByRole('main');
						await expect(card.getByRole('heading')).toHaveText(heading);
						await expect(card.getByRole('link').or(card.getByRole('button'))).toHaveText(action);
						if (alert) await expect(card.getByRole('alert')).toHaveText(alert);
						else await expect(card.getByRole('alert')).toHaveCount(0);
						if (variant === 'no-access') {
							await expect(card.getByText(kit['signIn.noAccessSentence']({ appName: 'Probe' }))).toBeVisible();
						}
						expect(
							await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)
						).toBe(true);
					}
				});
			}
		}

		for (const width of widths) {
			for (const colorScheme of colorSchemes) {
				for (const variant of ['signing-in', 'window-blocked', 'unfinished']) {
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
						} else if (variant === 'window-blocked') {
							await expect(card.getByRole('link')).toBeVisible();
							await expect(card.locator('i')).toHaveCount(0);
							await expect(card.getByRole('alert')).toHaveCount(0);
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
