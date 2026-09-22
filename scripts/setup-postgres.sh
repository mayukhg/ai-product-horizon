#!/usr/bin/env bash
set -euo pipefail

sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname = 'horizonai'" | grep -q 1 \
  || sudo -u postgres psql -c "CREATE USER horizonai WITH PASSWORD 'horizonai_dev';"

sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname = 'horizonai'" | grep -q 1 \
  || sudo -u postgres psql -c "CREATE DATABASE horizonai OWNER horizonai;"

sudo -u postgres psql -d horizonai -c "CREATE EXTENSION IF NOT EXISTS vector;"
sudo -u postgres psql -d horizonai -c "GRANT ALL ON SCHEMA public TO horizonai;"

echo "PostgreSQL ready: postgresql://horizonai:horizonai_dev@localhost:5432/horizonai"
