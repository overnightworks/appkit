import { expect, test, type Page } from '@playwright/test';
import type { KitLanguage, KitWords } from 'overnightworks-design';
import { buildConsumer, loadKitWordsUnderNode, origin, routeTo, type ConsumerName } from './build-consumer.ts';
import { resolveStyle } from './probe.ts';

const colorSchemes = ['light', 'dark'] as const;
const widths = [390, 1280] as const;
const touchRowFloor = 44;
const languages = ['de', 'en'] as const satisfies readonly KitLanguage[];
/** The names of the consumer page's rows. */
const mozart = 'Mozart';
const leonardo = 'Leonardo da Vinci, the long-named painter and inventor';

const reportsOf = (page: Page) => page.evaluate(() => window.reports);

for (const consumer of ['imported', 'linked'] as const satisfies ConsumerName[]) {
	test.describe(`the agent control in a production consumer that ${consumer === 'imported' ? 'imports' : 'statically links'} design.css`, () => {
		let outDir: string;
		let wordsOf: Record<KitLanguage, KitWords>;
		let en: KitWords;
		let callMozart: string;
		let askLeonardoToLeave: string;
		test.beforeAll(async () => {
			outDir = await buildConsumer(consumer);
			wordsOf = { de: await loadKitWordsUnderNode('de'), en: await loadKitWordsUnderNode('en') };
			en = wordsOf.en;
			callMozart = en['agent.callLabel']({ name: mozart });
			askLeonardoToLeave = en['agent.askToLeaveLabel']({ name: leonardo });
		});

		async function open(page: Page, variant = '', language: KitLanguage = 'en'): Promise<void> {
			await routeTo(page.context(), outDir);
			await page.goto(`${origin}/?agents=${variant}${language === 'en' ? '' : `&lang=${language}`}`);
			await expect(page.getByRole('button', { name: wordsOf[language]['agent.callLabel']({ name: mozart }) })).toBeVisible();
		}

		for (const colorScheme of colorSchemes) {
			for (const width of widths) {
				test(`paints the refusal, the marks, the actions and the waiting dots in ${colorScheme} at ${width} px`, async ({
					page
				}) => {
					await page.emulateMedia({ colorScheme });
					await page.setViewportSize({ width, height: 800 });
					await open(page, 'refusal');

					const tokens = await resolveStyle(
						page,
						{
							'border-top-color': 'var(--fail)',
							'background-color': 'var(--fail-soft)',
							color: 'var(--text-muted)'
						},
						['border-top-color', 'background-color', 'color']
					);
					const alert = page.getByRole('alert');
					await expect(alert).toHaveText(en['agent.ownerAbsent']);
					await expect(alert).toHaveCSS('border-top-color', tokens['border-top-color']);
					await expect(alert).toHaveCSS('background-color', tokens['background-color']);

					const marks = page.getByText('AI', { exact: true });
					await expect(marks).toHaveCount(3);
					for (const mark of await marks.all()) {
						await expect(mark).toHaveCSS('color', tokens.color);
						await expect(mark).toHaveCSS('border-top-style', 'solid');
					}
					await expect(page.getByRole('status').locator('i').first()).toBeVisible();
					await expect(page.getByRole('button', { name: callMozart })).toHaveCSS(
						'border-top-style',
						'solid'
					);
				});
			}
		}

		for (const width of widths) {
			test(`keeps every action inside the viewport with a long name at ${width} px`, async ({ page }) => {
				await page.setViewportSize({ width, height: 800 });
				await open(page);
				for (const name of [callMozart, askLeonardoToLeave]) {
					const box = (await page.getByRole('button', { name }).boundingBox())!;
					expect(box.x).toBeGreaterThanOrEqual(0);
					expect(box.x + box.width).toBeLessThanOrEqual(width);
				}
				expect(
					await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)
				).toBe(true);
			});
		}

		test.describe('with a finger at 390 px', () => {
			test.use({ hasTouch: true, isMobile: true, viewport: { width: 390, height: 800 } });

			test('every row reaches its touch floor', async ({ page }) => {
				await open(page);
				expect(await page.evaluate(() => matchMedia('(any-pointer: coarse)').matches)).toBe(true);
				const rows = await page.getByRole('listitem').all();
				expect(rows).toHaveLength(3);
				for (const row of rows) {
					expect((await row.boundingBox())!.height).toBeGreaterThanOrEqual(touchRowFloor);
				}
			});
		});

		test.describe('with a mouse at 390 px', () => {
			test.use({ hasTouch: false, viewport: { width: 390, height: 800 } });

			test('a row stays below the touch floor', async ({ page }) => {
				await open(page);
				expect(await page.evaluate(() => matchMedia('(any-pointer: coarse)').matches)).toBe(false);
				const row = page.getByRole('listitem').first();
				expect((await row.boundingBox())!.height).toBeLessThan(touchRowFloor);
			});
		});

		test('sizes the AI mark by the control, not by the font size of its place', async ({ page }) => {
			await open(page);
			const mark = page.getByText('AI', { exact: true }).first();
			const size = () => mark.evaluate((node) => parseFloat(getComputedStyle(node).fontSize));
			const before = await size();
			await page.getByRole('list').evaluate((list) => {
				list.closest('div')!.style.fontSize = '24px';
			});
			expect(await size()).toBe(before);
		});

		test('reports the key of a call and of a send-away once each and keeps the page', async ({ page }) => {
			await open(page);
			await page.getByRole('button', { name: callMozart }).click();
			expect(await reportsOf(page)).toEqual(['call:key-mozart']);
			await page.getByRole('button', { name: askLeonardoToLeave }).click();
			expect(await reportsOf(page)).toEqual(['call:key-mozart', 'leave:key-leonardo']);
			await expect(page.getByRole('dialog')).toHaveCount(0);
			expect(page.url()).toBe(`${origin}/?agents=`);
		});

		test('gives the waiting row no button and keeps the dots still under reduced motion', async ({ page }) => {
			await open(page);
			const waiting = page.getByRole('status');
			await expect(waiting).toHaveText(en['agent.calling']);
			await expect(waiting.getByRole('button')).toHaveCount(0);
			const dot = waiting.locator('i').first();
			await page.emulateMedia({ reducedMotion: 'no-preference' });
			await expect(dot).not.toHaveCSS('animation-name', 'none');
			await page.emulateMedia({ reducedMotion: 'reduce' });
			await expect(dot).toHaveCSS('animation-name', 'none');
		});

		const outcomes = [
			['ended-no-answer', 'agent.noAnswer'],
			['ended-busy', 'agent.busy'],
			['ended-owner-absent', 'agent.ownerAbsent']
		] as const;

		for (const colorScheme of colorSchemes) {
			for (const width of widths) {
				for (const [variant, key] of outcomes) {
					test(`paints the ${variant} row muted with a small icon and no key in ${colorScheme} at ${width} px`, async ({
						page
					}) => {
						await page.emulateMedia({ colorScheme });
						await page.setViewportSize({ width, height: 800 });
						await routeTo(page.context(), outDir);
						await page.goto(`${origin}/?agents=${variant}`);
						const row = page.getByRole('listitem').first();
						const outcome = row.getByRole('status');
						await expect(outcome).toHaveText(en[key]);
						await expect(row.getByRole('button')).toHaveCount(0);
						const tokens = await resolveStyle(page, { color: 'var(--text-muted)' }, ['color']);
						await expect(outcome).toHaveCSS('color', tokens.color);
						const icon = outcome.locator('svg');
						await expect(icon).toHaveCSS('width', '15px');
						await expect(icon).toHaveCSS('height', '15px');
						await expect(outcome.locator('i')).toHaveCount(0);
						const box = (await outcome.boundingBox())!;
						expect(box.x + box.width).toBeLessThanOrEqual(width);
						expect(
							await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)
						).toBe(true);
					});
				}
			}
		}

		for (const language of languages) {
			test(`draws the ${language} words of an outcome`, async ({ page }) => {
				await routeTo(page.context(), outDir);
				await page.goto(`${origin}/?agents=ended-no-answer&lang=${language}`);
				await expect(page.getByRole('listitem').first().getByRole('status')).toHaveText(
					wordsOf[language]['agent.noAnswer']
				);
			});
		}

		test('draws the row callable again after the outcome and reports the call', async ({ page }) => {
			await routeTo(page.context(), outDir);
			await page.goto(`${origin}/?agents=ended-busy`);
			await expect(page.getByRole('status').filter({ hasText: en['agent.busy'] })).toBeVisible();
			const call = page.getByRole('button', { name: callMozart });
			await expect(call).toBeVisible({ timeout: 10_000 });
			await expect(page.getByRole('status').filter({ hasText: en['agent.busy'] })).toHaveCount(0);
			await call.click();
			expect(await reportsOf(page)).toEqual(['call:key-mozart']);
		});

		test('is operable by keyboard in reading order', async ({ page }) => {
			await open(page);
			await page.keyboard.press('Tab');
			await expect(page.getByRole('button', { name: callMozart })).toBeFocused();
			await page.keyboard.press('Tab');
			await expect(page.getByRole('button', { name: askLeonardoToLeave })).toBeFocused();
			await page.keyboard.press('Enter');
			expect(await reportsOf(page)).toEqual(['leave:key-leonardo']);
		});

		for (const language of languages) {
			for (const width of widths) {
				test(`draws the ${language} words in every row, the refusal and the empty sentence at ${width} px`, async ({
					page
				}) => {
					await page.setViewportSize({ width, height: 800 });
					await open(page, 'refusal', language);
					await expect(page.locator('html')).toHaveAttribute('lang', language);
					const kit = wordsOf[language];
					await expect(page.getByRole('alert')).toHaveText(kit['agent.ownerAbsent']);
					await expect(page.getByRole('status')).toHaveText(kit['agent.calling']);
					for (const name of [
						kit['agent.callLabel']({ name: mozart }),
						kit['agent.askToLeaveLabel']({ name: leonardo })
					]) {
						const box = (await page.getByRole('button', { name }).boundingBox())!;
						expect(box.x).toBeGreaterThanOrEqual(0);
						expect(box.x + box.width).toBeLessThanOrEqual(width);
					}
					expect(
						await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)
					).toBe(true);
					await routeTo(page.context(), outDir);
					await page.goto(`${origin}/?agents=empty&lang=${language}`);
					await expect(page.getByText(kit['agent.empty'])).toBeVisible();
				});
			}
		}

		test('draws only the empty sentence when no agent is listed', async ({ page }) => {
			await routeTo(page.context(), outDir);
			await page.goto(`${origin}/?agents=empty`);
			await expect(page.getByText(en['agent.empty'])).toBeVisible();
			await expect(page.getByRole('button')).toHaveCount(0);
			await expect(page.getByRole('list')).toHaveCount(0);
		});
	});
}
