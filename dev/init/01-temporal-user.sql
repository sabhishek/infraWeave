-- Initializes Temporal DB user and databases for local development
CREATE USER temporal WITH PASSWORD 'temporal';
CREATE DATABASE temporal OWNER temporal;
CREATE DATABASE temporal_visibility OWNER temporal;
