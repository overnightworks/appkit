import { execFileSync } from 'node:child_process';
import { cpSync, existsSync, mkdirSync, readdirSync, rmSync, statSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, join, normalize, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import type { BrowserContext, Page } from '@playwright/test';
import { build, createServer } from 'vite';

const consumersRoot = dirname(fileURLToPath(import.meta.url));
const repositoryRoot = resolve(consumersRoot, '../..');
const packDirectory = join(consumersRoot, '.pack');

export const origin = 'http://consumer.test';

export type ConsumerName = 'imported' | 'linked';

let tarballPath: string | undefined;

/** The tarball a consumer installs: the working tree packed by pnpm. */
function tarball(): string {
	if (!tarballPath) {
		rmSync(packDirectory, { recursive: true, force: true });
		mkdirSync(packDirectory, { recursive: true });
		execFileSync('pnpm', ['pack', '--pack-destination', packDirectory], {
			cwd: repositoryRoot,
			stdio: 'pipe'
		});
		tarballPath = join(packDirectory, readdirSync(packDirectory).find((name) => name.endsWith('.tgz'))!);
	}
	return tarballPath;
}

/** Lays the tarball out as `npm install` does, under node_modules, where both consumers resolve it. */
function installPackage(): void {
	const installed = join(consumersRoot, 'node_modules/overnightworks-design');
	rmSync(installed, { recursive: true, force: true });
	mkdirSync(installed, { recursive: true });
	execFileSync('tar', ['-xzf', tarball(), '-C', installed, '--strip-components=1']);
}

/** Builds the consumer for production and returns its output directory. */
export async function buildConsumer(name: ConsumerName): Promise<string> {
	const consumerDirectory = join(consumersRoot, name);
	const outDir = join(consumerDirectory, 'dist');
	installPackage();
	await build({
		root: consumerDirectory,
		configFile: false,
		logLevel: 'warn',
		plugins: [svelte()],
		build: { outDir, emptyOutDir: true }
	});
	if (name === 'linked') {
		// A linked stylesheet is copied into the page's origin untouched, bypassing the bundler.
		const stylesheet = createRequire(join(consumersRoot, 'package.json')).resolve(
			'overnightworks-design/design.css'
		);
		cpSync(stylesheet, join(outDir, 'design.css'));
		cpSync(join(dirname(stylesheet), 'fonts'), join(outDir, 'fonts'), { recursive: true });
	}
	return outDir;
}

/** Serves a built consumer through request routing, so no server process exists. */
export async function routeTo(target: Page | BrowserContext, outDir: string): Promise<void> {
	await target.route(`${origin}/**`, async (route) => {
		const { pathname } = new URL(route.request().url());
		const file = normalize(join(outDir, pathname === '/' ? 'index.html' : pathname));
		if (!file.startsWith(outDir + sep) || !existsSync(file) || !statSync(file).isFile()) {
			return route.fulfill({ status: 404 });
		}
		return route.fulfill({ path: file });
	});
}

/** What a prerendering `load` does under Node: the package root loaded through Vite's server-side module graph, then the words of one language. */
export async function loadKitWordsUnderNode(language: string): Promise<Record<string, unknown>> {
	installPackage();
	const server = await createServer({
		root: join(consumersRoot, 'imported'),
		configFile: false,
		logLevel: 'warn',
		appType: 'custom',
		server: { middlewareMode: true },
		plugins: [svelte()]
	});
	try {
		const kit = await server.ssrLoadModule('overnightworks-design');
		return await kit.loadKitWords(language);
	} finally {
		await server.close();
	}
}
