"""Load feedback form data from CalInnovate sites"""
from __future__ import annotations

import random
import string
from datetime import datetime
from typing import cast

import pandas
import requests
from airflow.decorators import dag, task
from common.defaults import DEFAULT_ARGS
from google.cloud import bigquery

# TODO: parameterize over different sites
DATA_URL = (
    "https://api.alpha.ca.gov/WasHelpfulData/?url=covid19.ca.gov&requestor=datastudio"
)

default_args = {
    **DEFAULT_ARGS,
    "email": cast(list[str], DEFAULT_ARGS["email"]) + ["james.logan@cdph.ca.gov"],
}


@task
def load_feedback_data() -> None:
    """
    Load feedback data from api.alpha.ca.gov
    """
    # Load the raw JSON data
    data = requests.get(DATA_URL).json()

    # Convert to dataframe, rename columns to match destination table.
    df = pandas.DataFrame.from_records(data)
    df = (
        df.assign(
            timestamp=pandas.to_datetime(df.timestamp, utc=True),
            source="covid19",
        )
        .sort_values("timestamp", ascending=True)
        .rename(
            columns={
                "helpful": "is_helpful",
                "timestamp": "date_time_utc",
                "pagesection": "page_section",
            }
        )
    )

    client = bigquery.Client(project="dse-product-analytics-prd-bqd")
    schema = "prod_analytics_web"
    table = "ppf_data"
    tmp_table = f"{table}_tmp_{''.join(random.choices(string.ascii_lowercase, k=3))}"

    # In general we will pull the data from this endpoint multiple times, so we don't
    # want to just naively append it to BQ table as we'll get many duplicates for each
    # comment. So instead we upload to a temp table and then do a MERGE operation
    # into the actual table. It would be nice to use an *actual* temp table here so
    # that we wouldn't be responsible for cleaning it up, but I don't think that's
    # possible using tha pandas_gbq API, so keeping things simple.
    try:
        df.to_gbq(
            f"{schema}.{tmp_table}",
            project_id="dse-product-analytics-prd-bqd",
            if_exists="replace",
        )

        q = client.query(
            f"""
            MERGE INTO `{schema}.{table}` AS tgt
            USING `{schema}.{tmp_table}` AS src
            ON tgt.id = src.id
            WHEN NOT MATCHED THEN
            -- Insert ROW doesn't work for partitioned targets, unfortunately
            INSERT (
              id,
              site,
              url,
              is_helpful,
              comments,
              page,
              page_section,
              language,
              date_time_utc,
              source
            )
            VALUES (
              src.id,
              src.site,
              src.url,
              src.is_helpful,
              src.comments,
              src.page,
              src.page_section,
              src.language,
              src.date_time_utc,
              src.source
            )
            """,
            project="dse-product-analytics-prd-bqd",
        )
        # Drain the result -- not sure if this is entirely necessary
        for _ in q:
            pass
    finally:
        q = client.query(f"""DROP TABLE `{schema}.{tmp_table}`""")


@dag(
    description="Load CalInnovate Feedback form data",
    start_date=datetime(2022, 12, 19),
    schedule_interval="0 */6 * * *",
    default_args=default_args,
)
def load_cal_innovate_feedback_data():
    load_feedback_data()


run = load_cal_innovate_feedback_data()
