#!/bin/bash
DIR=$(sudo docker container inspect fragjetzt-backend 2>/dev/null | grep "com.docker.compose.project.working_dir" | sed -rn 's/[^"]*"[^"]*": "([^"]*)",/\1/p')
if [ -z "$DIR" ]; then
  echo "Please start the compose project before this one."
  exit 1
fi
# if not orchestration, standard secret key
if [[ "$DIR" != *-orchestration ]]; then
  SECRET_KEY="ThisIsSecretForJWTHS512SignatureAlgorithmThatMUSTHave64ByteLengt"
else
  # compose project
  SECRET_KEY="$(cat $DIR/environments/backend.env | grep SPRING_JWT_SECRET | cut -d '=' -f 2)"
fi
ORIGINS="http://localhost:4200"
sudo docker run --rm -it -e SECRET_KEY="$SECRET_KEY" -e ORIGINS="$ORIGINS" \
  -p 6001:8080 \
  -v "./app:/code/app" -v "./files:/code/files" \
  --network langchain_network --network fragjetzt \
  --name fragjetzt-ai-provider \
  fragjetzt-langchain-langchain