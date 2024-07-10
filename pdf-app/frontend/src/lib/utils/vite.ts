import { BROWSER } from 'esm-env';
import * as pdfjs from 'pdfjs-dist';
import { onDestroy, setContext } from 'svelte';

// let pdfjs;
// if (typeof window !== 'undefined') {
// 	pdfjs = require('pdfjs-dist');
// }

export function set_pdfjs_context() {
	if (BROWSER && typeof window !== 'undefined') {
		const worker = new pdfjs.PDFWorker({
			port: new Worker(
				new URL('pdfjs-dist/legacy/build/pdf.js', import.meta.url)
			) as unknown as null,
		});
		setContext('svelte_pdfjs_worker', worker);
		onDestroy(() => worker.destroy());
	}
}
