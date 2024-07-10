<script lang="ts">
    import { onMount } from "svelte";
    export let spec: any;

    console.log('spec:', spec);
    
    onMount(async () => {
        const vegaEmbed = await import('vega-embed');
        const el = document.getElementById('vis');
        try {
            await vegaEmbed.default(el, spec, { mode: "vega-lite" });
        } catch (error) {
            el.innerHTML = `<div style="color:red;">
            <p>JavaScript Error: ${error.message}</p>
            <p>See the javascript console for the full traceback.</p>
            </div>`;
            console.error(error);
        }
    });

</script>
  
<div id="vis"></div>
  