import { readdirSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { expect, test } from '@playwright/test';
import { buildConsumer, loadKitWordsUnderNode, origin, routeTo } from './build-consumer.ts';

const catalogs = join(dirname(fileURLToPath(import.meta.url)), '../../src/catalogs');
const languages = readdirSync(catalogs)
	.filter((name) => name.endsWith('.po'))
	.map((name) => name.slice(0, -'.po'.length))
	.sort();
/** A key the consumer page never reads, so only a words chunk holds it. */
const firstKey = /^msgctxt "(.+)"$/m.exec(readFileSync(join(catalogs, 'de.po'), 'utf8'))![1];

test.describe('the kit words in a production consumer', () => {
	let outDir: string;
	test.beforeAll(async () => {
		outDir = await buildConsumer('imported');
	});

	test('emit one chunk per kit language', () => {
		const assets = join(outDir, 'assets');
		const chunks = readdirSync(assets).filter(
			(name) => name.endsWith('.js') && readFileSync(join(assets, name), 'utf8').includes(`"${firstKey}"`)
		);
		expect(chunks).toHaveLength(languages.length);
	});

	for (const [language, logOut] of [
		['de', 'Abmelden'],
		['en', 'Log out']
	] as const) {
		test(`load the ${language} words in the browser`, async ({ page }) => {
			await routeTo(page, outDir);
			await page.goto(`${origin}/?words=${language}`);
			await expect(page.getByRole('status')).toHaveText(logOut);
		});

		test(`load the ${language} words under Node`, async () => {
			expect((await loadKitWordsUnderNode(language))['account.logOut']).toBe(logOut);
		});
	}
});
