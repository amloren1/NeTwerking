#!/bin/bash

docker stop netwerkerapi_mongo_1

docker system prune -f

docker-compose up -d --build mongo