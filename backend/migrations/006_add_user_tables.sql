-- Migration 006: Add User Authentication Tables
-- Created: 2025-12-29
-- Description: User and session management with Argon2 and Fernet security

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    password_hash TEXT NOT NULL,
    api_key_hash TEXT,
    api_key_encrypted TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
    order_mode VARCHAR(20) NOT NULL DEFAULT 'auto',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE
);

-- Indexes for users
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_users_order_mode ON users(order_mode);

-- User sessions table
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    session_token_hash TEXT NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_activity TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    revoked_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for user_sessions
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_is_active ON user_sessions(is_active);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON user_sessions(expires_at);

-- Comments
COMMENT ON TABLE users IS 'User authentication with Argon2 password hashing and Fernet API key encryption';
COMMENT ON TABLE user_sessions IS 'User session tracking for security audit';
COMMENT ON COLUMN users.order_mode IS 'Order execution mode: auto or semi_auto';
COMMENT ON COLUMN users.api_key_hash IS 'Argon2 hash for API key verification';
COMMENT ON COLUMN users.api_key_encrypted IS 'Fernet encrypted API key for retrieval';
