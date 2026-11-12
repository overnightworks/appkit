import { expect, test, type Locator, type Page } from '@playwright/test';
import type { KitLanguage, KitWords } from 'overnightworks-design';
import { buildConsumer, loadKitWordsUnderNode, origin, routeTo, type ConsumerName } from './build-consumer.ts';
import { resolveStyle } from './probe.ts';

const colorSchemes = ['light', 'dark'] as const;
const widths = [390, 1280] as const;
const languages = ['de', 'en'] as const satisfies readonly KitLanguage[];

const reportsOf = (page: Page) => page.evaluate(() => window.reports);

/** The computed `transform` of the knob, the track's `::after`. */
const knobTransform = (track: Locator) => track.evaluate((node) => getComputedStyle(node, '::after').transform);

for (const consumer of ['imported', 'linked'] as const satisfies ConsumerName[]) {
	test.describe(`the hearing switch in a production consumer that ${consumer === 'imported' ? 'imports' : 'statically links'} design.css`, () => {
		let outDir: string;
		let wordsOf: Record<KitLanguage, KitWords>;
		let en: KitWords;
		test.beforeAll(async () => {
			outDir = await buildConsumer(consumer);
			wordsOf = { de: await loadKitWordsUnderNode('de'), en: await loadKitWordsUnderNode('en') };
			en = wordsOf.en;
		});

		const chipOf = (page: Page, kind: 'hear' | 'listen', language: KitLanguage = 'en') =>
			page.getByRole('switch', {
				name: wordsOf[language][kind === 'hear' ? 'hearing.agentMayHearMe' : 'hearing.iWantToHearAgent'],
				exact: true
			});

		async function open(page: Page, variant = '', language: KitLanguage = 'en'): Promise<void> {
			await routeTo(page.context(), outDir);
			await page.goto(`${origin}/?hearing=${variant}${language === 'en' ? '' : `&lang=${language}`}`);
			await expect(chipOf(page, 'hear', language)).toBeVisible();
		}

		test('blurs the video behind the chip, so the built CSS keeps the standard backdrop-filter', async ({ page }) => {
			await open(page);
			await expect(chipOf(page, 'hear')).not.toHaveCSS('backdrop-filter', 'none');
		});

		for (const colorScheme of colorSchemes) {
			for (const width of widths) {
				test(`paints an on chip in the app accent and an off chip softened, on its own glass, in ${colorScheme} at ${width} px`, async ({
					page
				}) => {
					await page.emulateMedia({ colorScheme, reducedMotion: 'reduce' });
					await page.setViewportSize({ width, height: 800 });
					await open(page);
					const tokens = await resolveStyle(
						page,
						{ color: 'var(--accent)', 'background-color': 'var(--surface)', 'border-top-color': 'var(--text)' },
						['color', 'background-color', 'border-top-color']
					);

					const on = chipOf(page, 'hear');
					await expect(on).toHaveAttribute('aria-checked', 'true');
					await expect(on.locator('svg')).toHaveCSS('color', tokens.color);
					await expect(on.locator('span[aria-hidden]')).toHaveCSS('background-color', tokens.color);
					const onInk = await on.evaluate((node) => getComputedStyle(node.querySelector('span:nth-child(2)')!).color);
					const onKnob = await knobTransform(on.locator('span[aria-hidden]'));
					expect(onKnob).not.toBe('none');
					await expect(on).not.toHaveCSS('background-color', tokens['background-color']);
					await expect(on).not.toHaveCSS('color', tokens['border-top-color']);

					await open(page, 'off');
					const off = chipOf(page, 'hear');
					await expect(off).toHaveAttribute('aria-checked', 'false');
					await expect(off.locator('svg')).not.toHaveCSS('color', tokens.color);
					await expect(off.locator('span[aria-hidden]')).not.toHaveCSS('background-color', tokens.color);
					expect(await knobTransform(off.locator('span[aria-hidden]'))).not.toBe(onKnob);
					await expect(off.locator('span').nth(1)).not.toHaveCSS('color', onInk);
				});
			}
		}

		for (const width of widths) {
			test(`keeps both chips inside the viewport in the de words at ${width} px`, async ({ page }) => {
				await page.setViewportSize({ width, height: 800 });
				await open(page, '', 'de');
				for (const kind of ['hear', 'listen'] as const) {
					const box = (await chipOf(page, kind, 'de').boundingBox())!;
					expect(box.x).toBeGreaterThanOrEqual(0);
					expect(box.x + box.width).toBeLessThanOrEqual(width);
				}
				expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
			});
		}

		for (const language of languages) {
			test(`names each chip by its ${language} label and lang`, async ({ page }) => {
				await open(page, '', language);
				await expect(page.locator('html')).toHaveAttribute('lang', language);
				await expect(chipOf(page, 'listen', language)).toHaveText(wordsOf[language]['hearing.iWantToHearAgent']);
				await expect(page.getByRole('switch')).toHaveCount(2);
			});
		}

		test.describe('with a finger at 390 px', () => {
			test.use({ hasTouch: true, isMobile: true, viewport: { width: 390, height: 800 } });

			test('lets the visible body of each chip belong to that chip at the edges that face each other', async ({ page }) => {
				await open(page);
				expect(await page.evaluate(() => matchMedia('(any-pointer: coarse)').matches)).toBe(true);
				const lands = async (chip: Locator, edge: 'bottom' | 'top') => {
					const box = (await chip.boundingBox())!;
					const y = edge === 'bottom' ? box.y + box.height - 2 : box.y + 2;
					return chip.evaluate((node, point) => node.contains(document.elementFromPoint(point.x, point.y)), {
						x: box.x + box.width / 2,
						y
					});
				};
				expect(await lands(chipOf(page, 'hear'), 'bottom')).toBe(true);
				expect(await lands(chipOf(page, 'listen'), 'top')).toBe(true);
			});
		});

		test('reports the negated state of each chip and follows the app when it takes the change', async ({ page }) => {
			await open(page);
			await chipOf(page, 'hear').click();
			expect(await reportsOf(page)).toEqual(['hear:false']);
			await expect(chipOf(page, 'hear')).toHaveAttribute('aria-checked', 'false');
			await chipOf(page, 'hear').click();
			await chipOf(page, 'listen').click();
			expect(await reportsOf(page)).toEqual(['hear:false', 'hear:true', 'listen:false']);
			await expect(chipOf(page, 'hear')).toHaveAttribute('aria-checked', 'true');
			await expect(chipOf(page, 'listen')).toHaveAttribute('aria-checked', 'false');
		});

		test('never flips itself when the app ignores the change', async ({ page }) => {
			await open(page, 'ignore');
			await chipOf(page, 'hear').click();
			await chipOf(page, 'hear').click();
			expect(await reportsOf(page)).toEqual(['hear:false', 'hear:false']);
			await expect(chipOf(page, 'hear')).toHaveAttribute('aria-checked', 'true');
		});

		test('is operable by keyboard with Space and Enter, in reading order, with a visible focus ring', async ({ page }) => {
			await open(page);
			const accent = (await resolveStyle(page, { 'outline-color': 'var(--accent)' }, ['outline-color']))[
				'outline-color'
			];
			await page.keyboard.press('Tab');
			await expect(chipOf(page, 'hear')).toBeFocused();
			await expect(chipOf(page, 'hear')).toHaveCSS('outline-style', 'solid');
			await expect(chipOf(page, 'hear')).toHaveCSS('outline-color', accent);
			await page.keyboard.press('Space');
			await page.keyboard.press('Enter');
			expect(await reportsOf(page)).toEqual(['hear:false', 'hear:true']);
			await page.keyboard.press('Tab');
			await expect(chipOf(page, 'listen')).toBeFocused();
			await page.keyboard.press('Space');
			expect(await reportsOf(page)).toEqual(['hear:false', 'hear:true', 'listen:false']);
		});

		test('moves the knob with a transition only while motion is allowed', async ({ page }) => {
			await open(page);
			const track = chipOf(page, 'hear').locator('span[aria-hidden]');
			const duration = () => track.evaluate((node) => getComputedStyle(node, '::after').transitionDuration);
			await page.emulateMedia({ reducedMotion: 'no-preference' });
			expect(await duration()).not.toBe('0s');
			await page.emulateMedia({ reducedMotion: 'reduce' });
			expect(await duration()).toBe('0s');
		});

		test('shows the chip in the en words by its icon and label only', async ({ page }) => {
			await open(page);
			await expect(chipOf(page, 'hear')).toHaveText(en['hearing.agentMayHearMe']);
			await expect(chipOf(page, 'hear').locator('svg')).toHaveCount(1);
		});
	});
}
