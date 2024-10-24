#!/bin/bash
set -x

# Load environment variables from .env file
export $(grep -v '^#' ../.env | xargs)

# Variables from the environment
ROOT_DBNAME=$ROOT_DBNAME
NEW_DBNAME=$NEW_DBNAME
ROOT_USER=$ROOT_USER
ROOT_PASSWORD=$ROOT_PASSWORD
MAIN_USER=$MAIN_USER
MAIN_USER_PASSWORD=$MAIN_USER_PASSWORD
COMMON_USER=$COMMON_USER
COMMON_USER_PASSWORD=$COMMON_USER_PASSWORD
READ_ONLY_USER=$READ_ONLY_USER
READ_ONLY_USER_PASSWORD=$READ_ONLY_USER_PASSWORD
HOST=$HOST
PORT=$PORT

# Logging function
log_message() {
  local LEVEL=$1
  local MESSAGE=$2
  echo "$(date +'%Y-%m-%d %H:%M:%S') - $LEVEL - $MESSAGE" >> logs/app.log
  echo "$(date +'%Y-%m-%d %H:%M:%S') - $LEVEL - $MESSAGE"
}

log_message "INFO" "Loaded NEW_DBNAME: $NEW_DBNAME"

# Function to create a new database
create_database() {
  local ROOT_DBNAME=$1
  local ROOT_USER=$2
  local ROOT_PASSWORD=$3
  local HOST=$4
  local PORT=$5
  local NEW_DBNAME=$6

  log_message "INFO" "Creating database $NEW_DBNAME..."

  # Check if the database name is valid
  if [[ $NEW_DBNAME =~ ^[a-zA-Z0-9_]+$ ]]; then
    # Check if the database already exists
    PGPASSWORD=$ROOT_PASSWORD psql -h $HOST -p $PORT -U $ROOT_USER -d $ROOT_DBNAME -tc "SELECT 1 FROM pg_database WHERE datname = '$NEW_DBNAME'" | grep -q 1
    if [ $? -eq 0 ]; then
      log_message "INFO" "Database $NEW_DBNAME already exists."
    else
      # Create the database
      PGPASSWORD=$ROOT_PASSWORD psql -h $HOST -p $PORT -U $ROOT_USER -d $ROOT_DBNAME -c "CREATE DATABASE $NEW_DBNAME"
      if [ $? -eq 0 ]; then
        log_message "INFO" "Database $NEW_DBNAME created successfully."
      else
        log_message "ERROR" "PostgreSQL error while creating the database $NEW_DBNAME."
      fi
    fi
  else
    log_message "ERROR" "Invalid database name: $NEW_DBNAME"
    exit 1
  fi
}

# Main function
main() {
  # Create the database if it doesn't exist
  create_database "$ROOT_DBNAME" "$ROOT_USER" "$ROOT_PASSWORD" "$HOST" "$PORT" "$NEW_DBNAME"
}

main
