# Common commands for project

# Load from .env for local config or sensitive data
set dotenv-load

local := "dev"
env_path := "composer" / local
port := "8081"

create-local-env:
  composer-dev create {{local}} \
      --from-source-environment $SOURCE_ENVIRONMENT$ \
      --location $LOCATION \
      --project $PROJECT \
      --port {{port}} \
      --dags-path dags

start:
  cp requirements.txt {{env_path}}/requirements.txt
  composer-dev start {{local}} 

restart:
  cp requirements.txt {{env_path}}/requirements.txt
  composer-dev restart {{local}}

sync-dags:
  gsutil rsync -d -r -x "airflow_monitoring\.py|.*\.pyc|.*\.ipynb_checkpoints.*" \
  dags $DAGS_BUCKET
