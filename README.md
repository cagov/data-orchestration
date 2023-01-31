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
just start-local-env
```

Then open a web browser and navigate to `localhost:8081` to view the Airflow UI.
You can view DAGs and their history from the UI, as well as trigger new test runs.

You can also run Airflow commands from the command line.
A couple of common ones are in the `justfile`:

```bash
just list-local-dags  # list the DAGs that Airflow sees.
just trigger-local $DAG  # trigger a specific DAG for testing.
```

DAGs which use a `KubernetesPodOperator` are more difficult to test as it requires
you to have a local kubernetes setup.

Any easier approach is to use [this](https://cloud.google.com/composer/docs/how-to/using/testing-dags#error-check) guide,
which copies your test DAGs to a test directory in the GCS bucket and runs it in the real cluster.
This should be done with care as you could interfere with the production environment.

A workflow for testing a local kubernetes-based dag is:

1. Publish a new docker image:
    ```bash
    just publish
    ```
2. Update the image tag for the project `KubernetesPodOperator`s to point at your new image.
3. Trigger the task you want to run:
    ```bash
    just test-task <dag-id> <task-id>
    ```

## Deploying

Currently there is no CI/CD set up for this project.

A basic deployment workflow:

1. Publish a new docker image:
    ```bash
    PUBLISH_IMAGE_TAG=prod just publish
    ```
2. Update the Airflow environment
    ```
    just deploy
    ```
