import { expect, test, type Page } from '@playwright/test';
import { buildConsumer, origin, routeTo, type ConsumerName } from './build-consumer.ts';

const colorSchemes = ['light', 'dark'] as const;
const widths = [390, 1280] as const;
const legalNames = ['Imprint', 'Privacy', 'Terms'];
const typedName = 'Felix mcDonald';

const panelOf = (page: Page) => page.getByRole('link', { name: typedName }).locator('..');
const reportsOf = (page: Page) => page.evaluate(() => window.reports);

/** The requests the page itself makes, to compare with the assets it was routed. */
function watchRequests(page: Page): { method: string; pathname: string }[] {
	const seen: { method: string; pathname: string }[] = [];
	page.on('request', (request) =>
		seen.push({ method: request.method(), pathname: new URL(request.url()).pathname })
	);
	return seen;
}

async function expectNothingStoredOrFetched(
	page: Page,
	requests: { method: string; pathname: string }[]
): Promise<void> {
	for (const { method, pathname } of requests) {
		expect(method).toBe('GET');
		expect(pathname).toMatch(/^\/($|assets\/|fonts\/|appkit\.css$)/);
	}
	const stored = await page.evaluate(
		() => localStorage.length + sessionStorage.length + document.cookie.length
	);
	expect(stored).toBe(0);
}

for (const consumer of ['imported', 'linked'] as const satisfies ConsumerName[]) {
	test.describe(`the account menu in a production consumer that ${consumer === 'imported' ? 'imports' : 'statically links'} appkit.css`, () => {
		let outDir: string;
		test.beforeAll(async () => {
			outDir = await buildConsumer(consumer);
		});

		async function open(page: Page, variant = ''): Promise<void> {
			await routeTo(page.context(), outDir);
			await page.goto(`${origin}/?menu=${variant}`);
			await expect(panelOf(page)).toBeVisible();
		}

		for (const colorScheme of colorSchemes) {
			for (const width of widths) {
				test(`paints the panel, the dot, the log out border and the legal row in ${colorScheme} at ${width} px`, async ({
					page
				}) => {
					await page.emulateMedia({ colorScheme });
					await page.setViewportSize({ width, height: 800 });
					await open(page);

					const surface = await page.evaluate(() => {
						const probe = document.createElement('div');
						probe.style.background = 'var(--surface)';
						document.body.append(probe);
						const color = getComputedStyle(probe).backgroundColor;
						probe.remove();
						return color;
					});
					expect(surface).not.toBe('rgba(0, 0, 0, 0)');
					await expect(panelOf(page)).toHaveCSS('background-color', surface);
					await expect(page.getByRole('radio', { name: 'Follow system' })).toBeChecked();
					await expect(page.getByRole('radio', { name: 'Follow system' })).toHaveCSS(
						'background-image',
						/radial-gradient/
					);
					await expect(page.getByRole('button', { name: 'Log out' }).locator('..')).toHaveCSS(
						'border-top-style',
						'solid'
					);
					expect(
						(await page.getByRole('button', { name: 'Log out' }).locator('..').boundingBox())!.height
					).toBe(40);
					const viewport = page.viewportSize()!;
					for (const name of legalNames) {
						const box = (await page.getByRole('link', { name }).boundingBox())!;
						expect(box.x).toBeGreaterThanOrEqual(0);
						expect(box.x + box.width).toBeLessThanOrEqual(viewport.width);
						expect(box.y + box.height).toBeLessThanOrEqual(viewport.height);
					}
				});
			}
		}

		test('keeps the case of a mixed-case name', async ({ page }) => {
			await open(page);
			const name = panelOf(page).locator('.as-typed');
			await expect(name).toHaveCSS('text-transform', 'none');
			expect(await name.textContent()).toBe(typedName);
			expect(await name.innerText()).toBe(typedName);
		});

		test('opens the name link in a new tab and reports it once', async ({ page }) => {
			const requests = watchRequests(page);
			await open(page);
			const [popup] = await Promise.all([
				page.context().waitForEvent('page'),
				page.getByRole('link', { name: typedName }).click()
			]);
			expect(popup.url()).toContain('/account');
			expect(await reportsOf(page)).toEqual(['account']);
			await expectNothingStoredOrFetched(page, requests);
		});

		test('reports Settings once and stays on the page', async ({ page }) => {
			const requests = watchRequests(page);
			await open(page);
			await page.getByRole('button', { name: 'Settings' }).click();
			expect(await reportsOf(page)).toEqual(['settings']);
			expect(page.url()).toBe(`${origin}/?menu=`);
			await expectNothingStoredOrFetched(page, requests);
		});

		test('sets data-theme on a pick, keeps the menu open, and removes it for Follow system on a dark device', async ({
			page
		}) => {
			const requests = watchRequests(page);
			await page.emulateMedia({ colorScheme: 'dark' });
			await open(page);
			const html = page.locator('html');
			await page.getByRole('radio', { name: 'Light' }).click();
			await expect(html).toHaveAttribute('data-theme', 'light');
			await page.getByRole('radio', { name: 'Dark' }).click();
			await expect(html).toHaveAttribute('data-theme', 'dark');
			await expect(panelOf(page)).toBeVisible();
			await expect(page.getByRole('radio', { name: 'Dark' })).toBeChecked();
			await page.getByRole('radio', { name: 'Follow system' }).click();
			await expect(html).not.toHaveAttribute('data-theme');
			await expect(page.getByRole('radio', { name: 'Follow system' })).toBeChecked();
			await expectNothingStoredOrFetched(page, requests);
		});

		test('snaps back when the app ignores the choice, and reports nothing for the checked radio', async ({
			page
		}) => {
			const requests = watchRequests(page);
			await open(page, 'ignore');
			await page.getByRole('radio', { name: 'Dark' }).click();
			expect(await reportsOf(page)).toEqual(['theme:dark']);
			await expect(page.getByRole('radio', { name: 'Follow system' })).toBeChecked();
			await expect(page.getByRole('radio', { name: 'Dark' })).not.toBeChecked();
			await page.getByRole('radio', { name: 'Follow system' }).click();
			expect(await reportsOf(page)).toEqual(['theme:dark']);
			await expectNothingStoredOrFetched(page, requests);
		});

		test('is reachable and operable by keyboard in reading order', async ({ page }) => {
			const requests = watchRequests(page);
			await open(page);
			const focused = () =>
				page.evaluate(() => {
					const element = document.activeElement!;
					return element.matches('a, button, input')
						? (element.closest('label') ?? element).textContent!.trim()
						: null;
				});
			const order: (string | null)[] = [];
			for (let stop = 0; stop < 8; stop++) {
				await page.keyboard.press('Tab');
				order.push(await focused());
			}
			expect(order).toEqual([typedName, 'Settings', 'Follow system', 'Log out', ...legalNames, null]);

			await page.getByRole('radio', { name: 'Follow system' }).focus();
			await page.keyboard.press('ArrowDown');
			await page.keyboard.press('ArrowDown');
			await page.keyboard.press('Space');
			await Promise.all([
				page.context().waitForEvent('page'),
				(async () => {
					await page.getByRole('link', { name: typedName }).focus();
					await page.keyboard.press('Enter');
				})()
			]);
			await page.getByRole('button', { name: 'Log out' }).focus();
			await page.keyboard.press('Enter');
			await page.keyboard.press('Space');
			expect(await reportsOf(page)).toEqual([
				'theme:light',
				'theme:dark',
				'account',
				'logout',
				'logout'
			]);
			await expectNothingStoredOrFetched(page, requests);
		});

		test('shows no theme rows and touches nothing without them', async ({ page }) => {
			const requests = watchRequests(page);
			await open(page, 'no-theme');
			await expect(page.getByRole('radio')).toHaveCount(0);
			await expect(page.getByText('Theme')).toHaveCount(0);
			await expectNothingStoredOrFetched(page, requests);
		});

		test('posts to the log out action when it is a form', async ({ page }) => {
			await routeTo(page.context(), outDir);
			const posted: string[] = [];
			await page.route(`${origin}/logout`, (route) => {
				posted.push(route.request().method());
				return route.fulfill({ status: 204 });
			});
			await page.goto(`${origin}/?menu=action`);
			await page.getByRole('button', { name: 'Log out' }).click({ noWaitAfter: true });
			await expect.poll(() => posted).toEqual(['POST']);
		});
	});
}
