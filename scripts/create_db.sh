#!/bin/bash

exec > >(tee -a logs/app.log) 2>&1
set -x

# Load environment variables from .env file
export $(grep -v '^#' .env | grep -v '^TELEGRAM*' | xargs)

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
        fi
    else
        log_message "ERROR" "Invalid database name: $new_db_name"
        exit 1
    fi
}

# Function to create a new database
create_table() {
    local root_user=$1
    local new_db_name=$2
    local table_names=("${@:3}")
    local query=""
    for table_name in "${table_names[@]}"; do
        local command="${!table_name}"
        query+="$command "
    done
    query="BEGIN; $query COMMIT;"
    log_message "INFO" "Connecting to database '$new_db_name'..."
    log_message "INFO" "Creating tables..."
    sudo -u $root_user psql -d $new_db_name -c "$query" 2>&1
       
    if [[ $? -eq 0 ]]; then
        log_message "INFO" "All tables created successfully."
    else
        log_message "ERROR" "Error occurred while creating tables."
        exit 1
    fi
}

# Function to create a new user
create_linux_user() { 
    local user_name=$1
    local password=$2

    # Create the user with the specified username and set the user's password
    usradd_err=$(sudo useradd -m -s /bin/bash $user_name 2>&1)
    usradd_stat=$?
    if [[ $usradd_stat -eq 0 ]]; then
        log_message "INFO" "User $user_name created successfully."
        echo "$user_name:$password" | sudo chpasswd
        log_message "INFO" "Password for User $user_name created successfully."
    else
        log_message "WARNING" "$usradd_err"
    fi
}

# Main function
main() {
create_table_users="CREATE TABLE users (
    id INT NOT NULL PRIMARY KEY,
    family_id INT NOT NULL,
    name VARCHAR(32) NOT NULL,
    language CHAR(2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_verified BOOLEAN,
    is_main_user BOOLEAN,
    is_read_only BOOLEAN
);"

create_table_spendings="CREATE TABLE spendings (
    id SERIAL PRIMARY KEY,
    name VARCHAR(250) NOT NULL,
    buyer INT NOT NULL REFERENCES users(id),
    price NUMERIC NOT NULL,
    source INT NOT NULL REFERENCES sources_data(id),
    category INT NOT NULL REFERENCES categories_data(id),
    subcategory INT NOT NULL REFERENCES subcategories_data(id),
    date TIMESTAMP WITH TIME ZONE NOT NULL
);"

create_table_sources="CREATE TABLE sources_data (
    id SERIAL PRIMARY KEY,
    source_info JSONB NOT NULL
);"

create_table_categories="CREATE TABLE categories_data (
    id SERIAL PRIMARY KEY,
    category_info JSONB NOT NULL
);"

create_table_subcategories="CREATE TABLE subcategories_data (
    id SERIAL PRIMARY KEY,
    subcategory_info JSONB NOT NULL,
    category_id INT NOT NULL REFERENCES categories_data(id)
);"

table_names=(create_table_sources create_table_categories create_table_subcategories create_table_users create_table_spendings)

create_database "$root_user" "$new_db_name"
create_table "$root_user" "$new_db_name" "${table_names[@]}"
create_linux_user "$main_user" "$main_user_passwd"
create_linux_user "$common_user" "$common_user_passwd"
create_linux_user "$read_only_user" "$read_only_user_passwd"

}

main