# Common commands for project

# Load from .env for local config or sensitive data
set dotenv-load

env_path := "composer/$LOCAL"
dags_path := "${DAGS_BUCKET}/dags"
test_path := "${DAGS_BUCKET}/data/test"
port := "8081"
rev := `git rev-parse --short HEAD`
image_arch := "linux/amd64"
image_name := "analytics"

# Create a local composer development environment
create-local-env:
  composer-dev create $LOCAL \
      --from-source-environment $SOURCE_ENVIRONMENT \
      --location $LOCATION \
      --project $PROJECT \
      --port {{port}} \
      --dags-path dags

# Start the local composer development environment
start-local-env:
  cp requirements.txt {{env_path}}/requirements.txt
  composer-dev start $LOCAL

# Restart the local composer development environment
restart-local-env:
  cp requirements.txt {{env_path}}/requirements.txt
  composer-dev restart $LOCAL

stop-local-env:
  composer-dev stop $LOCAL

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
deploy: sync-requirements sync-dags
  echo "Deployed to ${SOURCE_ENVIRONMENT}!"

# List the local DAGs
list-local-dags:
  composer-dev run-airflow-cmd $LOCAL dags list

# Trigger a DAG by name using the local deployment
trigger-local dag:
  composer-dev run-airflow-cmd $LOCAL dags trigger \
  -e `date -u +"%Y-%m-%dT%H:%M:%S%z"` {{dag}}

# Test a DAG on the composer cluster
test-task dag task:
  gsutil rsync -d -r -x "airflow_monitoring\.py|.*\.pyc|.*\.ipynb_checkpoints.*" \
  dags {{test_path}}

  gcloud composer environments run $SOURCE_ENVIRONMENT --project $PROJECT --location $LOCATION \
  tasks test -- --subdir /home/airflow/gcs/data/test \
  {{dag}} {{task}} `date -u +"%Y-%m-%dT%H:%M:%S%z"`

# Private rule to create an image repository in gcp
_create-image-repository:
  gcloud artifacts repositories describe --location $LOCATION --project $PROJECT $IMAGE_REPO || \
  gcloud artifacts repositories create --location $LOCATION --project $PROJECT \
  --repository-format=docker $IMAGE_REPO

# Build image
build:
  docker buildx build --platform {{image_arch}} \
  -t ${LOCATION}-docker.pkg.dev/$PROJECT/$IMAGE_REPO/`basename {{image_name}}`:{{rev}} .

# Build and publish and image
publish: build _create-image-repository
  docker push ${LOCATION}-docker.pkg.dev/$PROJECT/$IMAGE_REPO/`basename {{image_name}}`:{{rev}}
