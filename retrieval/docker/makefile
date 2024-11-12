# Makefile

# Define the URLs for the deb files
PG_SEARCH_URL := "https://github.com/paradedb/paradedb/releases/download/v0.12.0/postgresql-17-pg-search_0.12.0-1PARADEDB-bookworm_amd64.deb"
PGVECTORSCALE_ZIP_URL := "https://github.com/timescale/pgvectorscale/releases/download/0.4.0/pgvectorscale-0.4.0-pg17-amd64.zip"

# Define the local paths for the deb files
PG_SEARCH_DEB := pg_search.deb
PGVECTORSCALE_DEB := pgvectorscale.deb

# Download the deb files
.PHONY: download
download: $(PG_SEARCH_DEB) $(PGVECTORSCALE_DEB)

$(PG_SEARCH_DEB):
	curl -L $(PG_SEARCH_URL) -o $(PG_SEARCH_DEB)

$(PGVECTORSCALE_DEB):
	curl -L $(PGVECTORSCALE_ZIP_URL) -o pgvectorscale.zip
	unzip -j pgvectorscale.zip "pgvectorscale-postgresql-17_0.4.0-Linux_amd64.deb" -d .
	mv pgvectorscale-postgresql-17_0.4.0-Linux_amd64.deb $(PGVECTORSCALE_DEB)
	rm -f pgvectorscale.zip

# Build the Docker image
.PHONY: build
build: download
	docker build -t oaklight/vectorsearch .

# Clean up the deb files
.PHONY: clean
clean:
	rm -f $(PG_SEARCH_DEB) $(PGVECTORSCALE_DEB)