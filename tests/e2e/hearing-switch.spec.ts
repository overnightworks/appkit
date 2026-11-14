import { expect, test, type Locator, type Page } from '@playwright/test';
import type { KitLanguage, KitWords } from 'overnightworks-design';
import { buildConsumer, loadKitWordsUnderNode, origin, routeTo, type ConsumerName } from './build-consumer.ts';
import { resolveStyle } from './probe.ts';

const colorSchemes = ['light', 'dark'] as const;
const widths = [390, 1280] as const;
const languages = ['de', 'en'] as const satisfies readonly KitLanguage[];

const nameKeys = {
	hear: 'hearing.agentMayHearMe',
	listen: 'hearing.iWantToHearAgent',
	see: 'hearing.agentMaySeeMe'
} as const satisfies Record<'hear' | 'listen' | 'see', keyof KitWords>;

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

		const chipOf = (page: Page, kind: 'hear' | 'listen' | 'see', language: KitLanguage = 'en') =>
			page.getByRole('switch', { name: wordsOf[language][nameKeys[kind]], exact: true });

		async function open(page: Page, variant = '', language: KitLanguage = 'en'): Promise<void> {
			await routeTo(page.context(), outDir);
			await page.goto(`${origin}/?hearing=${variant}${language === 'en' ? '' : `&lang=${language}`}`);
			await expect(chipOf(page, 'hear', language)).toBeVisible();
		}

		test('blurs the video behind the chip, so the built CSS keeps the standard backdrop-filter', async ({ page }) => {
			await open(page);
			await expect(chipOf(page, 'hear')).not.toHaveCSS('backdrop-filter', 'none');
		});

		for (const kind of ['hear', 'see'] as const) {
			for (const colorScheme of colorSchemes) {
				for (const width of widths) {
					test(`paints an on ${kind} chip in the app accent and an off chip softened, on its own glass, in ${colorScheme} at ${width} px`, async ({
						page
					}) => {
						await page.emulateMedia({ colorScheme, reducedMotion: 'reduce' });
						await page.setViewportSize({ width, height: 800 });
						await open(page, 'see');
						const tokens = await resolveStyle(
							page,
							{ color: 'var(--accent)', 'background-color': 'var(--surface)', 'border-top-color': 'var(--text)' },
							['color', 'background-color', 'border-top-color']
						);

						const on = chipOf(page, kind);
						await expect(on).toHaveAttribute('aria-checked', 'true');
						await expect(on.locator('svg')).toHaveCSS('color', tokens.color);
						await expect(on.locator('span[aria-hidden]')).toHaveCSS('background-color', tokens.color);
						const onInk = await on.evaluate((node) => getComputedStyle(node.querySelector('span:nth-child(2)')!).color);
						const onKnob = await knobTransform(on.locator('span[aria-hidden]'));
						expect(onKnob).not.toBe('none');
						await expect(on).not.toHaveCSS('background-color', tokens['background-color']);
						await expect(on).not.toHaveCSS('color', tokens['border-top-color']);

						await open(page, 'see,off');
						const off = chipOf(page, kind);
						await expect(off).toHaveAttribute('aria-checked', 'false');
						await expect(off.locator('svg')).not.toHaveCSS('color', tokens.color);
						await expect(off.locator('span[aria-hidden]')).not.toHaveCSS('background-color', tokens.color);
						expect(await knobTransform(off.locator('span[aria-hidden]'))).not.toBe(onKnob);
						await expect(off.locator('span').nth(1)).not.toHaveCSS('color', onInk);
					});
				}
			}
		}

		for (const width of widths) {
			test(`keeps every chip inside the viewport in the de words at ${width} px`, async ({ page }) => {
				await page.setViewportSize({ width, height: 800 });
				await open(page, 'see', 'de');
				for (const kind of ['hear', 'listen', 'see'] as const) {
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

		for (const language of languages) {
			test(`shows the see chip by its short ${language} word and names it by the full words`, async ({ page }) => {
				await open(page, 'see', language);
				await expect(chipOf(page, 'see', language)).toHaveText(wordsOf[language]['hearing.seeShort']);
				await expect(page.getByRole('switch')).toHaveCount(3);
			});
		}

		for (const colorScheme of colorSchemes) {
			for (const width of widths) {
				for (const language of languages) {
					test(`keeps the compact see chip whole, pressable and inside a 120 px container beside the hearing chip in ${language}, ${colorScheme} at ${width} px`, async ({
						page
					}) => {
						await page.emulateMedia({ colorScheme, reducedMotion: 'reduce' });
						await page.setViewportSize({ width, height: 800 });
						await open(page, 'narrow', language);
						const see = chipOf(page, 'see', language);
						const stage = (await page.locator('.hearing-stage').boundingBox())!;
						const track = see.locator('span[aria-hidden]');
						for (const on of [true, false]) {
							await expect(see).toHaveAttribute('aria-checked', String(on));
							const box = (await see.boundingBox())!;
							const trackBox = (await track.boundingBox())!;
							const iconBox = (await see.locator('svg').boundingBox())!;
							expect(box.width).toBeCloseTo(26, 0);
							expect(trackBox.width).toBeCloseTo(26, 0);
							expect(box.x).toBeGreaterThanOrEqual(stage.x);
							expect(box.x + box.width).toBeLessThanOrEqual(stage.x + stage.width);
							expect(iconBox.width).toBeCloseTo(12, 0);
							expect(iconBox.x).toBeGreaterThanOrEqual(trackBox.x);
							expect(iconBox.x + iconBox.width).toBeLessThanOrEqual(trackBox.x + trackBox.width);
							expect(iconBox.y).toBeGreaterThanOrEqual(trackBox.y);
							expect(iconBox.y + iconBox.height).toBeLessThanOrEqual(trackBox.y + trackBox.height);
							const label = (await see.locator('span').nth(1).boundingBox())!;
							expect(label.width).toBeLessThanOrEqual(1);
							await see.click();
							await expect(see).toHaveAttribute('aria-checked', String(!on));
						}
						expect(await reportsOf(page)).toEqual(['see:false', 'see:true']);
						const hear = (await chipOf(page, 'hear', language).boundingBox())!;
						expect(hear.x + hear.width).toBeLessThanOrEqual(stage.x + stage.width);
						expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
					});
				}
			}
		}

		test('moves the icon with the knob on a compact chip', async ({ page }) => {
			await page.emulateMedia({ reducedMotion: 'reduce' });
			await open(page, 'narrow');
			const see = chipOf(page, 'see');
			const iconX = async () => (await see.locator('svg').boundingBox())!.x;
			const on = await iconX();
			await see.click();
			expect(await iconX()).toBeLessThan(on);
		});

		test.describe('with a finger at 390 px', () => {
			test.use({ hasTouch: true, isMobile: true, viewport: { width: 390, height: 800 } });

			const reach = 20;

			async function tapsLandOnChip(page: Page, chip: Locator, directions: readonly (readonly [number, number])[]) {
				const box = (await chip.boundingBox())!;
				for (const [dx, dy] of directions) {
					const point = { x: box.x + box.width / 2 + dx * reach, y: box.y + box.height / 2 + dy * reach };
					expect(
						await chip.evaluate((node, at) => node.contains(document.elementFromPoint(at.x, at.y)), point)
					).toBe(true);
					const before = await chip.getAttribute('aria-checked');
					await page.touchscreen.tap(point.x, point.y);
					await expect(chip).toHaveAttribute('aria-checked', String(before !== 'true'));
				}
			}

			test('reaches a compact chip from 20 px off its centre in every direction', async ({ page }) => {
				await open(page, 'narrow');
				expect(await page.evaluate(() => matchMedia('(any-pointer: coarse)').matches)).toBe(true);
				await tapsLandOnChip(page, chipOf(page, 'see'), [[0, -1], [0, 1], [-1, 0]]);
			});

			test('reaches a full chip from 20 px off its centre, away from the chip beside it', async ({ page }) => {
				await open(page);
				await tapsLandOnChip(page, chipOf(page, 'hear'), [[0, -1], [-1, 0], [1, 0]]);
				await tapsLandOnChip(page, chipOf(page, 'listen'), [[0, 1], [-1, 0], [1, 0]]);
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
