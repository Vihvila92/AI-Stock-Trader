#!/bin/sh
# Wait for database connection
until pg_isready -h db -p 5432 -U postgres; do
  echo "Waiting for postgres..."
  sleep 1
done

# Run Alembic migrations before starting backend
alembic upgrade head
exec uvicorn main:app --host 0.0.0.0 --port 8000
