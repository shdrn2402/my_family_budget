#!/bin/bash

: <<'DOCSTRING'
This script automates the setup of a PostgreSQL database, creating tables and roles with specified permissions for a budgeting application.

Dependencies:
- PostgreSQL must be installed and running.
- Environment variables are loaded from a .env file located in the same directory.

Workflow:
1. Creates a database if it does not already exist.
2. Sets up tables using `IF NOT EXISTS` to avoid overwriting existing data.
3. Sets up roles with specified permissions, ensuring roles are created only if they do not already exist.
4. Configures pg_hba.conf to use md5 authentication for local connections.
5. Restarts PostgreSQL to apply changes.

Environment Variables:
- ROOT_USER: PostgreSQL root user with privileges to create databases and roles.
- NEW_DBNAME: Name of the database to be created.
- MAIN_USER, COMMON_USER, READ_ONLY_USER: Names of database roles with different access levels.
- MAIN_USER_PASSWORD, COMMON_USER_PASSWORD, READ_ONLY_USER_PASSWORD: Passwords for the respective roles.

Logging:
- Outputs both to the terminal and to logs/app.log.

Usage:
Execute this script as a superuser to ensure sufficient permissions for database and role creation.

DOCSTRING

exec > >(tee -a logs/app.log) 2>&1
# set -x

# Load environment variables from .env file
set -a
source .env
set +a
# export $(grep -v '^#' .env | grep -v '^TELEGRAM*' | xargs)


# Variables from the environment
new_db_name=$NEW_DBNAME
root_user=$ROOT_USER
main_user=$MAIN_USER
main_user_passwd=$MAIN_USER_PASSWORD
common_user=$COMMON_USER
common_user_passwd=$COMMON_USER_PASSWORD
read_only_user=$READ_ONLY_USER
read_only_user_passwd=$READ_ONLY_USER_PASSWORD

# Logging function
log_message() {
    local level=$1
    local message=$2
    echo "$(date +'%Y-%m-%d %H:%M:%S') - $level - $message" >> logs/app.log
    echo "$(date +'%Y-%m-%d %H:%M:%S') - $level - $message"
}

# Function to create a new database
create_database() {
    local root_user=$1
    local new_db_name=$2

    log_message "INFO" "Creating database $new_db_name..."

    # Check if the database name is valid
    if [[ $new_db_name =~ ^[a-zA-Z0-9_]+$ ]]; then
        result=$(sudo -u $root_user psql -c "\l" | grep -w "$new_db_name")
        if [[ -n $result ]]; then
            log_message "WARNING" "Database '$new_db_name' already exists!"
        else
            sudo -u $root_user psql -c "CREATE DATABASE $new_db_name"
            log_message "INFO" "Database $new_db_name created successfully."
            
            log_message "INFO" "Creating schema $new_db_name..."
            sudo -u $root_user psql -d $new_db_name -c "CREATE SCHEMA $new_db_name"
            log_message "INFO" "Schema $new_db_name created successfully."
        fi
    else
        log_message "ERROR" "Invalid database name: $new_db_name"
        exit 1
    fi
}

# Function to create tables
create_table() {
    local root_user=$1
    local new_db_name=$2
    local table_names=("${@:3}")
    local query=""
    local table_list=""

    for table_name in "${table_names[@]}"; do
        local command="${!table_name}"
        query+="$command "
        table_list+="$table_name, "
    done

    # Remove the last character ", " from table_list
    table_list="${table_list%, }"

    query="SET SEARCH_PATH TO $new_db_name; BEGIN; $query COMMIT;"
    log_message "INFO" "Connecting to database '$new_db_name'..."
    log_message "INFO" "Creating tables..."
    sudo -u $root_user psql -v ON_ERROR_STOP=1 -d $new_db_name -c "$query" 2>&1
       
    if [[ $? -eq 0 ]]; then
        log_message "INFO" "Following tables created successfully: $table_list"
    else
        log_message "ERROR" "Error occurred while creating tables."
        exit 1
    fi
}

# Function to create roles
create_roles() {
    local root_user=$1
    local new_db_name=$2
    local role_names=("${@:3}")
    local query=""
    local role_list=""

    for role_name_var in "${role_names[@]}"; do
        local role_name="${!role_name_var}"
        local query_var="${role_name_var}_query"
        local command="${!query_var}"

        # Add a check for existing role before creation
        query+="DO \$\$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '${role_name}') THEN
                $command
            END IF;
        END
        \$\$; "
        
        role_list+="$role_name, "
    done

    # Remove the trailing comma and space from the role list
    role_list="${role_list%, }"

    log_message "INFO" "Connecting to database '$new_db_name'..."
    log_message "INFO" "Creating roles..."
    
    sudo -u $root_user psql -v ON_ERROR_STOP=1 -d $new_db_name -c "$query" 2>&1
       
    if [[ $? -eq 0 ]]; then
        log_message "INFO" "Following roles created successfully (if they did not exist): $role_list"
    else
        log_message "ERROR" "Error occurred while creating roles."
        exit 1
    fi
}


# Main function
main() {
# Define SQL queries for table creation
users="CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY, -- Telegram User ID
    family_id INT NOT NULL,
    name VARCHAR(64) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);"

accounts="CREATE TABLE IF NOT EXISTS accounts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL, -- e.g., 'Visa 4787', 'Cash'
    type VARCHAR(20) CHECK (type IN ('bank', 'credit_card', 'cash')),
    balance NUMERIC(12, 2) DEFAULT 0
);"

categories="CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    parent_id INT REFERENCES categories(id) ON DELETE CASCADE -- Allows subcategories
);"

transactions="CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    account_id INT REFERENCES accounts(id),
    category_id INT REFERENCES categories(id),
    amount NUMERIC(12, 2) NOT NULL,
    description TEXT,
    date TIMESTAMP WITH TIME ZONE NOT NULL,
    external_id VARCHAR(255) UNIQUE, -- Hash to prevent duplicates during import
    source_type VARCHAR(20) CHECK (source_type IN ('manual', 'import_xls'))
);"

table_names=(users accounts categories transactions)

# Define queries to create roles
main_user_query="CREATE USER $main_user WITH PASSWORD '$main_user_passwd' CREATEROLE;
GRANT CONNECT ON DATABASE $new_db_name TO $main_user;
GRANT USAGE ON SCHEMA $new_db_name TO $main_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA $new_db_name TO $main_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA $new_db_name TO $main_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA $new_db_name GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO $main_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA $new_db_name GRANT USAGE, SELECT ON SEQUENCES TO $main_user;"

common_user_query="CREATE USER $common_user WITH PASSWORD '$common_user_passwd';
GRANT CONNECT ON DATABASE $new_db_name TO $common_user;
GRANT USAGE ON SCHEMA $new_db_name TO $common_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA $new_db_name TO $common_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA $new_db_name TO $common_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA $new_db_name GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO $common_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA $new_db_name GRANT USAGE, SELECT ON SEQUENCES TO $common_user;"

read_only_user_query="CREATE USER $read_only_user WITH PASSWORD '$read_only_user_passwd';
GRANT CONNECT ON DATABASE $new_db_name TO $read_only_user;
GRANT USAGE ON SCHEMA $new_db_name TO $read_only_user;
GRANT SELECT ON ALL TABLES IN SCHEMA $new_db_name TO $read_only_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA $new_db_name GRANT SELECT ON TABLES TO $read_only_user;"

user_names=(main_user common_user read_only_user)

create_database "$root_user" "$new_db_name"
create_table "$root_user" "$new_db_name" "${table_names[@]}"
create_roles "$root_user" "$new_db_name" "${user_names[@]}"

log_message "INFO" "Filling tables with initial data..."
sudo -u $root_user psql -d $new_db_name -f scripts/seed_data.sql

  # Path to the pg_hba.conf file
  pg_hba_conf="/etc/postgresql/16/main/pg_hba.conf"

  # Change authentication method to md5 for local connections
  sudo sed -i '/^local[[:space:]]\+all[[:space:]]\+all[[:space:]]\+peer$/s/peer/md5/' "$pg_hba_conf"

  # Restart PostgreSQL server to apply changes
  sudo systemctl restart postgresql
}

main