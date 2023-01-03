"""Load feedback form data from CalInnovate sites"""
from __future__ import annotations

import random
import string
from datetime import datetime, timedelta

import pandas
import requests
from airflow.decorators import dag, task
from google.cloud import bigquery

DATA_URLS = {
    "covid19": "https://fa-go-alph-d-002.azurewebsites.net/WasHelpfulData/?url=covid19.ca.gov&requestor=datastudio",
    "drought": "https://fa-go-alph-d-002.azurewebsites.net/FeedbackData/?url=drought.ca.gov&requestor=datastudio",
    "cannabis": "https://fa-go-alph-d-002.azurewebsites.net/FeedbackData/?url=cannabis.ca.gov&requestor=datastudio",
    "innovation": "https://fa-go-alph-d-002.azurewebsites.net/FeedbackData/?url=innovation.ca.gov&requestor=datastudio",
    "designsystem": "https://fa-go-alph-d-002.azurewebsites.net/FeedbackData/?url=designsystem.webstandards.ca.gov&requestor=datastudio",  # noqa: E501
    "ca": "https://fa-go-alph-d-002.azurewebsites.net/FeedbackData/?url=www.ca.gov&requestor=datastudio",
}

DEFAULT_ARGS = {
    "owner": "CalData",
    "depends_on_past": False,
    "email": ["odi-caldata-dse@innovation.ca.gov", "james.logan@cdph.ca.gov"],
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


@task
def load_feedback_data() -> None:
    """
    Load feedback data from api.alpha.ca.gov
    """
    dfs = []
    # Iterate over the various CalInnovate domains. This could be broken up into
    # separate tasks to isolate failures, that's probably overkill right now.
    for source, url in DATA_URLS.items():
        # Load the raw JSON data
        print(f"Reading data for {source}")
        data = requests.get(url).json()
        if not data:
            continue

        # Convert to dataframe, rename columns to match destination table.
        df = pandas.DataFrame.from_records(data)
        df = (
            df.assign(
                timestamp=pandas.to_datetime(df.timestamp, utc=True),
                source=source,
            )
            .sort_values("timestamp", ascending=True)
            .rename(
                columns={
                    "helpful": "is_helpful",
                    "timestamp": "date_time_utc",
                    "pagesection": "page_section",  # Some, but not all sites use `pagesection`
                }
            )
        )
        dfs.append(df)

    final = pandas.concat(dfs, axis=0, ignore_index=True)

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
        final.to_gbq(
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
    default_args=DEFAULT_ARGS,
)
def load_cal_innovate_feedback_data():
    load_feedback_data()


run = load_cal_innovate_feedback_data()
