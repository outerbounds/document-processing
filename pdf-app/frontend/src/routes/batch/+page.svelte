<script lang='ts'>
	import { writable, get } from 'svelte/store';
	import { toast } from '@zerodevx/svelte-toast';
	import { onMount } from "svelte";
	import { loader } from './loader';

	// Store for managing the list of URLs
	const urls = writable([]);
	const names = writable([]);
	const loading = writable(false);
	const workflowCompletedState = writable(false);

	// Server endpoint for uploading PDF files and fetching the chart
	let endpoint: string = 'http://0.0.0.0:8000';
	let uploadAPI: string = 'upload-url-list-file';

	let newUrl = '';
	let name = '';
	let message = '';

	function addUrl() {
		if (newUrl.trim() !== '') {
			if (get(urls).includes(newUrl)) {
				toast.push('URL already exists');
				return;
			}
			urls.update(n => [...n, newUrl]);
			newUrl = '';
			if (name.trim() !== '') {
				names.update(n => [...n, name]);
				name = '';
			} else {
				const newId = get(urls).length;
				names.update(n => [...n, `untitled-${newId}`]);
			}
			toast.push(`URL ${get(urls)[get(urls).length - 1]} added with name ${get(names)[get(names).length - 1]}`);
		}
	}

	async function fitSearchModel() {
		if (get(urls).length === 0) {
			toast.push('Please add at least one URL');
			return;
		}
		loading.set(true);
		workflowCompletedState.set(false);

		const urlNamePairs = get(urls).map((url, index) => {
			return { url, name: get(names)[index] };
		});
		const pdfsStr = urlNamePairs.map(pair => {
			return `${pair.name}: ${pair.url}`;
		}).join(`|||`);

		console.log(pdfsStr);

		const res = await fetch(`${endpoint}/${uploadAPI}?text_ls=${pdfsStr}`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
			}
		});

		message = await res.text();
		
		loading.set(false);
		workflowCompletedState.set(true);
		toast.push('Workflow completed');

	}

	onMount(() => {
		const loaderNode = document.querySelector('.loader-container');
		loader(loaderNode, loading);
	});
</script>

<div class="main">
	<div class='loader-container'></div>

	{#if $workflowCompletedState}
		<h2> {message} </h2>
		<button class="buttons" on:click={() => workflowCompletedState.set(false)}>Reset</button>
	{:else}
		<div class='url-list' style="opacity: {$loading ? 0.1 : 1}">
			<h2>Add URLs to PDF Documents</h2>
			<div>
				<input 
					type="text" 
					class="input-text"
					bind:value={newUrl} 
					on:keypress={e => e.key === 'Enter' && addUrl()}
					placeholder="Enter pdf url (e.g., to arxiv paper)" 
				/>
				<div class="name-add-row">
					<input 
						type="text" 
						class="input-text"
						bind:value={name} 
						on:keypress={e => e.key === 'Enter' && addUrl()}
						placeholder="Name" 
					/>
					<button class="button-row" on:click={addUrl}>
						<span>Add URL</span>
					</button>
				</div>
			</div>
			<div class="url-items">
				{#each $urls as url, index (url)}
					<div class="url-item">
						<a href={url} target="_blank">{`${url}: ${$names[index]}`}</a>
					</div>
				{/each}
			</div>
			<button class="buttons" on:click={fitSearchModel}>Fit search model</button>
		</div>	
	{/if}
</div>

<style>
	.main {
		display: flex;
		align-items: center;  
		justify-content: center;
		flex-direction: column;
		flex: 1;
		height: 100%;
		overflow: hidden;
		position: relative;
	}

	h2 {
		margin-bottom: 30px;
	}

	.input-text {
		width: 100%;
		padding: 10px;
		height: 30px;
		border-radius: 2rem;
		border: 1px solid #ccc;
		margin-top: 15px;
		margin-bottom: 15px;
	}

	.loader-container {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		z-index: 1000;
	}

	.pdf-content-graph {
		width: 75%;
		height: 75%;
	}
	
	.button-row {
		padding: 10px 20px;
		background-color: var(--green-100);
		border-radius: 1rem;
		cursor: pointer;
		margin-left: 20px;
	}

	.buttons {
		padding: 10px 20px;
		background-color: var(--green-100);
		border-radius: 1rem;
		border: none;
		cursor: pointer;
		margin-top: 20px;
		margin-bottom: 20px;
	}

	.name-add-row {
		display: flex;
		flex-direction: row;
		align-items: center;
		justify-content: space-between;
	}

	.url-items {
		margin-top: 20px;
	}

	.url-item {
		margin: 10px 0;
	}

	a {
		color: var(--green-300);
		text-decoration: none;
	}
</style>
