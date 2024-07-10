declare module '$lib/pdfViewer/Document.svelte';
declare module '$lib/pdfViewer/Page.svelte';
declare module '$lib/utils/target_dimension.ts' {
    export type MultipleOf90 = number;
    export type CalcViewport = (page: any, rotation: MultipleOf90) => any;
    export function preferThisWidth(width: number): CalcViewport;
    export function preferThisHeight(height: number): CalcViewport;
}
declare module '$lib/utils/vite.ts' {
    export function set_pdfjs_context(): void;
}

declare module '$lib/components/PdfViewer.svelte';