import { execFileSync } from 'node:child_process';
import { cpSync, mkdirSync, readdirSync, rmSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import { build } from 'vite';

const consumersRoot = dirname(fileURLToPath(import.meta.url));
const repositoryRoot = resolve(consumersRoot, '../..');
const packDirectory = join(consumersRoot, '.pack');

export type ConsumerName = 'imported' | 'linked';

let tarballPath: string | undefined;

/** The tarball a consumer installs: APPKIT_TARBALL, or the working tree packed by pnpm. */
function tarball(): string {
	if (process.env.APPKIT_TARBALL) return resolve(process.env.APPKIT_TARBALL);
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
	const installed = join(consumersRoot, 'node_modules/overnightworks-appkit');
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
			'overnightworks-appkit/appkit.css'
		);
		cpSync(stylesheet, join(outDir, 'appkit.css'));
		cpSync(join(dirname(stylesheet), 'fonts'), join(outDir, 'fonts'), { recursive: true });
	}
	return outDir;
}
