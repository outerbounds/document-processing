from metaflow import (
    FlowSpec,
    step,
    dbt,
    secrets,
    Snowflake,
    kubernetes,
    conda_base,
    conda,
    retry,
    pypi,
    trigger_on_finish,
)


@trigger_on_finish(flow="MarketIntelIngestion")
@conda_base(python="3.11")
class MarketIntelTransformations(FlowSpec):

    @conda(packages={"dbt-snowflake": "1.8.1"})
    @secrets(sources=["snowflake-ob-content-universe"])
    @dbt(project_dir="./company_analytics", generate_docs=True)
    @kubernetes
    @step
    def start(self):
        self.next(self.end)

    @retry
    @conda(
        packages={
            "snowflake-connector-python": "3.10.0",
            "pandas": "2.2.2",
            "pyarrow": "16.0.0",
            "pyyaml": "6.0.1",
        }
    )
    @secrets(sources=["snowflake-ob-content-universe"])
    @kubernetes
    @step
    def end(self):
        with Snowflake(
            database="FREE_COMPANY_DATASET_OUTPUTS",
            schema="public",
            warehouse="compute_wh",
        ) as sf:
            self.df = sf.get("SELECT * FROM VALID_WEBSITES", return_type="pandas")
        print(f"There are {self.df.shape[0]} valid websites in the dataset.")


if __name__ == "__main__":
    MarketIntelTransformations()
