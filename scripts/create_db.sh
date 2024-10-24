  #!/bin/bash

  set -x

  # Path to the pg_hba.conf file
  PG_HBA_CONF="/etc/postgresql/16/main/pg_hba.conf"

  # Change authentication method to md5
  sudo sed -i 's/peer/md5/g' $PG_HBA_CONF

  # Restart PostgreSQL server to apply changes
  sudo systemctl restart postgresql

  # Load environment variables from .env file
  export $(grep -v '^#' .env | grep -v '^TELEGRAM*' | xargs)

  # Variables from the environment
  PORT=$PORT
  HOST=$HOST
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


  # Logging function
  log_message() {
      local LEVEL=$1
      local MESSAGE=$2
      echo "$(date +'%Y-%m-%d %H:%M:%S') - $LEVEL - $MESSAGE" >> logs/app.log
      echo "$(date +'%Y-%m-%d %H:%M:%S') - $LEVEL - $MESSAGE"
  }

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
            result=$(PGPASS=$ROOT_PASSWORD psql -U $ROOT_USER -h $HOST -p $PORT -d $ROOT_DBNAME -tc \
            "SELECT count(*) FROM pg_database WHERE datname = '$NEW_DBNAME'" 2>&1)
          if [[ $result -ne 0 ]]; then
              log_message "INFO" "Database $NEW_DBNAME already exists."
          else
              # Create the database
              PGPASS=$ROOT_PASSWORD psql -U $ROOT_USER -h $HOST -p $PORT -d $ROOT_DBNAME -c "CREATE DATABASE $NEW_DBNAME" 2>&1
              if [ $? -eq 0 ]; then
                  log_message "INFO" "Database $NEW_DBNAME created successfully."
              else
                  log_message "ERROR" "PostgreSQL error while creating the database $NEW_DBNAME: $?"
                  exit 1
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