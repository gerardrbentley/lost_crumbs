---
title: Postgres
description: Database flavour popular for performance and extensions.
links:
  - Prerequisites:
    - setup_terminal
    - setup_ide
    - setup_docker
---

# Postgres


Install Binary from source: [https://www.postgresql.org/download/]()

Or on Mac use `brew install postgres`

Or just use Docker:

```sh
docker run --name some-postgres -e POSTGRES_PASSWORD=mysecretpassword -d postgres
```

Or use Docker within a docker-compose stack:

```yaml
services:
  db:
    image: postgres
    restart: always
    environment:
      POSTGRES_PASSWORD: example
```