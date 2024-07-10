<script>
	import { page } from '$app/stores';
	import logo from '$lib/images/outerbounds.png';
	import github from '$lib/images/github.svg';
</script>

<header>
	<div class="corner-left">
		<a href="https://outerbounds.co/get-started">
			<img src={logo} alt="Outerbounds" />
		</a>
	</div>

	<nav>
		<ul>
			<li aria-current={$page.url.pathname === '/' ? 'page' : undefined}>
				<a href="/">Home</a>
			</li>
			<li aria-current={$page.url.pathname === '/single' ? 'page' : undefined}>
				<a href="/single">Single PDF</a>
			</li>
			<li aria-current={$page.url.pathname.startsWith('/batch') ? 'page' : undefined}>
				<a href="/batch">Batch workflow</a>
			</li>
		</ul>
	</nav>

	<div class="corner-right">
		<a href="https://github.com/outerbounds/document-processing/tree/main/pdf-app">
			<img src={github} alt="GitHub" />
		</a>
	</div>
</header>

<style>
	header {
		display: flex;
		flex: 0 0 auto;
		justify-content: space-between;
		background-color: var(--sand-100);
		height: var(--headerHeight);
	}

	.corner-left {
		width: 10em;
		height: var(--headerHeight);
	}

	.corner-left a {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 100%;
		height: 100%;
	}

	.corner-left img {
		width: 8em;
		height: 2em;
		object-fit: contain;
	}

	.corner-right {
		width: 3em;
		height: var(--headerHeight);
	}

	.corner-right a {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 100%;
		height: 100%;
	}

	.corner-right img {
		width: 3em;
		height: 2em;
		object-fit: contain;
	}

	nav {
		display: flex;
		justify-content: center;
		--background: var(--sand-300);
	}

	ul {
		position: relative;
		padding: 0;
		margin: 0;
		height: 3em;
		display: flex;
		justify-content: center;
		align-items: center;
		list-style: none;
		background: var(--sand-300);
		background-size: contain;
		border-radius: 0.25em;
	}

	li {
		position: relative;
		height: 100%;
	}

	li[aria-current='page']::before {
		--size: 6px;
		content: '';
		width: 0;
		height: 0;
		position: absolute;
		top: 0;
		left: calc(50% - var(--size));
		border: var(--size) solid transparent;
		border-top: var(--size) solid var(--color-theme-1);
	}

	nav a {
		display: flex;
		height: 100%;
		align-items: center;
		padding: 0 2.5rem;
		color: var(--color-text);
		font-weight: 700;
		font-size: 0.9rem;
		text-transform: uppercase;
		letter-spacing: 0.1em;
		text-decoration: none;
		transition: color 0.2s linear;
	}

	a:hover {
		color: var(--black);
		background-color: var(--sand-200);
		border-radius: 0.25em;
	}
</style>
