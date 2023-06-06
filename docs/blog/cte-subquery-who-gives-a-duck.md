---
title: "CTE vs Subquery: Who gives a 🦆uck?"
description: Exploring query structure in postgres and duckdb
categories: 
    - data
tags:
    - sql
    - data
    - beginner
date: 2023-06-04
---

# CTE vs Subquery: Who gives a 🦆uck?

## Inspiration

- [https://duckdb.org/2023/05/26/correlated-subqueries-in-sql.html](https://duckdb.org/2023/05/26/correlated-subqueries-in-sql.html)
- [https://cs.emis.de/LNI/Proceedings/Proceedings241/383.pdf](https://cs.emis.de/LNI/Proceedings/Proceedings241/383.pdf)
- Blog Posts about CTEs vs Subqueries

## TL;DR

Rough performance numbers on M1 Macbook Pro 16GB.
100,000 students joined with 1,000,000 exam scores.

Follow along from the [github repo](https://github.com/gerardrbentley/duckdb-postgres/tree/main) if you're comfortable with docker.

| Engine      | Query Structure | Performance (seconds) |
| ----------- | ----------- | ----------- |
| DuckDB      | Subquery       | 0.02 |
| DuckDB   | CTE        | 0.02 |
| DuckDB + cached Postgres      | Subquery       | 0.03 |
| DuckDB + cached Postgres   | CTE        | 0.07 |
| Postgres   | CTE        | 0.49 |
| DuckDB + scanned Postgres      | Subquery       | 0.50 |
| DuckDB + scanned Postgres   | CTE        | 0.50 |
| Postgres      | Subquery       | ~6300 |

## Why it matters

This is an example of a query with a subquery:

```sql
select students.name, 
    exams.course
from students,
    exams
where students.id = exams.sid
    and exams.grade = (
        select min(e2.grade)
        from exams e2
        where students.id = e2.sid
    );
```

It selects, for each student, the exam with the lowest grade they received out of all their own exams.

If you have experience with SQL joins then you might recognize the `students.id = exams.sid` clause, which joins exams to students.

The subquery utilizes each student's id to find their own minimum grade of their exams.

The performance of this query in postgres is *atrocious*.

On the other hand, the performance of this completely equivalent query using a Common Table Expression (CTE) is *very passable* in postgres:

```sql
with 
    min_exam_grades as (
        select e2.sid as id,
            min(e2.grade) as best
        from exams e2
        group by e2.sid
    )
select students.name,
    exams.course
from students,
    exams,
    min_exam_grades
where students.id = exams.sid
    and min_exam_grades.id = students.id
    and exams.grade = min_exam_grades.best;
```

This is the CTE vs Subquery debate in a nutshell.

You have to keep in mind that subqueries can produce poor query performance and you cannot write all subquery expressions as CTEs!

In comes the OLAP-centric duckdb and de-correlated queries so we can have our cake and eat it too.

## Not giving a flock

We'll run these queries over a duckdb database and compare their performance.
(HINT: they're the same in duckdb)

You can follow along with this experience in your browser; visit [https://shell.duckdb.org](https://shell.duckdb.org) to open a duckdb shell.

Then we'll show that you can bring these benefits over to a live postgres instance with the duckdb postgres scanner extension!

### Tables

We'll generate some similar tables to the examples in the paper.
Namely, a students and an exams table.

Copy and paste the following into a duckdb shell.

Follow along with the sql comments (`-- these lines with two dashes are comments`)

```sql
-- cleanup existing tables and sequences if necessary
drop table if exists exams;
drop table if exists students;
drop sequence if exists seq_studentid;
drop sequence if exists seq_examid;

-- generate tables for students and exams
create table students (
    id bigint, 
    name text
);
create table exams (
    id bigint,
    sid bigint,
    grade int,
    course text
);

-- create sequences to create ids for exams and students
create sequence seq_studentid start 1;
create sequence seq_examid start 1;

-- generate 100000 students with random text names
insert into students (id, name)
select nextval('seq_studentid'), md5(random()::text)
from generate_series(1, 100000);

-- generate 10 exams per student with random grades between 0 and 100 and random text course names
insert into exams (id, sid, grade, course)
select nextval('seq_examid'),
    students.id,
    floor(random() * (101))::int,
    md5(random()::text)
from generate_series(1, 10),
    students;
```

You should see something like the following in your shell:

    | Count |
    ---------
    | 1000000 |

### Subquery

The subquery is the first version of the query I personally would write.

Let's evaluate its performance:

```sql
explain analyze
select s.name,
    e.course
from students s,
    exams e
where s.id = e.sid
    and e.grade =(
        select min(e2.grade)
        from exams e2
        where s.id = e2.sid
    );
```

This takes about `0.02` seconds on my machine on the first run (about `0.09` in the duckdb browser shell).

### CTE

Now for the CTE:

```sql
explain analyze
select students.name,
    exams.course
from students,
    exams,
    (
        select e2.sid as id,
            min(e2.grade) as best
        from exams e2
        group by e2.sid
    ) min_exam_grades
where students.id = exams.sid
    and min_exam_grades.id = students.id
    and exams.grade = min_exam_grades.best;
```

This also takes about `0.02` seconds on my machine (about `0.09` in the duckdb browser shell).

## So What

Let's run the same experiment in postgres via a docker compose file:

```yaml
services:
  database:
    image: postgres:15.1
    command: ["postgres", "-c", "log_statement=all", "-c", "log_destination=stderr"]
    volumes:
      - ./pg:/tmp/pg
      - postgres_data:/var/lib/postgresql/data/pgdata
    environment:
      PGDATA: /var/lib/postgresql/data/pgdata/
      POSTGRES_HOST: database
      POSTGRES_PORT: 5432
      POSTGRES_DB: demo
      POSTGRES_USER: demo_user
      POSTGRES_PASSWORD: demo_password
    ports:
      - "5432:5432"
    restart: always

volumes:
  postgres_data:
```

With `docker-compose up --build` and this `docker-compose.yml` we should get a live postgres container.

### Init Postgres Tables

The following should get us a `psql` shell in the postgres instance:

```sh
docker-compose exec database psql --username demo_user --dbname demo
```

(*NOTE* you will probably need to open another terminal)

And then we can create the same demo tables:

```sql
-- cleanup if necessary
drop table if exists exams;
drop table if exists students;

-- generate tables
create table students (
    id bigserial, 
    name text
);
create table exams (
    id bigserial,
    sid bigint,
    grade int,
    course text
);

-- generate 100000 students
insert into students (name)
select md5(random()::text)
from generate_series(1, 100000);

-- generate 10 exams per student
insert into exams (sid, grade, course)
select students.id,
    floor(random() * (101))::int,
    md5(random()::text)
from generate_series(1, 10),
    students;
```

### PG CTE

For Postgres we'll start with the CTE version of the query:

```sql
explain analyze
select students.name,
    exams.course
from students,
    exams,
    (
        select e2.sid as id,
            min(e2.grade) as best
        from exams e2
        group by e2.sid
    ) min_exam_grades
where students.id = exams.sid
    and min_exam_grades.id = students.id
    and exams.grade = min_exam_grades.best;
```

Execution time `493 ms` or `0.493` seconds.

Ok, not atrocious, but slower than duckdb running in WASM in the browser.

So if our subquery query can be re-written as a CTE query then we're mostly safe.

### PG Subquery

If you're brave, go ahead and try the following.

In the same `psql` shell let's evaluate the subquery:

```sql
explain analyze
select s.name,
    e.course
from students s,
    exams e
where s.id = e.sid
    and e.grade =(
        select min(e2.grade)
        from exams e2
        where s.id = e2.sid
);
```

**WARNING** this took about an hour and 45 minutes on my machine

## Blending It Together

But we can do even better!

By combining the power of duckdb and postgres we can run these queries efficiently against a live postgres instance without thinking about the structure of our query!

### Duckdb Postgres Scan

We can scan live data with the benefits of the de-correlated algorithm with the original queries.

We'll run duckdb from the CLI with `duckdb` and connect to the dockerized postgres instance.

```sh
duckdb
```

And in the duckdb shell we can attach to the postgres instance:

```sql
INSTALL postgres_scanner;
LOAD postgres_scanner;
CALL postgres_attach('dbname=demo user=demo_user password=demo_password host=localhost');
PRAGMA show_tables;
```

#### Live Scan

Using `.read` will execute the sql query in a given file.
This might be more convenient for you than copy and pasting the whole query.

```sql
-- explain analyze subquery version
.read pg/subquery.sql

-- explain analyze cte version
.read pg/cte.sql
```

About `0.5` seconds for each of these queries.

(*NOTE* you could take this a step further by isolating the postgres instance on another server. In this experiment they are literally running on the same machine sharing resources)

Both had **equivalent** performance to the regular Postgres CTE version.
Both had **orders of magnitude** better performance than the Postgres Subquery version.

So write whatever query makes sense to you and your team / organization!

#### Cached Scan

If data duplication is not an issue, then we can load the postgres table data into duckdb itself and get even better performance!

```sql
-- copy data into duckdb tables. Only has to happen once
.read pg/init_db_scan_cache.sql

-- explain analyze cached subquery version
.read pg/subquery_cached.sql

-- explain analyze cached cte version
.read pg/cte_cached.sql
```

Around `0.07` seconds.
An order of magnitude better than the "efficient" CTE version on Postgres.

Interestingly, the cached subquery duckdb version has the best performance around `0.03` seconds.

(*NOTE* these queries only differ in the tables they reference: the cached tables. Start duckdb with a command like `duckdb students.db` to save the database file and not have to copy tables again)

### Duckdb Docker

This mimics a real production scenario where your duckdb instance is querying a live postgres instance either on RDS or some other host.

Perhaps duckdb is running in a lambda or other type of workflow job.

The Dockerfile chooses a basic OS and downloads necessary packages:

```Dockerfile
FROM debian:bullseye-slim

RUN apt-get update && apt-get install -y \
    wget unzip gettext-base \
    && rm -rf /var/lib/apt/lists/*

RUN wget https://github.com/duckdb/duckdb/releases/download/v0.8.0/duckdb_cli-linux-amd64.zip \
    && unzip duckdb_cli-linux-amd64.zip -d /usr/local/bin \
    && rm duckdb_cli-linux-amd64.zip

# Run as non-root user
RUN useradd --create-home appuser
WORKDIR /home/appuser
USER appuser

# Duckdb startup helpers
COPY .duckdbrc /tmp/.duckdbrc
COPY entrypoint.sh ./entrypoint.sh

ENTRYPOINT [ "/bin/bash" ]
CMD [ "entrypoint.sh", "duckdb" ]
```

#### .duckdbrc

The `.duckdbrc` file defines the initialization of duckdb shells for this image.
It will instruct each duckdb shell you open to connect to the live postgres docker container:

```sh
.prompt '⚫◗ '
INSTALL postgres_scanner;
LOAD postgres_scanner;
CALL postgres_attach('dbname=$POSTGRES_DB user=$POSTGRES_USER password=$POSTGRES_PASSWORD host=$POSTGRES_HOST');
PRAGMA show_tables;
```

#### Entrypoint

But to set those postgres connection variables at runtime we'll need a small entrypoint bash script that will allow other commands to be entered after:

```sh
#!/bin/sh
envsubst < /tmp/.duckdbrc > /home/appuser/.duckdbrc
exec "$@"
```

#### Docker Compose

Let's add this other container / service to our docker-compose file:

```yaml
  duck-database:
    build: duck
    volumes:
      - ./pg:/home/appuser/pg
      - ./duck:/home/appuser/duck
    environment:
      POSTGRES_HOST: database
      POSTGRES_PORT: 5432
      POSTGRES_DB: demo
      POSTGRES_USER: demo_user
      POSTGRES_PASSWORD: demo_password
    # Probably only necessary for M1 Mac
    platform: linux/x86_64
```

The following should get us a duckdb shell that can connect to the live postgres instance:

```sh
docker-compose run --build duck-database entrypoint.sh duckdb duck/students.db
```

Or we can run a query directly from the cli:

```sh
docker-compose run --build duck-database entrypoint.sh duckdb -c ".read pg/subquery.sql"
```

This method might cause a performance hit on your machine, but can be tested more rigorously before a cloud pipeline deployment.

## Story Time

If you've made it this far then you probably have some interest in the topic.

Here's an example of how I learned about subquery performance in Postgres in the real world:

- Imagine a table full of account records for your customers
- Imagine this table has a column for the date the data was updated
- Imagine you want to select the most up to date information for a large set of accounts

Maybe you would write a query like this:

```sql
select accounts.id, accounts.balance
from accounts
where 
    accounts.balance > 1
    and accounts.updated_date = (
        select max(a2.updated_date)
        from accounts a2
        where accounts.id = a2.id
    );
```

And thus you fell into the trap.
This query could take god-knows-how-long and that is not at all useful for developer experience.

Would you rather spend the mental cycles re-writing it to a CTE or move on with your life?

## Resources

Keep exploring!

- More on this example from [@FrankPachot](https://twitter.com/FranckPachot/status/1665960170222919680?s=20): [dbfiddle.uk/wLZ4H496](dbfiddle.uk/wLZ4H496)
- [https://duckdb.org/2023/05/26/correlated-subqueries-in-sql.html](https://duckdb.org/2023/05/26/correlated-subqueries-in-sql.html)
- [https://duckdb.org/2022/09/30/postgres-scanner.html](https://duckdb.org/2022/09/30/postgres-scanner.html)
- [https://hakibenita.com/be-careful-with-cte-in-postgre-sql](https://hakibenita.com/be-careful-with-cte-in-postgre-sql)
- [https://cs.emis.de/LNI/Proceedings/Proceedings241/383.pdf](https://cs.emis.de/LNI/Proceedings/Proceedings241/383.pdf)
