-- PostgreSQL initialization script for OpenFlow

-- Create extensions if they don't exist
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "unaccent";

-- Set default timezone
SET timezone = 'UTC';

-- Create default schema if needed
-- CREATE SCHEMA IF NOT EXISTS openflow;

-- You can add initial database setup here
-- For example, creating custom types, functions, etc.

-- Grant permissions (adjust as needed for production)
GRANT ALL PRIVILEGES ON DATABASE openflow TO openflow;
