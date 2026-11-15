#!/bin/bash
set -e

# Update and install Docker and Docker Compose
apt-get update -y
apt-get install -y apt-transport-https ca-certificates curl software-properties-common git ufw

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
apt-get update -y
apt-get install -y docker-ce docker-compose-plugin

systemctl start docker
systemctl enable docker

# Firewall rules
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo "Host setup complete."
