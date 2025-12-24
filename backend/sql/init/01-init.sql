-- Initial database setup for Ghost Squad system
-- This script runs when the PostgreSQL container starts for the first time

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create database user if not exists (handled by environment variables)
-- The main database and user are created by the Docker environment variables

-- Set timezone
SET timezone = 'Asia/Tokyo';

-- Create basic schema structure (will be managed by Alembic migrations later)
-- This is just to ensure the database is ready for the application