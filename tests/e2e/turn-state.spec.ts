import { expect, test, type Page } from '@playwright/test';
import type { KitLanguage, KitWords } from 'overnightworks-design';
import { buildConsumer, loadKitWordsUnderNode, origin, routeTo, type ConsumerName } from './build-consumer.ts';
import { resolveStyle } from './probe.ts';

const colorSchemes = ['light', 'dark'] as const;
const widths = [390, 1280] as const;
const languages = ['de', 'en'] as const satisfies readonly KitLanguage[];

for (const consumer of ['imported', 'linked'] as const satisfies ConsumerName[]) {
	test.describe(`the turn state in a production consumer that ${consumer === 'imported' ? 'imports' : 'statically links'} design.css`, () => {
		let outDir: string;
		let wordsOf: Record<KitLanguage, KitWords>;
		test.beforeAll(async () => {
			outDir = await buildConsumer(consumer);
			wordsOf = { de: await loadKitWordsUnderNode('de'), en: await loadKitWordsUnderNode('en') };
		});

		async function open(page: Page, variant: string, language: KitLanguage = 'en'): Promise<void> {
			await routeTo(page.context(), outDir);
			await page.goto(`${origin}/?turn=${variant}${language === 'en' ? '' : `&lang=${language}`}`);
			await expect(page.locator('.turn-state').first()).toBeVisible();
		}

		for (const language of languages) {
			test(`words each stated outcome in the ${language} words and draws nothing for an unstated one`, async ({ page }) => {
				await open(page, 'alone', language);
				const words = wordsOf[language];
				const parts = page.locator('.turn-state');
				await expect(parts).toHaveText([
					words['turnState.notEnabled'],
					words['turnState.busy'],
					words['turnState.budgetSpent'],
					words['turnState.unavailable']
				]);
				await expect(page.locator('.turn-stage > div').last()).toBeEmpty();
				await expect(parts.first().locator('svg')).toHaveAttribute('aria-hidden', 'true');
			});
		}

		for (const colorScheme of colorSchemes) {
			for (const width of widths) {
				test(`paints the part in the muted ink on one line, in ${colorScheme} at ${width} px`, async ({ page }) => {
					await page.emulateMedia({ colorScheme });
					await page.setViewportSize({ width, height: 800 });
					await open(page, 'alone');
					const tokens = await resolveStyle(page, { color: 'var(--text-muted)' }, ['color']);
					const part = page.locator('.turn-state').first();
					await expect(part).toHaveCSS('color', tokens.color);
					await expect(part).toHaveCSS('white-space', 'nowrap');
					const box = (await part.boundingBox())!;
					const markBox = (await part.locator('svg').boundingBox())!;
					expect(markBox.width).toBeGreaterThan(0);
					expect(box.height).toBeLessThan(2 * markBox.height);
				});

				test(`keeps the part whole beside a long name in a here row, in ${colorScheme} at ${width} px`, async ({ page }) => {
					await page.emulateMedia({ colorScheme });
					await page.setViewportSize({ width, height: 800 });
					await open(page, 'here');
					const rows = page.locator('li.agent');
					await expect(rows).toHaveCount(3);

					const long = rows.nth(1);
					const name = long.locator('.name');
					await expect(name).toHaveCSS('text-overflow', 'ellipsis');
					expect(await name.evaluate((node) => node.scrollWidth > node.clientWidth)).toBe(true);
					const part = long.locator('.turn-state');
					const partBox = (await part.boundingBox())!;
					const rowBox = (await long.boundingBox())!;
					expect(partBox.x).toBeGreaterThanOrEqual(rowBox.x);
					expect(partBox.x + partBox.width).toBeLessThanOrEqual(rowBox.x + rowBox.width);
					expect(await part.evaluate((node) => node.scrollWidth <= node.clientWidth)).toBe(true);
					expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);

					await expect(rows.nth(2).locator('.turn-state')).toHaveCount(0);
					await expect(rows.first().locator('.turn-state')).toHaveText(wordsOf.en['turnState.busy']);
				});
			}
		}
	});
}
