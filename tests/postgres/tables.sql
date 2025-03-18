-- Schema for the users table
CREATE TABLE users (
    id serial PRIMARY KEY,
    user_id VARCHAR (50) UNIQUE NOT NULL,
    chat_id VARCHAR (50) NOT NULL,
    status VARCHAR (50) NOT NULL DEFAULT 'denied'
);

-- Schema for the users_requests table
CREATE TABLE users_requests (
    id serial PRIMARY KEY,
    user_id VARCHAR (50) NOT NULL,
    message_id VARCHAR (50),
    chat_id VARCHAR (50),
    authentication VARCHAR (50) NOT NULL,
    "authorization" VARCHAR (255) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    rate_limits TIMESTAMP
);

-- Schema for the migrations table
CREATE TABLE migrations (
    id serial PRIMARY KEY,
    name VARCHAR (255) NOT NULL,
    version VARCHAR (255) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Schema for the messages table
CREATE TABLE messages (
    id serial PRIMARY KEY,
    message_id VARCHAR (50) NOT NULL,
    chat_id VARCHAR (50) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    message_type VARCHAR (50) NOT NULL,
    producer VARCHAR (50) NOT NULL,
    message_content_hash VARCHAR (64) NOT NULL,
    state VARCHAR (50) NOT NULL DEFAULT 'added'
);

-- Schema for the currency table
CREATE TABLE finance_currency (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    rate DECIMAL(10, 2) NOT NULL DEFAULT 0.0,
    last_update TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
