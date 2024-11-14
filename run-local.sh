#!/bin/bash
DIR=$(sudo docker container inspect fragjetzt-backend 2>/dev/null | grep "com.docker.compose.project.working_dir" | sed -rn 's/[^"]*"[^"]*": "([^"]*)",/\1/p')
if [ -z "$DIR" ]; then
  echo "Please start the compose project before this one."
  exit 1
fi
# if not orchestration, standard secret key
if [[ "$DIR" != *-orchestration ]]; then
  export SECRET_KEY="ThisIsSecretForJWTHS512SignatureAlgorithmThatMUSTHave64ByteLengt"
else
  # compose project
  export SECRET_KEY="$(cat $DIR/environments/backend.env | grep SPRING_JWT_SECRET | cut -d '=' -f 2)"
fi
export ORIGINS="http://localhost:4200"
export CHROMA_HOST="localhost"
export CHROMA_PORT="6002"
export POSTGRES_HOST="localhost"
export POSTGRES_PORT="6003"
cd "$(dirname "$0")"
poetry run langchain serve --port 6001