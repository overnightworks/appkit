import { svelte } from '@sveltejs/vite-plugin-svelte';
import { defineConfig } from 'vitest/config';

export default defineConfig({
	test: {
		coverage: {
			provider: 'v8',
			reporter: ['lcov', 'text-summary'],
			include: ['src/lib/**'],
			// The generated words hold data and one loader line; the consumer build proves them.
			exclude: ['**/*.test.ts', 'src/lib/words/**']
		},
		projects: [
			{
				plugins: [svelte()],
				resolve: { conditions: ['browser'] },
				test: {
					name: 'client',
					include: ['src/**/*.test.ts'],
					exclude: ['src/**/*.ssr.test.ts'],
					environment: 'jsdom'
				}
			},
			{
				plugins: [svelte()],
				test: { name: 'server', include: ['src/**/*.ssr.test.ts'], environment: 'node' }
			}
		]
	}
});
