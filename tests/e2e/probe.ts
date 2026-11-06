import type { Page } from '@playwright/test';

/** Resolves CSS declarations such as `{ color: 'var(--text)' }` to the computed values of the named properties. */
export function resolveStyle(
	page: Page,
	declarations: Record<string, string>,
	properties: readonly string[]
): Promise<Record<string, string>> {
	return page.evaluate(
		([declared, names]) => {
			const probe = document.createElement('div');
			for (const [name, value] of Object.entries(declared)) probe.style.setProperty(name, value);
			document.body.append(probe);
			const style = getComputedStyle(probe);
			const resolved = Object.fromEntries(names.map((name) => [name, style.getPropertyValue(name)]));
			probe.remove();
			return resolved;
		},
		[declarations, properties] as const
	);
}
