#!/bin/sh
# Odotetaan että tietokantaan saa yhteyden
until pg_isready -h db -p 5432 -U postgres; do
  echo "Waiting for postgres..."
  sleep 1
done

# Aja Alembic-migraatiot ennen backendin käynnistystä
alembic upgrade head
exec uvicorn main:app --host 0.0.0.0 --port 8000
