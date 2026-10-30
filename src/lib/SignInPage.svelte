<script lang="ts">
	import LegalLinks from './LegalLinks.svelte';
	import type { SignInPageProps } from './types.ts';

	let { appName, state, legalLinks }: SignInPageProps = $props();
</script>

<svelte:head>
	<title>{appName}</title>
</svelte:head>

<div class="signin">
	<div class="grid-bg"></div>
	<div class="glow glow-primary"></div>
	<div class="glow glow-accent"></div>
	<main class="card">
		<span class="wordmark" data-text={appName}>{appName}</span>
		{#if state.page === 'signed-out'}
			<h1>You are logged out.</h1>
			<a class="action primary" href={state.signInHref} data-sveltekit-reload>Log in</a>
		{:else if state.page === 'login-failed'}
			<h1>Login failed</h1>
			<div class="banner" role="alert">
				<span class="fail-shape"><i></i></span>
				<span>Sign-in did not work. Please try again.</span>
			</div>
			<a class="action primary" href={state.signInHref} data-sveltekit-reload>Try again</a>
		{:else}
			<h1>No access</h1>
			<p>You are signed in, but this account has no access to {appName}.</p>
			{#if state.logOutAction !== undefined}
				<form class="log-out" method="post" action={state.logOutAction}>
					<button class="action secondary" type="submit">Log out</button>
				</form>
			{:else}
				{#if state.logOutFailure}
					<p role="alert">{state.logOutFailure}</p>
				{/if}
				<button class="action secondary" type="button" onclick={state.onLogOut}>Log out</button>
			{/if}
		{/if}
	</main>
	<LegalLinks links={legalLinks} />
</div>

<style>
	.signin {
		--glow-mix: 4%;
		--glow: color-mix(in srgb, var(--primary) var(--glow-mix), transparent);
		position: relative;
		overflow: hidden;
		min-height: 100dvh;
		box-sizing: border-box;
		padding: 36px 16px 24px;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 18px;
		background: var(--bg-deep);
		color: var(--text);
		font-family: 'Open Sans', system-ui, sans-serif;
	}
	:global(:root[data-theme='dark']) .signin {
		--glow-mix: 3%;
	}
	@media (prefers-color-scheme: dark) {
		:global(:root:not([data-theme='light'])) .signin {
			--glow-mix: 3%;
		}
	}
	.grid-bg {
		position: absolute;
		inset: 0;
		background-image:
			linear-gradient(var(--glow) 1px, transparent 1px),
			linear-gradient(90deg, var(--glow) 1px, transparent 1px);
		background-size: 40px 40px;
	}
	.glow {
		position: absolute;
		border-radius: 50%;
		filter: blur(70px);
		opacity: 0.15;
		pointer-events: none;
	}
	.glow-primary {
		width: 300px;
		height: 300px;
		background: var(--primary);
		top: -90px;
		right: -90px;
	}
	.glow-accent {
		width: 240px;
		height: 240px;
		background: var(--accent);
		bottom: -60px;
		left: -60px;
	}
	.card {
		position: relative;
		z-index: 1;
		width: 340px;
		max-width: 100%;
		box-sizing: border-box;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 16px;
		padding: 28px 22px 22px;
		text-align: center;
		background: var(--card-bg);
		border: 1px solid color-mix(in srgb, var(--primary) 18%, var(--border));
		border-radius: 6px;
	}
	.wordmark {
		position: relative;
		display: inline-block;
		font-family: 'Oswald', Impact, sans-serif;
		font-size: 27px;
		letter-spacing: 0.14em;
		text-transform: uppercase;
		color: var(--text);
		line-height: 1.1;
		overflow-wrap: anywhere;
	}
	.wordmark::before,
	.wordmark::after {
		content: attr(data-text);
		position: absolute;
		inset: 0;
		pointer-events: none;
		opacity: 0.85;
	}
	.wordmark::before {
		color: var(--primary);
		clip-path: inset(0 0 65% 0);
	}
	.wordmark::after {
		color: var(--accent);
		clip-path: inset(65% 0 0 0);
	}
	h1 {
		margin: 0;
		font-family: 'Oswald', Impact, sans-serif;
		font-weight: 400;
		font-size: 18px;
		letter-spacing: 0.03em;
		overflow-wrap: anywhere;
	}
	p {
		margin: 0;
		font-size: 14px;
		color: var(--text-muted);
	}
	.banner {
		display: flex;
		gap: 10px;
		align-items: flex-start;
		box-sizing: border-box;
		width: 100%;
		padding: 10px 12px;
		border: 1px solid var(--fail);
		border-left-width: 3px;
		border-radius: 4px;
		background: var(--fail-soft);
		font-size: 13.5px;
		text-align: left;
		color: var(--text);
	}
	.fail-shape {
		margin-top: 3px;
		display: inline-flex;
		color: var(--fail);
	}
	.fail-shape i {
		width: 12px;
		height: 12px;
		flex: none;
		display: inline-block;
		background: var(--fail);
		clip-path: polygon(50% 0%, 100% 100%, 0% 100%);
	}
	.action {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		box-sizing: border-box;
		width: 100%;
		min-height: 44px;
		padding: 0 14px;
		border: 1px solid transparent;
		border-radius: 4px;
		font-family: 'Oswald', Impact, sans-serif;
		font-size: 14px;
		letter-spacing: 0.05em;
		text-transform: uppercase;
		text-decoration: none;
		white-space: nowrap;
		cursor: pointer;
	}
	.log-out {
		display: contents;
	}
	.action.primary {
		background: var(--accent);
		border-color: var(--accent);
		color: var(--on-accent);
	}
	.action.secondary {
		background: transparent;
		border-color: var(--border);
		color: var(--text);
	}
	.action:focus-visible {
		outline: 2px solid var(--accent);
		outline-offset: 2px;
	}
</style>
