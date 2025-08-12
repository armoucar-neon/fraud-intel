#!/bin/bash
set -e

# Wait for Postgres to be ready
until pg_isready -U "$POSTGRES_USER"; do
  echo "Waiting for postgres..."
  sleep 2
done

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    SELECT 'CREATE DATABASE "phoenix"'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'phoenix')\gexec
EOSQL