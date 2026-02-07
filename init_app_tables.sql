-- ChatBI Application Database Schema
-- Single migration to create all required tables

-- Create datasources table
CREATE TABLE IF NOT EXISTS datasources (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(500),
    type VARCHAR(50) NOT NULL,
    connection_info JSONB NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now(),
    last_used_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_datasources_name ON datasources(name);
CREATE INDEX IF NOT EXISTS ix_datasources_type ON datasources(type);

-- Create chat_sessions table
CREATE TABLE IF NOT EXISTS chat_sessions (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    title VARCHAR(255),
    user_id VARCHAR(100) NOT NULL,
    datasource_id VARCHAR(36) REFERENCES datasources(id),
    context JSONB,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    last_active TIMESTAMP NOT NULL DEFAULT now(),
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);

-- Create chat_messages table
CREATE TABLE IF NOT EXISTS chat_messages (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL REFERENCES chat_sessions(id),
    role VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT now(),
    table_metadata JSONB,
    query_sql TEXT,
    execution_time INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);

-- Create visualizations table
CREATE TABLE IF NOT EXISTS visualizations (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    message_id VARCHAR(36) NOT NULL REFERENCES chat_messages(id),
    chart_type VARCHAR(50) NOT NULL,
    chart_config JSONB NOT NULL,
    data JSONB,
    title VARCHAR(255),
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);

-- Create query_history table
CREATE TABLE IF NOT EXISTS query_history (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    datasource_id VARCHAR(36) NOT NULL REFERENCES datasources(id),
    user_id VARCHAR(100),
    sql TEXT NOT NULL,
    execution_time_ms INTEGER NOT NULL,
    row_count INTEGER NOT NULL,
    error VARCHAR,
    status VARCHAR(20) NOT NULL DEFAULT 'success',
    executed_at TIMESTAMP NOT NULL DEFAULT now(),
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_query_history_datasource_id ON query_history(datasource_id);
CREATE INDEX IF NOT EXISTS idx_query_history_executed_at ON query_history(executed_at);

-- Create chat_history table
CREATE TABLE IF NOT EXISTS chat_history (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    conversation_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(100),
    timestamp TIMESTAMP NOT NULL,
    question TEXT,
    sql TEXT,
    row_count INTEGER,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    model VARCHAR(50),
    execution_time_ms INTEGER,
    usage JSONB,
    field_metadata JSONB,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_chat_history_conversation_id ON chat_history(conversation_id);
CREATE INDEX IF NOT EXISTS ix_chat_history_user_id ON chat_history(user_id);

-- Create saved_queries table
CREATE TABLE IF NOT EXISTS saved_queries (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    sql TEXT NOT NULL,
    datasource_id VARCHAR(36) NOT NULL REFERENCES datasources(id),
    user_id VARCHAR(100) NOT NULL,
    is_public BOOLEAN NOT NULL DEFAULT FALSE,
    tags VARCHAR[],
    meta_data JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);

-- Create app_users table (for auth)
CREATE TABLE IF NOT EXISTS app_users (
    id UUID NOT NULL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);

-- Create user_sessions table
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID NOT NULL PRIMARY KEY,
    user_id UUID NOT NULL,
    refresh_token TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_user_sessions_user_id ON user_sessions(user_id);

-- Create MDL tables
CREATE TABLE IF NOT EXISTS mdl_projects (
    id UUID NOT NULL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    datasource_id VARCHAR(36) NOT NULL REFERENCES datasources(id) ON DELETE CASCADE,
    owner_id UUID NOT NULL REFERENCES app_users(id),
    meta_data JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS mdl_models (
    id UUID NOT NULL PRIMARY KEY,
    project_id UUID NOT NULL REFERENCES mdl_projects(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    primary_key VARCHAR(100),
    sql_table VARCHAR(255),
    meta_data JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS mdl_fields (
    id UUID NOT NULL PRIMARY KEY,
    model_id UUID NOT NULL REFERENCES mdl_models(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    field_type VARCHAR(50) NOT NULL,
    expression TEXT,
    is_calculated BOOLEAN NOT NULL DEFAULT FALSE,
    meta_data JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS mdl_relationships (
    id UUID NOT NULL PRIMARY KEY,
    project_id UUID NOT NULL REFERENCES mdl_projects(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    from_model_id UUID NOT NULL REFERENCES mdl_models(id) ON DELETE CASCADE,
    to_model_id UUID NOT NULL REFERENCES mdl_models(id) ON DELETE CASCADE,
    join_type VARCHAR(20) NOT NULL,
    condition TEXT NOT NULL,
    meta_data JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);

-- Create diagnosis tables
CREATE TABLE IF NOT EXISTS error_patterns (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    error_type VARCHAR(100) NOT NULL,
    pattern_regex TEXT NOT NULL,
    description TEXT,
    solution_template TEXT,
    severity VARCHAR(20),
    frequency_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sql_corrections (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    original_sql TEXT NOT NULL,
    corrected_sql TEXT NOT NULL,
    error_message TEXT,
    correction_type VARCHAR(50),
    datasource_id VARCHAR(36) REFERENCES datasources(id),
    user_id VARCHAR(100),
    success BOOLEAN NOT NULL,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

-- Create diagnosis_results table
CREATE TABLE IF NOT EXISTS diagnosis_results (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    query_id VARCHAR(36) NOT NULL,
    summary TEXT NOT NULL,
    key_points JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_diagnosis_results_query_id ON diagnosis_results(query_id);

-- Create correction_logs table
CREATE TABLE IF NOT EXISTS correction_logs (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    query_id VARCHAR(36) NOT NULL,
    attempt_number INTEGER NOT NULL,
    original_sql TEXT NOT NULL,
    error_message TEXT NOT NULL,
    corrected_sql TEXT,
    was_successful BOOLEAN NOT NULL,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_correction_logs_query_id ON correction_logs(query_id);
