#!/bin/bash
SECRET_KEY="ThisIsSecretForJWTHS512SignatureAlgorithmThatMUSTHave64ByteLengt"
sudo docker build --build-arg "SECRET_KEY=$SECRET_KEY" --build-arg "OPENAI_API_KEY=sk-123" -t fragjetzt-langchain-langchain .