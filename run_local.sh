#!/bin/bash

if ! docker ps | grep -E -q "dynamodb-local.*Up"; then
    echo -e "Iniciando dynamodb-local\n"
    docker run -d -p 8000:8000 amazon/dynamodb-local -jar DynamoDBLocal.jar -sharedDb

    echo -e "Criando tabela local...\n"
    aws dynamodb create-table --table-name reddit-posts-gatherer-last-searched-date-table \
        --attribute-definitions \
        AttributeName=id,AttributeType=N \
        --key-schema \
        AttributeName=id,KeyType=HASH \
        --billing-mode PAY_PER_REQUEST --endpoint-url http://localhost:8000
fi

echo "Iniciando API...\n"
sam local start-api --env-vars env.json
