# Vectorsearch Docker Image

## About

I initially targeted paradedb/paradedb:0.12.0-pg17 for our task, but found out that we only need its pg_search, pgvector extensions. While all the others are not necessary for our use case.

Also, in an old paradedb release, they imported pgvectorscale from timescale for its advanced algorithms, but in the latest release, they removed it. I decided to give it a shot, thus we are here.

## Build

I used postgres 17 with pgvector 0.8.0 as the base image (pgvector/pgvector:0.8.0-pg17). <br>
Then added pg_search:0.12.0 and pgvectorscale:0.4.0 as dependencies. <br>
In [ `bootstrap.sh` ](./bootstrap.sh), there are sql to create the extensions for every potential database.

## Usage

1. I have published a docker image for vectorsearch at [dockerhub](https://hub.docker.com/r/oaklight/vectorsearch)

2. To build from the Dockerfile: `make build`

To run the container:

```bash
docker run --name vectorsearch -p <5432>:5432 -v <$pwd/pgdata>:/var/lib/postgresql/data/ -e POSTGRES_USER=myuser -e POSTGRES_PASSWORD=mypassword -e POSTGRES_DB=mydatabase oaklight/vectorsearch
```

or use `docker compose` :

```bash
docker compose up -d
```

## Note

The image is based on the official postgres image, so you can use the same commands to interact with the database.

For example, you could use `psql` to connect to the database:

```bash
psql -h <your_container_name> -U <username> -d <database>
```

You can also use `pgAdmin` to connect to the database.
