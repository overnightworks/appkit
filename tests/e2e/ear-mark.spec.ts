import { expect, test, type Locator, type Page } from '@playwright/test';
import type { KitLanguage, KitWords } from 'overnightworks-design';
import { buildConsumer, loadKitWordsUnderNode, origin, routeTo, type ConsumerName } from './build-consumer.ts';
import { resolveStyle } from './probe.ts';

const colorSchemes = ['light', 'dark'] as const;
const widths = [390, 1280] as const;
const languages = ['de', 'en'] as const satisfies readonly KitLanguage[];

const pillOf = (mark: Locator) => mark.locator('span').last();
const discOf = (mark: Locator) => mark.locator('span').first();

for (const consumer of ['imported', 'linked'] as const satisfies ConsumerName[]) {
	test.describe(`the ear mark in a production consumer that ${consumer === 'imported' ? 'imports' : 'statically links'} design.css`, () => {
		let outDir: string;
		let wordsOf: Record<KitLanguage, KitWords>;
		test.beforeAll(async () => {
			outDir = await buildConsumer(consumer);
			wordsOf = { de: await loadKitWordsUnderNode('de'), en: await loadKitWordsUnderNode('en') };
		});

		async function open(page: Page, variant: string, language: KitLanguage = 'en'): Promise<void> {
			await routeTo(page.context(), outDir);
			await page.goto(`${origin}/?ear=${variant}${language === 'en' ? '' : `&lang=${language}`}`);
			await expect(page.getByRole('img').first()).toBeVisible();
		}

		test('blurs the video behind the disc and the pill, so the built CSS keeps the standard backdrop-filter', async ({
			page
		}) => {
			await open(page, 'one');
			const mark = page.getByRole('img');
			await expect(discOf(mark)).not.toHaveCSS('backdrop-filter', 'none');
			await expect(pillOf(mark)).not.toHaveCSS('backdrop-filter', 'none');
		});

		for (const colorScheme of colorSchemes) {
			for (const width of widths) {
				test(`draws a round disc ringed in the app accent with the name pill beside it, in ${colorScheme} at ${width} px`, async ({
					page
				}) => {
					await page.emulateMedia({ colorScheme });
					await page.setViewportSize({ width, height: 800 });
					await open(page, 'one');
					const tokens = await resolveStyle(page, { color: 'var(--accent)' }, ['color']);
					const mark = page.getByRole('img');
					const disc = discOf(mark);
					const pill = pillOf(mark);

					await expect(disc).toHaveCSS('color', tokens.color);
					expect(await disc.evaluate((node) => getComputedStyle(node).boxShadow)).toContain(tokens.color);
					await expect(disc).toHaveCSS('border-radius', '50%');
					const discBox = (await disc.boundingBox())!;
					expect(discBox.width).toBe(discBox.height);

					await expect(pill).toHaveText('Mozart');
					await expect(pill).not.toHaveCSS('color', tokens.color);
					const discGlass = await disc.evaluate((node) => getComputedStyle(node).backgroundColor);
					await expect(pill).toHaveCSS('background-color', discGlass);
					const pillBox = (await pill.boundingBox())!;
					expect(pillBox.x).toBeGreaterThanOrEqual(discBox.x + discBox.width);
					expect(Math.abs(pillBox.y + pillBox.height / 2 - (discBox.y + discBox.height / 2))).toBeLessThanOrEqual(1);
				});
			}
		}

		for (const language of languages) {
			test(`names the mark on one's own tile and on another person's tile in the ${language} words`, async ({ page }) => {
				await open(page, 'one', language);
				await expect(page.locator('html')).toHaveAttribute('lang', language);
				const own = wordsOf[language]['hearing.agentHearsYou']({ agent: 'Mozart' });
				await expect(page.getByRole('img', { name: own, exact: true })).toHaveAttribute('title', own);

				await open(page, 'two', language);
				const other = wordsOf[language]['hearing.agentHearsPerson']({ agent: 'Mozart', name: 'Anna' });
				await expect(page.getByRole('img', { name: other, exact: true })).toHaveAttribute('title', other);
			});
		}

		for (const width of widths) {
			test(`stacks the marks of two agents in one column without overlap at ${width} px`, async ({ page }) => {
				await page.setViewportSize({ width, height: 800 });
				await open(page, 'two');
				const first = page.getByRole('img', { name: /Mozart/ });
				const second = page.getByRole('img', { name: /Bach/ });
				const firstBox = (await first.boundingBox())!;
				const secondBox = (await second.boundingBox())!;
				expect(secondBox.x).toBe(firstBox.x);
				expect(secondBox.y).toBeGreaterThanOrEqual(firstBox.y + firstBox.height);
				await expect(discOf(first)).toBeVisible();
				await expect(discOf(second)).toBeVisible();
			});

			test(`ends a long agent name in an ellipsis inside its column at ${width} px`, async ({ page }) => {
				await page.setViewportSize({ width, height: 800 });
				await open(page, 'long');
				const mark = page.getByRole('img');
				const pill = pillOf(mark);
				await expect(pill).toHaveCSS('text-overflow', 'ellipsis');
				expect(await pill.evaluate((node) => node.scrollWidth > node.clientWidth)).toBe(true);
				const stage = (await page.locator('.ear-stage').boundingBox())!;
				const box = (await mark.boundingBox())!;
				expect(box.x + box.width).toBeLessThanOrEqual(stage.x + stage.width);
				expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
			});
		}
	});
}
