# CalData Orchestration Tooling

This repository hosts code, documentation, and configuration for ETL/ELT orchestration.
It us currently structured as a Google Composer (managed Airflow) project,
though that is subject to change.


## Philosophy

We intend to do most data transformation in our data warehouses (i.e. ELT rather than ETL).
There is still need to do some custom loading, however!
This project is intended to do relatively simple loads into data warehouse tables,
and complex DAGs should be regarded with suspicion.

Most DAGs should have a single node.

## Local Development Workflow

Basic commands are driven from a [`justfile`](https://just.systems/man/en/).
Project variables are loaded from a `.env` file. To start, create your `.env` file:

```bash
cp .env.sample
```
and populate the variables therein.

Create a local dev environment (which uses `composer-dev` and `docker` under the hood):

```bash
just create-local-env
```

Start your dev environment:

```bash
just start
```

Then open a web browser and navigate to `localhost:8081` to view the Airflow UI.
You can view DAGs and their history from the UI, as well as trigger new test runs.

You can also run Airflow commands from the command line.
A couple of common ones are in the `justfile`:

```bash
just list-dags  # list the DAGs that Airflow sees.
just trigger $DAG  # trigger a specific DAG for testing.
```

## Deploying

Currently there is no CI/CD set up for this project.

You can then sync the DAGs with the GCS bucket:

```bash
just sync-dags
```

And you can sync the additional Python requirements with:

```bash
just sync-requirements
```
