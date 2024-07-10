from metaflow import (
    FlowSpec,
    step,
    pypi,
    pypi_base,
    Snowflake,
    secrets,
    Parameter,
    kubernetes,
)
from constants import (
    COMPANY_DATA_QUERY,
    MARKETPLACE_DB,
    SCHEMA,
    WH,
    OUT_TABLE_NAME,
    OUTPUTS_DB,
    CREATE_OUTPUT_DB_QUERY,
)


@pypi_base(python="3.11")
class MarketIntelIngestion(FlowSpec):

    n_chunks = Parameter("n_chunks", default=5)
    samples_per_chunk = Parameter("samples_per_chunk", default=5)

    @secrets(sources=["snowflake-ob-content-universe"])
    @pypi(
        packages={
            "snowflake-connector-python": "3.10.0",
            "pandas": "2.2.2",
            "pyarrow": "16.0.0",
        }
    )
    @kubernetes
    @step
    def start(self):
        from utils import add_https

        with Snowflake(database=MARKETPLACE_DB, schema=SCHEMA, warehouse=WH) as sf:
            df = sf.get(COMPANY_DATA_QUERY, return_type="pandas")

        df["WEBSITE"] = df["WEBSITE"].apply(add_https)
        n_rows = df.shape[0]
        max_rows_per_chunk = n_rows // self.n_chunks
        self.chunks = [
            df.iloc[i : i + max_rows_per_chunk]
            for i in range(0, n_rows, max_rows_per_chunk)
        ]
        self.next(self.process, foreach="chunks")

    @secrets(
        sources=["snowflake-ob-content-universe", "openai_ob_content_universe"]
    )  # TODO: Add secret for your Snowflake account and OpenAI API key
    @pypi(
        packages={
            "nltk": "3.8.1",
            "openai": "1.30.1",
            "beautifulsoup4": "4.12.3",
            "pandas": "2.2.2",
        }
    )
    @kubernetes
    @step
    def process(self):
        from utils import summarize_and_classify
        import pandas as pd

        print(f"Processing chunk with {self.input.shape[0]} rows.")
        _active_df = (
            self.input
            if self.samples_per_chunk == -1
            else self.input[: self.samples_per_chunk]
        )
        _df_data = []
        for _, row in _active_df.iterrows():
            new_cols = summarize_and_classify(row["WEBSITE"])
            _df_data.append({**row.to_dict(), **new_cols})
        self.df = pd.DataFrame(_df_data)
        self.next(self.aggregate_dfs)

    @secrets(sources=["snowflake-ob-content-universe"])
    @kubernetes
    @pypi(
        packages={
            "snowflake-connector-python": "3.10.0",
            "pandas": "2.2.2",
            "pyarrow": "16.0.0",
        }
    )
    @step
    def aggregate_dfs(self, inputs):
        import pandas as pd

        self.df = pd.concat([input.df for input in inputs]).reset_index(drop=True)
        with Snowflake(database=OUTPUTS_DB, schema=SCHEMA, warehouse=WH) as sf:
            sf.execute(CREATE_OUTPUT_DB_QUERY)
            sf.execute(
                pd.io.sql.get_schema(self.df, OUT_TABLE_NAME).replace(
                    "CREATE TABLE", "CREATE TABLE IF NOT EXISTS"
                )
            )
            sf.put(self.df, OUT_TABLE_NAME)
        self.next(self.end)

    @step
    def end(self):
        pass


if __name__ == "__main__":
    MarketIntelIngestion()
