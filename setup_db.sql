-- Create datasources table (no dependencies)
CREATE TABLE IF NOT EXISTS datasources (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(500),
    type VARCHAR(50) NOT NULL,
    connection_info JSONB NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP
);

-- Create indexes for datasources
CREATE INDEX IF NOT EXISTS idx_datasources_name ON datasources(name);
CREATE INDEX IF NOT EXISTS idx_datasources_type ON datasources(type);

-- Create cubes table (depends on datasources)
CREATE TABLE IF NOT EXISTS cubes (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    datasource_id VARCHAR(36) REFERENCES datasources(id),
    metadata JSONB NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create query_history table (depends on datasources)
CREATE TABLE IF NOT EXISTS query_history (
    id VARCHAR(36) PRIMARY KEY,
    datasource_id VARCHAR(36) NOT NULL REFERENCES datasources(id),
    user_id VARCHAR(100),
    sql TEXT NOT NULL,
    execution_time_ms INTEGER NOT NULL,
    row_count INTEGER NOT NULL,
    error VARCHAR,
    status VARCHAR(20) NOT NULL DEFAULT 'success',
    executed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create chat_sessions table (depends on datasources and cubes)
CREATE TABLE IF NOT EXISTS chat_sessions (
    id VARCHAR(36) PRIMARY KEY,
    title VARCHAR(255),
    user_id VARCHAR(100) NOT NULL,
    cube_id VARCHAR(36) REFERENCES cubes(id),
    datasource_id VARCHAR(36) REFERENCES datasources(id),
    context JSONB,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    last_active TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create chat_messages table (depends on chat_sessions)
CREATE TABLE IF NOT EXISTS chat_messages (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL REFERENCES chat_sessions(id),
    role VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    table_metadata JSONB,
    query_sql TEXT,
    execution_time INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create visualizations table (depends on chat_messages)
CREATE TABLE IF NOT EXISTS visualizations (
    id VARCHAR(36) PRIMARY KEY,
    message_id VARCHAR(36) NOT NULL REFERENCES chat_messages(id),
    chart_type VARCHAR(50) NOT NULL,
    chart_config JSONB NOT NULL,
    data JSONB,
    title VARCHAR(255),
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for query_history
CREATE INDEX IF NOT EXISTS idx_query_history_datasource_id ON query_history(datasource_id);
CREATE INDEX IF NOT EXISTS idx_query_history_executed_at ON query_history(executed_at);
