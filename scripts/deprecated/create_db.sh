#!/bin/bash

set -e # Exit immediately if a command exits with a non-zero status

# Load environment variables
if [ -f .env ]; then
    source .env
else
    echo "Error: .env file not found! Please copy env.example to .env and fill it."
    exit 1
fi

echo "Cleaning up old database and user if they exist..."
# Drop old DB and user if we are doing a fresh start
sudo -u postgres psql -v ON_ERROR_STOP=0 <<EOF
DROP DATABASE IF EXISTS ${DB_NAME};
DROP USER IF EXISTS ${DB_USER};
EOF

echo "Creating database schema and tables..."

sudo -u postgres psql -v ON_ERROR_STOP=1 <<EOF
-- 1. Create the application user
CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';

-- 2. Create the database
CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};

-- 3. Connect to the new database
\c ${DB_NAME}

-- 4. Create Schema
CREATE SCHEMA IF NOT EXISTS budget AUTHORIZATION ${DB_USER};
SET search_path TO budget;

-- 5. Create Tables
CREATE TABLE IF NOT EXISTS families (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY, -- Telegram ID
    family_id INT NOT NULL REFERENCES families(id),
    name VARCHAR(255),
    is_admin BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS accounts (
    id SERIAL PRIMARY KEY,
    family_id INT NOT NULL REFERENCES families(id),
    owner_id BIGINT REFERENCES users(id), -- Nullable for family accounts
    name JSONB NOT NULL,
    type VARCHAR(50) NOT NULL -- e.g., 'cash', 'card', 'transit'
);

CREATE TABLE IF NOT EXISTS account_aliases (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    account_id INT REFERENCES accounts(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name JSONB NOT NULL,
    parent_id INT REFERENCES categories(id)
);

CREATE TABLE IF NOT EXISTS item_aliases (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    category_id INT REFERENCES categories(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    account_id INT REFERENCES accounts(id),
    category_id INT REFERENCES categories(id),
    amount NUMERIC(12, 2) NOT NULL,
    description TEXT,
    comment TEXT,
    date TIMESTAMP WITH TIME ZONE NOT NULL,
    external_id VARCHAR(255) UNIQUE, -- Hash to prevent duplicates during import
    source_type VARCHAR(20) CHECK (source_type IN ('manual', 'import_xls', 'manual_text')),
    status VARCHAR(20) DEFAULT 'confirmed' CHECK (status IN ('draft', 'pending', 'confirmed', 'adjustment'))
);

-- 6. Grant Privileges
GRANT ALL PRIVILEGES ON SCHEMA budget TO ${DB_USER};
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA budget TO ${DB_USER};
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA budget TO ${DB_USER};
ALTER DEFAULT PRIVILEGES IN SCHEMA budget GRANT ALL ON TABLES TO ${DB_USER};
ALTER DEFAULT PRIVILEGES IN SCHEMA budget GRANT ALL ON SEQUENCES TO ${DB_USER};
EOF

echo "✅ Database initialized successfully!"