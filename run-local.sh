#!/bin/bash
export SECRET_KEY="54f32ace6dac1315faa7a50ed1e10cae0d928d30094d1438ac1fa4c249fa8ce7"
export ORIGINS="http://localhost:4200"
export CHROMA_HOST="localhost"
export CHROMA_PORT="6002"
export POSTGRES_HOST="localhost"
export POSTGRES_PORT="6003"
cd "$(dirname "$0")"
poetry run langchain serve