#!/bin/bash

# Define a function to check if the last command succeeded
check_success() {
    if [ $? -eq 0 ]; then
        echo "Success: $1"
    else
        echo "Error: $1"
        exit 1
    fi
}


echo "Stopping NGINX..."
sudo service nginx stop
check_success "Stopped NGINX"


echo "Stopping all Docker containers..."
docker_container_ids=$(docker ps -a -q)
if [ -n "$docker_container_ids" ]; then
    docker stop $docker_container_ids
    check_success "Stopped all Docker containers"
else
    echo "No Docker containers to stop."
fi


echo "Removing unused Docker objects..."
docker system prune -f
check_success "Removed unused Docker objects"


echo "Removing all Docker images..."
docker rmi $(docker images -q) -f
check_success "Removed all Docker images"

echo "Starting Docker containers..."
docker-compose up -d
check_success "Started Docker containers"

echo "Starting NGINX..."
sudo service nginx start
check_success "Started NGINX"

echo "Deployment completed successfully."
