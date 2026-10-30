import { svelte } from '@sveltejs/vite-plugin-svelte';
import { defineConfig } from 'vitest/config';

export default defineConfig({
	test: {
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
