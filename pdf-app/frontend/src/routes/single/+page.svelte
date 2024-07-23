<script lang='ts'>

	import { onMount } from "svelte";
	import { loader } from './loader';
	import { writable } from 'svelte/store';

	import resetIcon from '$lib/images/reset.svg';
	import closePdfIcon from '$lib/images/close-pdf.svg';
	import pdfIcon from '$lib/images/pdf.svg';

	// PDF things
	import PdfViewer from '$lib/components/PdfViewer.svelte';
	import { toast } from '@zerodevx/svelte-toast';

	// FastAPI server
	let endpoint: string = 'http://0.0.0.0:8000';
	let uploadAPI: string = 'upload-pdf-file';
	let uploadUrlAPI: string = 'upload-pdf-url';
	let chatPdfAPI: string = 'pdf-chat'; 

	// Svelte stores for PDF file upload
	let loading = writable(false);
	let hasUploadedFile = writable(false);
	let uploadedFileLocalPath = writable(null);
	let base64Data = writable('');
	let pdfUrl = '';

	// user AI interaction
	import MessageCard from "../../lib/components/MessageCard.svelte";
	let loadingChatTurn = writable(false);

	// The user has one conversation. 
	let messages = writable([]);
	// Current status of what the user has typed.
	let prompt = '';

	let data: any; 
	let pageNum = writable(1);
  
	async function uploadFile(e: any) {
		base64Data.set('');
		hasUploadedFile.set(false);
		loading.set(true);

		const file = e.target.files[0];
		const formData = new FormData();
		formData.append('uf', file);

		const res = await fetch(
			`${endpoint}/${uploadAPI}`,
			{
				method: 'POST',
				body: formData
			}
		);

		toast.push('File uploaded successfully!');

		if (res.ok) {
			// Wait for API server to init the RAG stuff.
			data = await res.json();
			hasUploadedFile.set(true);
			// Load the PDF file for viewing in browser.
			const base64String: any = await pdfToBase64(file);
			base64Data.set(base64String);
			uploadedFileLocalPath.set(file.name);
			// Use initial summary of the PDF given by LM API.
			messages.update((msgs) => {
				return [...msgs, { 'content': data.summary, 'role': 'assistant' }];
			});
			console.log('[DEBUG] Add AI summary to message history.');
			loading.set(false);
		} else {
			loading.set(false);
		}
	}

	let name = 'pdf-file.pdf'

	function handlePdfUrlKeyPress(event) {
		if (event.key === 'Enter') {
			if (name === '') {
				name = pdfUrl.split('/').pop();
			}
			uploadFileFromUrl(pdfUrl);
		}
	}

	async function uploadFileFromUrl(url) {
		base64Data.set('');
		hasUploadedFile.set(false);
		loading.set(true);

		const name = 'curr-data';

		try {
			// Fetch the PDF from the URL
			const response = await fetch(url);
			if (!response.ok) {
				throw new Error(`Failed to fetch PDF: ${response.statusText}`);
			}

			// Get the blob of the PDF
			const blob = await response.blob();
			const reader = new FileReader();

			reader.onloadend = () => {
				if (typeof reader.result === 'string') {
					// Convert blob to Base64
					const base64String = reader.result.split(',')[1];
					base64Data.set(base64String);
					// hasUploadedFile.set(true);
					// loading.set(false);
				} else {
					console.error('Error: result is not a string');
					// loading.set(false);
				}
			};
			uploadedFileLocalPath.set(url);

			reader.onerror = () => {
				console.error('Error reading blob as Base64');
				// loading.set(false);
			};

			// Read the blob as Data URL
			reader.readAsDataURL(blob);

			const formData = new FormData();
			formData.append('url', url);
			formData.append('name', name);

			console.log('[DEBUG] Uploading file from URL:', url, 'to', `${endpoint}/${uploadUrlAPI}`);

			// Send the file to the server
			const res = await fetch(`${endpoint}/${uploadUrlAPI}?url=${encodeURIComponent(url)}&name=${name}`, {
				method: 'POST',
				headers: {
					'accept': 'application/json'
				},
				body: formData
			});

			if (res.ok) {
				data = await res.json();
				// Use initial summary of the PDF given by LM API.
				messages.update((msgs) => {
					return [...msgs, { 'content': data.summary, 'role': 'assistant' }];
				});
				console.log('[DEBUG] Add AI summary to message history.');
				loading.set(false);
				hasUploadedFile.set(true);
			} else {
				loading.set(false);
			}

		} catch (error) {
			console.error('Error uploading file from URL:', error);
			loading.set(false);
		}
	}

	const pdfToBase64 = (file: any) => {
		return new Promise((resolve, reject) => {
			const reader = new FileReader();
			reader.onloadend = () => {
				const base64String = (reader.result as string).split(',')[1];
				resolve(base64String);
			};
			reader.onerror = (error) => {
				reject(error);
			};
			reader.readAsDataURL(file);
		});
	};

	async function chat() {
		loadingChatTurn.set(true);

		// TODO: Filter out empty prompts / prompts with only spaces / etc.
		messages.update((msgs) => {
			return [...msgs, { 'content': prompt, 'role': 'user' }];
		});

		console.log('[DEBUG] User prompt:', prompt);
		const queryParams = new URLSearchParams({
			question: prompt,
			ctx_messages: JSON.stringify($messages)
		});
		const res = await fetch(
			`${endpoint}/${chatPdfAPI}?${queryParams.toString()}`,
			{
				method: 'GET',
				headers: {
					'accept': 'application/json'
				}
			}
		);

		if (res.ok) {
			const data = await res.json();
			console.log('[DEBUG] AI response:', data.answer);
			messages.update((msgs) => [...msgs, { 'content': data.answer, 'role': 'assistant' }]);
			loadingChatTurn.set(false);
		} else {
			console.log('[ERROR]', res);
			loadingChatTurn.set(false);
		}
	}

	function handleKeyPress(event) {
		if (event.key === 'Enter' && !event.shiftKey) {
			event.preventDefault();
			chat();
			prompt = '';
		}
		if (event.key === 'Enter' && event.shiftKey) {
			prompt += '\n';
		}
	}

	onMount(() => {
		const loaderNode = document.querySelector('.loader-container');
		loader(loaderNode, loading);
	});

</script>
  
<svelte:head>
	<title>About</title>
	<meta name="description" content="About this app" />
</svelte:head>

<div class='main'>
	
	<div class='loader-container'></div>
	{#if $hasUploadedFile}
		<div class='left-col'>
			<div class='header-left-col'>
				<button 
					class="close-pdf"
					on:click={
						() => {
							messages.set([]);
							hasUploadedFile.set(false);
							uploadedFileLocalPath.set(null);
							base64Data.set('');
						}
					}
				>
					<img src={closePdfIcon} alt="Close" />
				</button>
				<div>
					<p class='current-pdf-label'>
						{#if $uploadedFileLocalPath}
							{$uploadedFileLocalPath}
						{:else}
							'No file uploaded'
						{/if}
					</p>
				</div>	
			</div>
			<div class='pdf'> 
				<PdfViewer data={$base64Data} pageNum={$pageNum} />
			</div>		
		</div>
		<div class='right-col'>
			<div class='header-right-col'>
				<h2 class='right-col-title'>Chat</h2>
				<button 
					class="reset-chat"
					on:click={
						() => {
							messages.set([]);
							toast.push('Chat history emptied.');
						}
					}
				>
					<img src={resetIcon} alt="Reset" />
				</button>
			</div>
			<div class='message-container'>
				{#each $messages as message, i}
					<div class="message {message.role === 'user' ? 'message-user' : 'message-ai'}">
						<MessageCard width='75%'>
							<p style="text-align: 'left'}; color: black'};">
								{message.role === 'user' ? 'User' : 'AI'}: {message.content}
							</p>
						</MessageCard>
					</div>
				{/each}
			</div>
			<div class='chat-bar'>
				<input 
					type="text" 
					placeholder="Type your prompt..."
					class="chat-input"
					bind:value={prompt}
					on:keypress={handleKeyPress}
				>
				<button 
					class="send-button"
					on:click={
						() => {
							chat();
						}
					}
				>
					Send
				</button>
			</div>
		</div>
	{:else}
		{#if $loading}
			<div style='opacity: 0.25;'>
				<div class='both-col'>
				</div>
			</div>
		{:else}
			<div class='both-col'>
				<h2> 
					Chat with a PDF
				</h2>
				<input
					type="text"
					placeholder="Enter the URL to a PDF file..."
					class="pdf-url-input"
					bind:value={pdfUrl}
					on:keypress={handlePdfUrlKeyPress}
				/>
				<label for="file-upload" class="custom-file-upload">
					<img src={pdfIcon} alt="PDF" />
					<p class='file-upload-text'>
						Upload PDF
					</p>
				</label>
				<input id="file-upload" type="file" accept=".pdf" on:change={e => uploadFile(e)} />
			</div>
		{/if}

	{/if}

</div>


<style>

	.main {
		display: flex;
		align-items: center;  
		justify-content: center;
		flex: 1;
		height: 100%;
		overflow: hidden;
		position: relative;
	}


	.loader-container {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
	}

	.both-col {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		overflow: hidden;
		width: 100%;
	}

	.left-col, .right-col {
		display: flex;
		flex-direction: column;
		justify-content: flex-start;
		align-items: center;
		width: 50%;
		height: calc(100vh - 2 * var(--headerHeight));
		overflow: hidden;
	}

	.left-col {
		background: linear-gradient(to right, var(--sand-100), var(--sand-200));
	}

	.custom-file-upload {
		display: flex;
		padding: 6px 12px;
		cursor: pointer;
		align-items: center;
		background-color: var(--sand-300);
		border-radius: 8px;
		white-space: nowrap; 
		width: auto; 
	}

	.custom-file-upload:hover {
		background-color: var(--purple-200);
		border-style: solid;
		border-width: 3px;
		border-color: var(--purple-300);
	}

	.current-pdf-label {
		text-align: start;
		font-style: italic;
		font-size: 1rem;
		color: var(--black);
	}

	input[type="file"] {
		display: none;
	} 

	.pdf-url-input {
		padding: 6px 12px;
		border-radius: 8px;
		border: none;
		margin-top: 2rem;
		margin-bottom: 2rem;
		width: auto;
	}

	.file-upload-text {
		color: var(--black);
		cursor: pointer;
		margin-left: .5rem;
	}

	.right-col {
		background: linear-gradient(to right, var(--sand-200), var(--sand-100));
	}

	.header-right-col, .header-left-col {
		margin-top: 2rem;
		padding-left: 10%;
		padding-right: 10%;
		display: flex;
		flex-direction: row;
		align-items: center;
		justify-content: space-between;
		height: 4vh;
		min-height: 4vh;
	}

	.header-right-col {
		width: 100%;
	}

	.header-left-col {
		width: auto;
		min-width: 70%;
		max-width: 100%;
	}

	.right-col-title {
		text-align: start;
		margin-left: 2rem;
	}

	.close-pdf {
		border: none;
		cursor: pointer;
		transition: background-color 0.3s ease;
		margin-right: 1rem;
	}

	.reset-chat {
		border: none;
		cursor: pointer;
		transition: background-color 0.3s ease;
		margin-right: 2rem;
	}

	.pdf {
		/* min-height: 10%;
		max-height: 82vh; */
		z-index: 10;
	}

	.message-container {
		overflow-y: auto;
		height: calc(100vh - 4 * var(--headerHeight));
		max-height: calc(100vh - 6 * var(--headerHeight));
		width: 100%;
		margin-left: 2rem;
		margin-right: 2rem;
	}

	.chat-bar {
		position: absolute;
		bottom: 2%;
		width: 46%;
		background-color: var(--sand-300);
		padding: 1rem;
		border-radius: 8px;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); 
		display: flex;
		justify-content: space-between;
		z-index: 20;
	}

	.chat-input {
		flex: 1; 
		border: none; 
		padding: 0.5rem; 
		border-radius: 8px;
		background-color: var(--sand-100); 
	}

	.chat-input:focus-visible {
		border: 2px solid var(--purple-300);
		border-radius: 3px;
		outline: none;
	}

	.send-button {
		padding: 0.5rem 1rem;
		border: none;
		border-radius: 8px;
		background-color: var(--sand-100);
		color: var(--purple-400);
		cursor: pointer;
		transition: background-color 0.3s ease;
		margin-left: 1rem;
	}

	.send-button:hover {
		background-color: var(--purple-400);
		color: var(--sand-100);
	}

	.message {
		display: flex;
		margin-bottom: .5rem;
		margin-top: .5rem;
		margin-left: 2rem;
		margin-right: 2rem;
	}

	.message-user {
		justify-content: flex-end;
	}

	.message-ai {
		justify-content: flex-start;
	}

</style>
