import { sveltekit } from '@sveltejs/kit/vite';

/** @type {import('vite').UserConfig} */
const config = {
	plugins: [sveltekit()],
	test: {
		include: ['src/**/*.{test,spec}.{js,ts}']
	},
	optimizeDeps: {
		exclude: [
		  	'pdfjs-dist/build/pdf.worker.mjs', // Adjust the path as per your actual file path
			'pdfjs-dist'
		],
	},
};


export default config;
