#!/bin/bash
SECRET_KEY="54f32ace6dac1315faa7a50ed1e10cae0d928d30094d1438ac1fa4c249fa8ce7"
ORIGINS="http://localhost:4200"
sudo docker run --rm -it -e SECRET_KEY="$SECRET_KEY" -e ORIGINS="$ORIGINS" \
  -p 8000:8080 \
  -v "./app:/code/app" -v "./files:/code/files" \
  --network langchain_network --network fragjetzt \
  --name fragjetzt-ai-provider \
  fragjetzt-langchain-langchain