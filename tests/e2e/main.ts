import './app.css';
import { mount } from 'svelte';
import { SignInPage } from 'overnightworks-appkit';

if (location.search === '?typed') {
	// A person typed the name; the app wrote the words around it.
	document.body.innerHTML = '<main><h1>Source <span class="as-typed">talks</span></h1></main>';
} else {
	mount(SignInPage, {
		target: document.body,
		props: {
			appName: 'Probe',
			state: { page: 'signed-out', signInHref: '/login' },
			legalLinks: [
				{ label: 'Imprint', href: '/imprint' },
				{ label: 'Privacy', href: '/privacy' }
			]
		}
	});
}
