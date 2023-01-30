# Common commands for project

# Load from .env for local config or sensitive data
set dotenv-load

env_path := "composer/$LOCAL"
dags_path := "${DAGS_BUCKET}/dags"
test_path := "${DAGS_BUCKET}/data/test"
port := "8081"
rev := `git rev-parse --short HEAD`
image_arch := "linux/amd64"
image_tag := env_var_or_default("DEFAULT_IMAGE_TAG", "prod")
publish_image_tag := env_var_or_default("PUBLISH_IMAGE_TAG", "dev")
image_path := "${LOCATION}-docker.pkg.dev/$PROJECT/$DEFAULT_IMAGE_REPO/$DEFAULT_IMAGE_NAME"

# Create a local composer development environment
create-local-env:
  composer-dev create $LOCAL \
      --from-source-environment $SOURCE_ENVIRONMENT \
      --location $LOCATION \
      --project $PROJECT \
      --port {{port}} \
      --dags-path dags

_sync-local-env:
  cp requirements.txt {{env_path}}/requirements.txt
  cp variables.env {{env_path}}/variables.env
  echo "DEFAULT_IMAGE={{image_path}}:{{image_tag}}" >> {{env_path}}/variables.env

# Start the local composer development environment
start-local-env: _sync-local-env
  composer-dev start $LOCAL

# Restart the local composer development environment
restart-local-env: _sync-local-env
  composer-dev restart $LOCAL

# Stop the local composer development environment
stop-local-env:
  composer-dev stop $LOCAL

# Sync environment variables to the cloud environment
# (Right now, this only syncs the default image path)
sync-env-vars:
  gcloud composer environments update $SOURCE_ENVIRONMENT --project=$PROJECT --location=$LOCATION \
  --update-env-variables=DEFAULT_IMAGE={{image_path}}:{{image_tag}}

# Sync the dags/ folder to the GCP bucket for the cloud environment (deploys!)
sync-dags:
  gsutil rsync -d -r -x "airflow_monitoring\.py|.*\.pyc|.*\.ipynb_checkpoints.*" \
  dags {{dags_path}}

# Sync the requirements.txt file with the cloud environment
sync-requirements:
  gcloud composer environments update $SOURCE_ENVIRONMENT --project=$PROJECT --location=$LOCATION \
  --update-pypi-packages-from-file=requirements.txt \
  || true

# Deploy to the cloud environment
deploy: sync-requirements sync-env-vars sync-dags
  echo "Deployed to ${SOURCE_ENVIRONMENT}!"

# List the local DAGs
list-local-dags:
  composer-dev run-airflow-cmd $LOCAL dags list

# Trigger a DAG by name using the local deployment
trigger-local dag:
  composer-dev run-airflow-cmd $LOCAL dags trigger \
  -e `date -u +"%Y-%m-%dT%H:%M:%S%z"` {{dag}}

# Test a DAG by name using the local deployment
test-local-dag dag:
  composer-dev run-airflow-cmd $LOCAL \
  dags test {{dag}} `date -u +"%Y-%m-%dT%H:%M:%S%z"`

# Test a task by name using the local deployment
test-local-task dag task:
  composer-dev run-airflow-cmd $LOCAL \
  tasks test {{dag}} {{task}} `date -u +"%Y-%m-%dT%H:%M:%S%z"`

_sync-to-dest-directory:
  gsutil rsync -d -r -x "airflow_monitoring\.py|.*\.pyc|.*\.ipynb_checkpoints.*" \
  dags {{test_path}}

# Test a DAG on the composer cluster
test-dag dag: _sync-to-dest-directory
  gcloud composer environments run $SOURCE_ENVIRONMENT --project $PROJECT --location $LOCATION \
  dags test -- --subdir /home/airflow/gcs/data/test \
  {{dag}} `date -u +"%Y-%m-%dT%H:%M:%S%z"`

# Test a task on the composer cluster
test-task dag task: _sync-to-dest-directory
  gcloud composer environments run $SOURCE_ENVIRONMENT --project $PROJECT --location $LOCATION \
  tasks test -- --subdir /home/airflow/gcs/data/test \
  {{dag}} {{task}} `date -u +"%Y-%m-%dT%H:%M:%S%z"`

# Private rule to create an image repository in gcp
_create-image-repository:
  gcloud artifacts repositories describe --location $LOCATION --project $PROJECT $DEFAULT_IMAGE_REPO || \
  gcloud artifacts repositories create --location $LOCATION --project $PROJECT \
  --repository-format=docker $DEFAULT_IMAGE_REPO

# Build image
build:
  docker buildx build --platform {{image_arch}} \
  -t {{image_path}}:{{image_tag}} . 

# Build and publish and image
publish: build _create-image-repository
  docker push {{image_path}}:{{image_tag}} 
