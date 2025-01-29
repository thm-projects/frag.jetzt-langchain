#!/bin/bash
SECRET_KEY="ThisIsSecretForJWTHS512SignatureAlgorithmThatMUSTHave64ByteLengt"
sudo docker build --build-arg "SECRET_KEY=$SECRET_KEY" -t fragjetzt-langchain-langchain .