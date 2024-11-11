#!/bin/bash
# shellcheck disable=SC2154

# Executed at container start to bootstrap ParadeDB extensions and Postgres settings.

# Exit on subcommand errors
set -Eeuo pipefail

# Perform all actions as $POSTGRES_USER
export PGUSER="$POSTGRES_USER"

# Load ParadeDB and third-party extensions into both template1 and $POSTGRES_DB
# Creating extensions in template1 ensures that they are available in all new databases.
for DB in template1 "$POSTGRES_DB"; do
    echo "Loading ParadeDB extensions into $DB"
    psql -d "$DB" <<-'EOSQL'
    CREATE EXTENSION IF NOT EXISTS pg_search;
    CREATE EXTENSION IF NOT EXISTS vectorscale CASCADE;
    CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
EOSQL
done
# The CASCADE automatically installs pgvector.

# Add the `paradedb` schema to both template1 and $POSTGRES_DB
for DB in template1 "$POSTGRES_DB"; do
    echo "Adding 'paradedb' search_path to $DB"
    psql -d "$DB" -c "ALTER DATABASE \"$DB\" SET search_path TO public,paradedb;"
done

echo "ParadeDB bootstrap completed!"
