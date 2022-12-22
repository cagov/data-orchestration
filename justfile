# Common commands for project

# Load from .env for local config or sensitive data
set dotenv-load

env_path := "composer/$LOCAL"
port := "8081"

create-local-env:
  composer-dev create $LOCAL \
      --from-source-environment $SOURCE_ENVIRONMENT \
      --location $LOCATION \
      --project $PROJECT \
      --port {{port}} \
      --dags-path dags

start:
  cp requirements.txt {{env_path}}/requirements.txt
  composer-dev start $LOCAL

restart:
  cp requirements.txt {{env_path}}/requirements.txt
  composer-dev restart $LOCAL

sync-dags:
  gsutil rsync -d -r -x "airflow_monitoring\.py|.*\.pyc|.*\.ipynb_checkpoints.*" \
  dags $DAGS_BUCKET

sync-requirements:
   gcloud composer environments update $SOURCE_ENVIRONMENT --project=$PROJECT --location=$LOCATION \
   --update-pypi-packages-from-file=requirements.txt \
   || true

list-dags:
  composer-dev run-airflow-cmd $LOCAL dags list

trigger dag:
  composer-dev run-airflow-cmd $LOCAL dags trigger \
  -e `date -u +"%Y-%m-%dT%H:%M:%S%z"` {{dag}}
