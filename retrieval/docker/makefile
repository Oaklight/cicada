# Makefile
BUILD_VERSION ?= 0.2

# Define the version variables
PG_SEARCH_VERSION ?= 0.13.1
PG_VECTORSCALE_VERSION ?= 0.5.1
PGVECTOR_BASE_VERSION ?= 0.8.0

# Define the PostgreSQL major version, default to 17
PG_MAJOR_VERSION ?= 17

# Define the base image URL with PG_MAJOR_VERSION
PG_VECTOR_BASE_VERSION := $(PGVECTOR_BASE_VERSION)-pg$(PG_MAJOR_VERSION)

# --------------------------- Docker Build Tags ---------------------------
# Define the build tag, default to 0.1-pg{PG_MAJOR_VERSION}
BUILD_TAG := $(BUILD_VERSION)-pg$(PG_MAJOR_VERSION)
LATEST_TAG := latest-pg$(PG_MAJOR_VERSION)

# ---------------------------- Dependency URLs ----------------------------
# Define the URLs for the deb files with version variables and PG_MAJOR_VERSION
PG_SEARCH_URL := "https://github.com/paradedb/paradedb/releases/download/v$(PG_SEARCH_VERSION)/postgresql-$(PG_MAJOR_VERSION)-pg-search_$(PG_SEARCH_VERSION)-1PARADEDB-bookworm_amd64.deb"
PGVECTORSCALE_ZIP_URL := "https://github.com/timescale/pgvectorscale/releases/download/$(PG_VECTORSCALE_VERSION)/pgvectorscale-$(PG_VECTORSCALE_VERSION)-pg$(PG_MAJOR_VERSION)-amd64.zip"

# ------------------------------ Local Paths ------------------------------
# Define the local paths for the deb files
PG_SEARCH_DEB := pg_search.deb
PGVECTORSCALE_DEB := pgvectorscale.deb

# Download the deb files
.PHONY: download
download: $(PG_SEARCH_DEB) $(PGVECTORSCALE_DEB)

$(PG_SEARCH_DEB):
	@echo "Downloading pg_search.deb for PostgreSQL $(PG_MAJOR_VERSION) from $(PG_SEARCH_URL)"
	curl -L $(PG_SEARCH_URL) -o $(PG_SEARCH_DEB)

$(PGVECTORSCALE_DEB):
	@echo "Downloading pgvectorscale.zip for PostgreSQL $(PG_MAJOR_VERSION) from $(PGVECTORSCALE_ZIP_URL)"
	curl -L $(PGVECTORSCALE_ZIP_URL) -o pgvectorscale.zip
	unzip -j pgvectorscale.zip "pgvectorscale-postgresql-$(PG_MAJOR_VERSION)_$(PG_VECTORSCALE_VERSION)-Linux_amd64.deb" -d .
	mv pgvectorscale-postgresql-$(PG_MAJOR_VERSION)_$(PG_VECTORSCALE_VERSION)-Linux_amd64.deb $(PGVECTORSCALE_DEB)
	rm -f pgvectorscale.zip

# Build the Docker image
.PHONY: build
build: download
	@echo "Building Docker image with PG_VECTOR_BASE_IMAGE=$(PG_VECTOR_BASE_VERSION) and tags $(BUILD_TAG), $(LATEST_TAG)"
	docker build --build-arg PG_VECTOR_BASE_VERSION=$(PG_VECTOR_BASE_VERSION) -t oaklight/vectorsearch:$(BUILD_TAG) .
	docker tag oaklight/vectorsearch:$(BUILD_TAG) oaklight/vectorsearch:$(LATEST_TAG)

# Clean up the deb files
.PHONY: clean
clean:
	@echo "Cleaning up deb files"
	rm -f $(PG_SEARCH_DEB) $(PGVECTORSCALE_DEB)

# Prune Docker images
.PHONY: prune
prune: clean
	@echo "Pruning Docker images"
	docker rmi $(shell docker images -q oaklight/vectorsearch:$(BUILD_TAG))
	docker rmi $(shell docker images -q oaklight/vectorsearch:$(LATEST_TAG))