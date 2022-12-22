# Common commands for project

# Load from .env for local config or sensitive data
set dotenv-load

env_path := "composer/$LOCAL"
port := "8081"

# Create a local composer development environment
create-local-env:
  composer-dev create $LOCAL \
      --from-source-environment $SOURCE_ENVIRONMENT \
      --location $LOCATION \
      --project $PROJECT \
      --port {{port}} \
      --dags-path dags

# Start the local composer development environment
start:
  cp requirements.txt {{env_path}}/requirements.txt
  composer-dev start $LOCAL

# Restart the local composer development environment
restart:
  cp requirements.txt {{env_path}}/requirements.txt
  composer-dev restart $LOCAL

# Sync the dags/ folder to the GCP bucket for the cloud environment (deploys!)
sync-dags:
  gsutil rsync -d -r -x "airflow_monitoring\.py|.*\.pyc|.*\.ipynb_checkpoints.*" \
  dags $DAGS_BUCKET

# Sync the requirements.txt file with the cloud environment
sync-requirements:
   gcloud composer environments update $SOURCE_ENVIRONMENT --project=$PROJECT --location=$LOCATION \
   --update-pypi-packages-from-file=requirements.txt \
   || true

# Deploy to the cloud environment
deploy: sync-requirements sync-dags
  echo "Deployed to ${SOURCE_ENVIRONMENT}!"

# List the local DAGs
list-dags:
  composer-dev run-airflow-cmd $LOCAL dags list

# Trigger a DAG by name
trigger dag:
  composer-dev run-airflow-cmd $LOCAL dags trigger \
  -e `date -u +"%Y-%m-%dT%H:%M:%S%z"` {{dag}}
