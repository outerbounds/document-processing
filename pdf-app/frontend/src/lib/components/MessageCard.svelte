<script lang="ts">
	export let width: string | undefined = undefined;
</script>

<div style={`width: ${width || 'auto'};`}>
	<slot />
</div>

<style>
	div { 
		position: relative;
		z-index: 10;
		box-shadow: var(--shadow-base);
		border-radius: var(--radius-md);
		background-color: var(--sand-100);
		padding: 1rem; 
		margin: 0.5rem 0; 
        width: 67%;

	}
</style>