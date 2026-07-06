#!/bin/bash
# Sync local database with production server
# Use only for local development!

echo "Stopping local containers and removing old DB volume..."
docker compose down -v

echo "Fixing permissions for backups folder..."
sudo chown -R $USER:$USER ./backups/

echo "Downloading latest backups from server..."
scp root@167.172.33.210:~/my_family_budget/backups/* ./backups/

# echo "Starting local containers (bot will automatically restore DB from the new backup)..."
# docker compose up -d

echo "Done! Local database is synced with the server."
