# Use the official pgvector image as the base image
FROM pgvector/pgvector:0.8.0-pg17

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive

# Switch to root for configuring runtime dependencies
USER root

######################
# pg_search
######################

# Copy pg_search .deb package from the host system
COPY pg_search.deb /tmp/pg_search.deb
RUN dpkg -i /tmp/pg_search.deb || apt-get install -fy && \
    rm /tmp/pg_search.deb

######################
# pgvectorscale
######################

# Copy pgvectorscale .deb package from the host system
COPY pgvectorscale.deb /tmp/pgvectorscale.deb
RUN dpkg -i /tmp/pgvectorscale.deb || apt-get install -fy && \
    rm /tmp/pgvectorscale.deb

# Clean up the .deb package and APT cache
RUN apt-get autoremove --purge && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy pg_hba.conf files to the container
COPY pg_hba.conf /var/lib/postgresql/data/pg_hba.conf

# The postgresql.conf.sample file is used as a template for the postgresql.conf file, which
# does not exist until the first time the container is started. By adding our settings to the
# postgresql.conf.sample file, we ensure that our settings are applied onto the postgresql.conf file.
#
# The `postgres` database is the default database that exists in every Postgres installation. The pg_cron
# extension requires a database to store its metadata tables. By using `postgres`, we ensure that it has a
# stable, always-available database for its operations, no matter what other databases are created or deleted.
RUN sed -i "s/^#shared_preload_libraries = ''/shared_preload_libraries = 'pg_search'/" /usr/share/postgresql/postgresql.conf.sample && \
    echo "cron.database_name = 'postgres'" >>/usr/share/postgresql/postgresql.conf.sample

# No need for an ENTRYPOINT or CMD if the base image handles PostgreSQL startup
COPY ./bootstrap.sh /docker-entrypoint-initdb.d/10_bootstrap_paradedb.sh