<script lang='ts'>
	import { browser } from '$app/environment';
    import { onMount } from 'svelte';
    import { writable, get } from 'svelte/store';
  
    export let url = '';
    export let data = '';
  
    let pdf: any = null;
    let pageNum = writable(1);
    let gotoPageNum = 1;
    let totalPages = writable(0);
    let canvas: any;
    let context: any;

    const base64ToArrayBuffer = (base64: string) => {
        const binaryString = window.atob(base64.replace(/\s/g, ''));
        const len = binaryString.length;
        const bytes = new Uint8Array(len);
        for (let i = 0; i < len; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        return bytes.buffer;
    };
    
    const renderPage = async (num: any) => {
        if (!pdf) return;
        const page = await pdf.getPage(num);
        const viewport = page.getViewport({ scale: 1 });
        canvas.width = viewport.width;
        canvas.height = viewport.height;
        const renderContext = {
            canvasContext: context,
            viewport: viewport
        };
    
        page.render(renderContext);
    };
  
    const nextPage = () => {
        pageNum.update(n => {
            if (n < get(totalPages)) {
                const newPageNum = n + 1;
                renderPage(newPageNum);
                gotoPageNum = newPageNum;
                return newPageNum;
            }
            return n;
        });
    };
  
    const prevPage = () => {
        pageNum.update(n => {
            if (n > 1) {
                const newPageNum = n - 1;
                renderPage(newPageNum);
                gotoPageNum = newPageNum;
                return newPageNum;
            }
            return n;
        });
    };
    const loadPdf = async () => {
        if (browser) {
            
            // @ts-ignore
            const pdfjsLib = await import('pdfjs-dist/webpack');
            if (data) {
                const pdfData = base64ToArrayBuffer(data);
                pdf = await pdfjsLib.getDocument({ data: pdfData }).promise;
            } else if (url) {
                pdf = await pdfjsLib.getDocument(url).promise;
            }
            if (pdf) {
                totalPages.set(pdf.numPages as number);
                context = canvas.getContext('2d');
                renderPage(get(pageNum));
            }
        
        }
    }
    
    onMount(async () => {
        context = canvas.getContext('2d');
        if ( browser ) { 
            loadPdf();
        }
    });

    $: url, data, totalPages, loadPdf();

    const rerenderPdf = () => {
        if (gotoPageNum < 1 || gotoPageNum > get(totalPages)) {
            return;
        }
        pageNum.set(gotoPageNum);
        renderPage(gotoPageNum);
    }

</script>
  
<style>
    canvas {
        min-height: 10%;
        max-height: 100%;
        min-width: 20%;
        max-width: 100%;
    }

    .pdf-controller {
        display: flex;
        flex-direction: row;
        justify-content: space-between; 
        margin-top: 1rem;
        margin-bottom: .25rem;
        width: 100%;
    }

    .paginate-btn {
        display: flex; 
        justify-content: center;
        align-items: center;
        margin-right: 1rem;
    }

    .page-ctrl {
        display: flex;
        justify-content: flex-end;
        align-items: center;
        margin-left: auto; 
        /* margin-right: 1rem; */
    }

    .goto-page-input {
        width: 3rem;
        margin-right: 1rem;
    }

</style>

<div class='pdf-controller'>
    <button class='paginate-btn' on:click={prevPage} disabled={$pageNum <= 1}>Previous</button>
    <button class='paginate-btn' on:click={nextPage} disabled={$pageNum >= $totalPages}>Next</button>
    <div class='page-ctrl'> 
        <input 
            class='goto-page-input' 
            type='number' 
            bind:value={gotoPageNum} 
            on:change={rerenderPdf} 
            min={1} 
            max={$totalPages} 
        /> 
        <p>{$pageNum} / {$totalPages} </p>
    </div>
</div>
  
<canvas bind:this={canvas} />
