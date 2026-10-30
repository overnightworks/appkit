import './app.css';
import { mount } from 'svelte';
import { SignInPage } from 'overnightworks-appkit';

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
