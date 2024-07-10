<svelte:head>
	<title>Home</title>
	<meta name="description" content="Svelte demo app" />
</svelte:head>

<div class='main'>
	<div class='message'>
		<h2>Chat with documents</h2>
		<p>
		The app is based on <a href="https://github.com/outerbounds/document-processing/tree/main/pdf-app">this code</a>.
		Upload one or more PDF files and use LMs to understand and chat with it. 
		For more examples, see<a href="https://github.com/outerbounds/document-processing/tree/main/01-snowflake">this project</a> which uses LMs to summarize HTML files while showing how to use Snowflake with Outerbounds. 
		</p>
	</div>
</div>

<style>
  .main {
    display: flex;
    flex-direction: column;
	align-items: center;
    justify-content: center;
    flex: 1;
    height: 100%;
    position: relative;
  }

  h2 {
	margin-bottom: 20px;
  }

  a {
	color: var(--green-200);
  }

  a:hover {
	color: var(--green-400);
  }

  .message {
	/* display: flex; */
    width: 30%;
    /* text-align: center; */
    margin: 20px;
	align-items: start;
  }

  .column {
    width: 50%;
    padding: 10px;
  }

  .chart {
    border: 1px solid #ccc;
    padding: 10px;
  }

  .main > .column {
    display: flex;
    flex-direction: column;
    align-items: center;
  }
</style>
