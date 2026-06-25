CREATE SCHEMA IF NOT EXISTS budget;
SET search_path TO budget;

CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY, -- Telegram ID
    name VARCHAR(255),
    is_admin BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS accounts (
    id SERIAL PRIMARY KEY,
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
