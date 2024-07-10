## Introduction
This example will teach you how to use the `metaflow.Snowflake` extension to pull a dataframe from a Snowflake database fetched in the [Snowflake marketplace](https://www.snowflake.com/en/data-cloud/marketplace/). You'll see how to run feature computation pipelines in parallel. 

This example uses the OpenAI API to compute summaries of website landing pages, but you can use this pattern to easily run any Python processing function in parallel. The [next lesson](../05-dbt/) will build on this example and deploy another workflow that runs dbt transformations each time this workflow completes.

## Setup

### Snowflake dependencies

To run this example, set up a secret in your Outerbounds/Metaflow `@secrets` manager containing the following dependencies:
```bash
SNOWFLAKE_USER=...
SNOWFLAKE_PASSWORD=...
SNOWFLAKE_ACCOUNT_IDENTIFIER=...
```

Place the secret name in the workflow code next to the `# TODO` comments.

#### Data marketplace 
In your Snowflake account, go to the [Snowflake marketplace entry for the `FREE_COUNTRY_DATASET`](https://app.snowflake.com/marketplace/listing/GZSTZRRVYL2/people-data-labs-free-company-dataset?pricing=free). Click the `Get` button.

### OpenAI dependencies
To run this example, set up a secret in your Outerbounds/Metaflow `@secrets` manager containing the following dependencies:
```bash
OPENAI_API_KEY=...
```
Place the secret name in the workflow code next to the `# TODO` comments.

### Code dependencies

Install the following in the local environment where you will interactively run Metaflow flows from:
```bash
pip install -U outerbounds metaflow-snowflake
```

## Run the workflow

```bash
python flow.py --environment=pypi run
```

## Deploy the workflow

```bash
python flow.py --environment=pypi argo-workflows create
```