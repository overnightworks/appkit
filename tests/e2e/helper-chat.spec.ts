import { expect, test, type Locator, type Page } from '@playwright/test';
import type { KitLanguage, KitWords } from 'overnightworks-design';
import { buildConsumer, loadKitWordsUnderNode, origin, routeTo, type ConsumerName } from './build-consumer.ts';
import { resolveStyle } from './probe.ts';

const colorSchemes = ['light', 'dark'] as const;
const widths = [390, 1280] as const;
const languages = ['de', 'en'] as const satisfies readonly KitLanguage[];

const reportsOf = (page: Page) => page.evaluate(() => window.reports);
const bubbleOf = (page: Page, text: string) => page.locator('.bubble', { hasText: text });
const rowOf = (page: Page, tool: string) => page.locator('.tool-call', { hasText: tool }).first();

for (const consumer of ['imported', 'linked'] as const satisfies ConsumerName[]) {
	test.describe(`the helper chat in a production consumer that ${consumer === 'imported' ? 'imports' : 'statically links'} design.css`, () => {
		let outDir: string;
		let wordsOf: Record<KitLanguage, KitWords>;
		test.beforeAll(async () => {
			outDir = await buildConsumer(consumer);
			wordsOf = { de: await loadKitWordsUnderNode('de'), en: await loadKitWordsUnderNode('en') };
		});

		const fieldOf = (page: Page, language: KitLanguage = 'en'): Locator =>
			page.getByRole('textbox', { name: wordsOf[language]['helperChat.composerLabel']({ name: 'Mozart' }), exact: true });
		const sendOf = (page: Page, language: KitLanguage = 'en'): Locator =>
			page.getByRole('button', { name: wordsOf[language]['helperChat.send'], exact: true });

		async function open(page: Page, variant: string, language: KitLanguage = 'en'): Promise<void> {
			await routeTo(page.context(), outDir);
			await page.goto(`${origin}/?helper=${variant}${language === 'en' ? '' : `&lang=${language}`}`);
			await expect(fieldOf(page, language)).toBeVisible();
		}

		for (const colorScheme of colorSchemes) {
			for (const width of widths) {
				test(`draws the bubbles, the tool rows and the composer from the fixed values and the app accent, in ${colorScheme} at ${width} px`, async ({
					page
				}) => {
					await page.emulateMedia({ colorScheme });
					await page.setViewportSize({ width, height: 800 });
					await open(page, 'base');
					const tokens = await resolveStyle(
						page,
						{
							color: 'var(--accent)',
							'background-color': 'var(--on-accent)',
							'border-top-color': 'var(--text-muted)',
							'font-family': 'var(--font-display)'
						},
						['color', 'background-color', 'border-top-color', 'font-family']
					);
					const send = sendOf(page);
					const field = fieldOf(page);

					await expect(send).toHaveCSS('background-color', tokens.color);
					await expect(send).toHaveCSS('color', tokens['background-color']);
					await expect(send).toHaveCSS('font-family', tokens['font-family']);
					await expect(send).toHaveCSS('text-transform', 'uppercase');
					await expect(send).toHaveCSS('border-top-left-radius', '6px');
					await expect(field).toHaveCSS('border-top-left-radius', '8px');
					await expect(bubbleOf(page, 'Make the second verse')).toHaveCSS('border-top-left-radius', '12px');
					await expect(bubbleOf(page, 'Make the second verse')).toHaveCSS('background-color', tokens.color);
					expect((await field.boundingBox())!.height).toBeGreaterThanOrEqual(44);
					const sendBox = (await send.boundingBox())!;
					expect(sendBox.height).toBeGreaterThanOrEqual(44);
					expect(sendBox.width).toBeGreaterThanOrEqual(44);

					const row = rowOf(page, 'rewrite_section');
					await expect(row).toHaveCSS('color', tokens['border-top-color']);
					await expect(row).toHaveCSS('font-size', '12.8px');
					expect(await row.evaluate((node) => getComputedStyle(node).fontFamily)).toContain('ui-monospace');

					expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
				});

				test(`draws a disabled field as muted text on the deep background and a disabled Send at half opacity, in ${colorScheme} at ${width} px`, async ({
					page
				}) => {
					await page.emulateMedia({ colorScheme });
					await page.setViewportSize({ width, height: 800 });
					await open(page, 'archived');
					const tokens = await resolveStyle(
						page,
						{ color: 'var(--text-muted)', 'background-color': 'var(--bg-deep)' },
						['color', 'background-color']
					);
					await expect(fieldOf(page)).toBeDisabled();
					await expect(fieldOf(page)).toHaveCSS('color', tokens.color);
					await expect(fieldOf(page)).toHaveCSS('background-color', tokens['background-color']);
					await expect(sendOf(page)).toBeDisabled();
					await expect(sendOf(page)).toHaveCSS('opacity', '0.5');
				});

				test(`wraps a long tool target and keeps the composer inside the page, in ${colorScheme} at ${width} px`, async ({
					page
				}) => {
					await page.emulateMedia({ colorScheme });
					await page.setViewportSize({ width, height: 800 });
					await open(page, 'base');
					const target = page.locator('.target', { hasText: 'Bridge of a long-named' });
					await expect(target).toBeVisible();
					const bubble = (await bubbleOf(page, 'Bridge of a long-named').boundingBox())!;
					const box = (await target.boundingBox())!;
					expect(box.x + box.width).toBeLessThanOrEqual(bubble.x + bubble.width + 1);
					const send = (await sendOf(page).boundingBox())!;
					expect(send.x + send.width).toBeLessThanOrEqual(width);
				});
			}
		}

		for (const language of languages) {
			test(`reads its kit words, its tool row and its thinking line in the ${language} words`, async ({ page }) => {
				const words = wordsOf[language];
				await open(page, 'base', language);
				await expect(page.locator('html')).toHaveAttribute('lang', language);
				await expect(sendOf(page, language)).toBeVisible();
				await expect(rowOf(page, 'rewrite_section')).toContainText(words['helperChat.ranTool']({ tool: 'rewrite_section' }));

				await open(page, 'running', language);
				await expect(page.getByRole('status')).toHaveText(words['helperChat.thinking']({ name: 'Mozart' }));

				await open(page, 'loading', language);
				await expect(page.getByText(words['helperChat.loading'], { exact: true })).toBeVisible();
			});
		}

		test('leads each helper message with the AI mark before its tool rows and gives the person none', async ({ page }) => {
			await open(page, 'base');
			const helper = bubbleOf(page, 'I shortened it');
			await expect(helper.locator('.ai-mark')).toHaveCount(1);
			const marked = await helper.evaluate((node) => {
				const mark = node.querySelector('.ai-mark')!;
				const row = node.querySelector('.tool-call')!;
				return Boolean(mark.compareDocumentPosition(row) & Node.DOCUMENT_POSITION_FOLLOWING) && node.firstElementChild!.contains(mark);
			});
			expect(marked).toBe(true);
			await expect(bubbleOf(page, 'Make the second verse').locator('.ai-mark')).toHaveCount(0);
		});

		test('shows message text as written, with its line breaks', async ({ page }) => {
			await open(page, 'base');
			const person = bubbleOf(page, 'Make the second verse').locator('.text');
			await expect(person).toHaveCSS('white-space', 'pre-wrap');
			expect((await person.boundingBox())!.height).toBeGreaterThan(30);
		});

		test('shows the tool row with the input as its title, the app’s target and the foreign mark with its title', async ({ page }) => {
			await open(page, 'base');
			await expect(rowOf(page, 'rewrite_section')).toHaveAttribute('title', '{"title":"Verse 2","foreign":false}');
			await expect(rowOf(page, 'rewrite_section').locator('.target')).toHaveText('in Verse 2');
			await expect(rowOf(page, 'add_line').locator('[title="Someone else\'s song"]')).toBeVisible();
			await expect(rowOf(page, 'rewrite_section').locator('[title="Someone else\'s song"]')).toHaveCount(0);
		});

		test('shows the empty hint while there is no message', async ({ page }) => {
			await open(page, 'empty');
			const hint = page.getByText('Ask Mozart about your song.');
			await expect(hint).toBeVisible();
			const tokens = await resolveStyle(page, { color: 'var(--text-muted)' }, ['color']);
			await expect(hint).toHaveCSS('color', tokens.color);
		});

		test('shows the loading word or the failure alert instead of the list and keeps the composer', async ({ page }) => {
			await open(page, 'loading');
			await expect(page.getByText(wordsOf.en['helperChat.loading'], { exact: true })).toBeVisible();
			await expect(page.getByText('Make the second verse')).toHaveCount(0);

			await open(page, 'failed');
			await expect(page.getByRole('alert')).toHaveText('The conversation could not be loaded.');
			await expect(sendOf(page)).toBeVisible();
		});

		test('shows the app’s problem line after the message it belongs to and reports its retry', async ({ page }) => {
			await open(page, 'problem');
			const message = page.locator('.message', { hasText: 'I got as far as' });
			await expect(message.getByRole('alert')).toContainText('Mozart stopped.');
			await message.getByRole('button', { name: 'Try again' }).click();
			expect(await reportsOf(page)).toEqual(['retry']);
			await expect(page.locator('.message', { hasText: 'Make the second verse' }).getByRole('alert')).toHaveCount(0);
		});

		test('shows the archived banner with its button above the composer and disables the composer', async ({ page }) => {
			await open(page, 'archived');
			const banner = page.getByText('This song is archived.');
			await expect(banner).toBeVisible();
			expect((await banner.boundingBox())!.y).toBeLessThan((await fieldOf(page).boundingBox())!.y);
			await page.getByRole('button', { name: 'Restore it' }).click();
			expect(await reportsOf(page)).toEqual(['restore']);
		});

		test('hands the message list to the app, which restores its place, and reports scrolling', async ({ page }) => {
			await open(page, 'scroll');
			const list = page.locator('.list');
			await expect.poll(() => list.evaluate((node) => node.scrollTop)).toBeGreaterThan(0);
			await list.evaluate((node) => {
				node.scrollTop = 0;
			});
			await expect.poll(() => reportsOf(page)).toContain('scroll:false');
		});

		test('keeps the one thinking line while the answer grows and the turn ends, changing only its text', async ({ page }) => {
			await open(page, 'running');
			const line = page.getByRole('status');
			await expect(line).toHaveCount(1);
			await expect(line).toHaveText(wordsOf.en['helperChat.thinking']({ name: 'Mozart' }));
			const handle = await line.elementHandle();

			await page.locator('#grow').click();
			await expect(page.getByText('Here is a shorter verse.')).toBeVisible();
			await expect(line).toHaveText('');
			await page.locator('#finish').click();
			expect(await handle!.evaluate((node) => node.isConnected)).toBe(true);
			await expect(page.getByRole('status')).toHaveCount(1);
		});

		test('sends the trimmed draft on Enter and on Send, and makes a new line on Shift+Enter', async ({ page }) => {
			await open(page, 'base');
			const field = fieldOf(page);
			await field.fill('  Hello  ');
			await field.press('Enter');
			await expect(field).toHaveValue('');
			expect(await reportsOf(page)).toEqual(['send:Hello']);

			await field.fill('Line one');
			await field.press('Shift+Enter');
			await field.pressSequentially('Line two');
			await expect(field).toHaveValue('Line one\nLine two');
			expect(await reportsOf(page)).toEqual(['send:Hello']);

			await sendOf(page).click();
			expect(await reportsOf(page)).toEqual(['send:Hello', 'send:Line one\nLine two']);
		});

		test('cancels a plain Enter without sending while the draft is empty and while a turn runs', async ({ page }) => {
			await open(page, 'base');
			const field = fieldOf(page);
			await field.press('Enter');
			await expect(field).toHaveValue('');
			await expect(sendOf(page)).toBeDisabled();

			await open(page, 'running');
			await field.fill('Another');
			await expect(sendOf(page)).toBeDisabled();
			await field.press('Enter');
			await expect(field).toHaveValue('Another');
			expect(await reportsOf(page)).toEqual([]);
		});

		test('picks from the app’s pick list on ArrowDown then Enter without sending', async ({ page }) => {
			await open(page, 'base');
			const field = fieldOf(page);
			await field.pressSequentially('Hi @');
			const list = page.getByRole('listbox', { name: 'People' });
			await expect(list.getByRole('option')).toHaveCount(3);
			await expect(list.getByRole('option').first()).toHaveAttribute('aria-selected', 'true');
			await field.press('ArrowDown');
			await expect(list.getByRole('option', { name: 'Bach' })).toHaveAttribute('aria-selected', 'true');
			await field.press('Enter');
			expect(await reportsOf(page)).toEqual(['pick:Bach']);
			await expect(field).toHaveValue('Hi ');
			await expect(page.getByRole('button', { name: 'Bach ×' })).toBeVisible();
			await expect(list).toHaveCount(0);

			await page.getByRole('button', { name: 'Bach ×' }).click();
			expect(await reportsOf(page)).toEqual(['pick:Bach', 'untag:Bach']);
		});

		test('places the pick list inside the composer box above the field and keeps the focus in the field when it is pressed', async ({
			page
		}) => {
			await open(page, 'base');
			const field = fieldOf(page);
			await field.pressSequentially('@');
			const option = page.getByRole('option', { name: 'Clara' });
			const optionBox = (await option.boundingBox())!;
			const fieldBox = (await field.boundingBox())!;
			expect(optionBox.y + optionBox.height).toBeLessThanOrEqual(fieldBox.y);
			expect(optionBox.x).toBeGreaterThanOrEqual(fieldBox.x - 1);
			await option.click();
			await expect(field).toBeFocused();
			expect(await reportsOf(page)).toEqual(['pick:Clara']);
		});

		test('keeps the focus in the field when Send is pressed', async ({ page }) => {
			await open(page, 'draft');
			await fieldOf(page).focus();
			await sendOf(page).click();
			await expect(fieldOf(page)).toBeFocused();
			expect(await reportsOf(page)).toEqual(['send:A first line\nA second line']);
		});
	});
}
