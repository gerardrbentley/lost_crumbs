---
title: Postgres
description: Programming language popular for readability and ecosystem.
links:
  - Optional Prerequisites:
    - setup_postgres
---

# Postgres


## psql

`psql` is the query interface CLI to postgres.

Commands such as:

```psql
# Show all tables
\dt
# Describe a table called note
\d note
# Show all functions
\df
# Show the data in a table called note
SELECT * FROM note;
# Quit psql
\q
```
