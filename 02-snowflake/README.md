## Introduction
This example will teach you how to use the `metaflow.Snowflake` extension and the Metaflow `@dbt` extension to run dbt jobs. It builds on the [previous example](../04-parallel-processing/) to trigger the `dbt run` on completion of the `MarketIntelIngestion` workflow. 

## Setup

### dbt dependencies

Edit your [dbt profile](./profiles.yml) to your liking:
```
company_analytics:
  outputs:
    dev:
      account: ...
      database: FREE_COMPANY_DATASET_OUTPUTS
      password: ...
      role: ...
      schema: ...
      threads: 8
      type: snowflake
      user: ...
      warehouse: ...
  target: dev
```

### Snowflake dependencies
To run this example, set up a secret in your Outerbounds/Metaflow `@secrets` manager containing the following dependencies:
```bash
SNOWFLAKE_USER=...
SNOWFLAKE_PASSWORD=...
SNOWFLAKE_ACCOUNT_IDENTIFIER=...
```
Place the secret name in the workflow code next to the `# TODO` comments.

### Code dependencies

Install the following in the local environment where you will interactively run Metaflow flows from:
```bash
pip install -r requirements.txt
```

## Run the workflow

```bash
python flow.py --environment=conda run
```

## Deploy the workflow

```bash
python flow.py --environment=conda argo-workflows create
```

### Trigger the end-to-end pipeline
Now return to the [previous example](../04-parallel-processing/) and deploy the workflow:

```bash
cd ../04-parallel-processing
python flow.py --environment=conda argo-workflows trigger
```