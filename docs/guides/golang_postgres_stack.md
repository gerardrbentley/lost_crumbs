---
title: Project Golang Postgres Stack
description: Writing a backend webservice with golang and postgres.
links:
  - Prerequisites:
    - project_golang_webserver
    - setup_postgres
    - setup_docker
---

# Project Golang Postgres Stack

This app looks up locations from a static table.

For simplicity, it's all treated as text.

```sh
# Open terminal to desired project directory
cd ~/projects
# Make directory for the project
mkdir places
# Enter the directory
cd places

# Make directory for the go backend server
mkdir backend
# Enter the go
cd backend
# Initialize go project
go mod init github.com/gerardrbentley/places
# Install postgres driver and mock interface
go get -u github.com/jackc/pgx/v5/pgxpool
go get -u github.com/spacetab-io/pgxpoolmock
# Make file for entrypoint and basic integration testing
touch main.go main_test.go
# Make package for API handlers
mkdir handler
# Make file for web handler code
touch handler/place.go handler/place_test.go
# Make package for data services
mkdir service
# Make files for service code
touch service/place.go service/place_test.go
# Run tests
go test ./...

# Run stack
docker-compose up --build
# Tear down stack and database
docker-compose down --volumes --remove-orphans
# Enter psql (with running stack)
docker-compose exec database psql -U places_user -d places
# Run database management script
docker-compose exec database psql -U places_user -d places -f /tmp/sample_data/load_places_data.sql


# With database in background
docker-compose up -d database
# Run Just Go server
DB_CONNECTION=postgres://places_user:places_password@localhost:5432/places go run main.go
# Manually request endpoint (from another terminal)
curl -v "http://localhost:5000/place?name=First"
# Build and run executable
go build main.go
DB_CONNECTION=postgres://places_user:places_password@localhost:5432/places ./main
```

## Main Entrypoint

Adds setup for services and database connection over basic web service.

```go title="main.go"
package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"

	. "github.com/gerardrbentley/places/handler"
	. "github.com/gerardrbentley/places/service"
	"github.com/jackc/pgx/v5/pgxpool"
)

func setupHandlers(placeService PlaceService) *http.ServeMux {
	h := http.NewServeMux()
	h.Handle("/place", PlaceHandler(placeService))

	return h
}

func main() {
	log.Println("Starting Up....")

	log.Println("Connecting to postgres...")
	dbpool, err := pgxpool.New(context.Background(), os.Getenv("DB_CONNECTION"))
	if err != nil {
		fmt.Fprintf(os.Stderr, "Unable to create connection pool: %v\n", err)
		os.Exit(1)
	}
	defer dbpool.Close()
	placeService := NewPgPlaceService(dbpool)

	h := setupHandlers(placeService)
	log.Fatal(http.ListenAndServe(":5000", h))
}
```

## Handler

Handler can accept a service on initialization for use in serving requests.

This layer can be responsible for serialization, but we'll re-use the struct from the service.

```go title="handler/place.go"
package handler

import (
	"encoding/json"
	"log"
	"net/http"

	. "github.com/gerardrbentley/places/service"
)

type PlaceError struct {
	Error string `json:"error"`
}

func PlaceHandler(service PlaceService) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")

		searchName := r.URL.Query().Get("name")
		if searchName == "" {
			w.WriteHeader(http.StatusBadRequest)
			p := PlaceError{Error: "no name query"}
			if err := json.NewEncoder(w).Encode(p); err != nil {
				log.Println(err.Error())
				w.WriteHeader(http.StatusInternalServerError)
			}
			return
		}

		records, err := service.LookupByName(searchName)
		if err != nil {
			log.Println(err.Error())
			w.WriteHeader(http.StatusNotFound)
			return
		}

		if err := json.NewEncoder(w).Encode(records); err != nil {
			log.Println(err.Error())
			w.WriteHeader(http.StatusInternalServerError)
		}
	})
}
```

## Service

By accepting an interface for our database Query tool we can freely mock out the database returns.

The database access could be abstracted to a "repository" layer or a "db" package.

```go title="service/place.go"
package service

import (
	"context"
	"errors"
	"log"

	"github.com/jackc/pgx/v5"
)

type PlaceRecord struct {
	FoodResourceType  string `db:"food_resource_type" json:"-"`
	Agency            string `db:"agency" json:"name"`
	Location          string `db:"location" json:"location"`
	OperationalStatus string `db:"operational_status" json:"-"`
	OperationalNotes  string `db:"operational_notes" json:"notes"`
	WhoTheyServe      string `db:"who_they_serve" json:"-"`
	Address           string `db:"address" json:"address"`
	Latitude          string `db:"latitude" json:"latitude"`
	Longitude         string `db:"longitude" json:"longitude"`
	PhoneNumber       string `db:"phone_number" json:"phone_number"`
	Website           string `db:"website" json:"website"`
	DaysOrHours       string `db:"days_or_hours" json:"days_or_hours"`
	DateUpdated       string `db:"date_updated" json:"-"`
}

type PlaceService interface {
	LookupByName(searchName string) ([]PlaceRecord, error)
}

type DbPool interface {
	Query(ctx context.Context, sql string, args ...any) (pgx.Rows, error)
}

type PgPlaceService struct {
	dbpool DbPool
}

func NewPgPlaceService(dbpool DbPool) *PgPlaceService {
	return &PgPlaceService{dbpool: dbpool}
}

func (s *PgPlaceService) LookupByName(searchName string) ([]PlaceRecord, error) {
	rows, err := s.dbpool.Query(context.Background(),
		`select "food_resource_type",
			"agency",
			"location",
			"operational_status",
			"operational_notes",
			"who_they_serve",
			"address",
			"latitude",
			"longitude",
			"phone_number",
			"website",
			"days_or_hours",
			"date_updated" 
		from place where tsv @@ to_tsquery($1);`,
		searchName)
	if err != nil {
		log.Printf("Query failed: %v\n", err)
		return []PlaceRecord{}, errors.New("Database Error")
	}
	records, err := pgx.CollectRows(rows, pgx.RowToStructByName[PlaceRecord])
	if err == pgx.ErrNoRows || len(records) == 0 {
		return []PlaceRecord{}, errors.New("Not Found")
	} else if err != nil {
		log.Printf("Parsing Record failed: %v\n", err)
		return []PlaceRecord{}, errors.New("Database Record Corrupted")
	}
	return records, nil
}

type InMemoryPlaceService struct {
	LookupByNameFunc func(searchName string) ([]PlaceRecord, error)
}

func (s *InMemoryPlaceService) LookupByName(searchName string) ([]PlaceRecord, error) {
	return s.LookupByNameFunc(searchName)
}

type InMemoryDbPool struct {
	QueryFunc func(ctx context.Context, sql string, args ...any) (pgx.Rows, error)
}

func (p InMemoryDbPool) Query(ctx context.Context, sql string, args ...any) (pgx.Rows, error) {
	return p.QueryFunc(ctx, sql, args)
}
```

## Happy Path Integration Test

This utilizes an in-memory service to mock the responses.

A full e2e test would ideally use the running postgres container.

```go title="main_test.go"
package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"net/http/httptest"
	"testing"

	. "github.com/gerardrbentley/places/service"
)

func TestLookupPlaceRoute(t *testing.T) {
	s := InMemoryPlaceService{
		LookupByNameFunc: func(searchName string) ([]PlaceRecord, error) {
			return []PlaceRecord{{Agency: searchName}}, nil
		},
	}
	h := setupHandlers(&s)

	w := httptest.NewRecorder()
	mockName := "seattle"
	req, _ := http.NewRequest("GET", fmt.Sprintf("/place?name=%s", mockName), nil)
	h.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("Not OK %v", w.Code)
	}
	results := []PlaceRecord{}
	if err := json.NewDecoder(w.Body).Decode(&results); err != nil {
		log.Fatalln(err)
	}
	result := results[0]
	if result.Agency != mockName {
		t.Errorf("Not same Name: %v", result.Agency)
	}
}
```

## Happy Path Handler Test

```go title="handler/place_test.go"
package handler

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"net/http/httptest"
	"testing"

	. "github.com/gerardrbentley/places/service"
)

func TestPlaceHandler(t *testing.T) {
	ctx := context.Background()
	mockName := "seattle"

	req, _ := http.NewRequestWithContext(
		ctx,
		http.MethodPatch,
		fmt.Sprintf("/place?name=%s", mockName),
		nil,
	)
	w := httptest.NewRecorder()

	s := InMemoryPlaceService{
		LookupByNameFunc: func(searchName string) ([]PlaceRecord, error) {
			return []PlaceRecord{{Agency: searchName}}, nil
		},
	}
	r := http.NewServeMux()
	r.Handle("/place", PlaceHandler(&s))
	r.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("Not OK %v", w.Code)
	}
	var results []PlaceRecord
	if err := json.NewDecoder(w.Body).Decode(&results); err != nil {
		log.Fatalln(err)
	}
	result := results[0]
	if result.Agency != mockName {
		t.Errorf("Not same name: %v", result.Agency)
	}
}
```

## Happy Path Service Test

Since the postgres rows is an interface, we can hack in a mock.

```go title="service/place_test.go"
package service

import (
	"context"
	"reflect"
	"testing"
	"unsafe"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgconn"
)

type MockRows struct {
	values   [][]any
	visitIdx int
}

func (r *MockRows) Close() {}

func (r *MockRows) Err() error {
	return nil
}

func (r *MockRows) CommandTag() pgconn.CommandTag {
	return pgconn.NewCommandTag("mock")
}

func (r *MockRows) FieldDescriptions() []pgconn.FieldDescription {
	return []pgconn.FieldDescription{}
}

func (r *MockRows) Next() bool {
	return r.visitIdx < len(r.values)
}

type mockScanner struct {
	ptrToStruct any
}

func (r *MockRows) Scan(dest ...any) error {
	v := reflect.ValueOf(dest[0]).Elem().FieldByName("ptrToStruct")
	v = reflect.NewAt(v.Type(), unsafe.Pointer(v.UnsafeAddr())).Elem()

	for i, value := range r.values[r.visitIdx] {
		n := v.Elem().Elem().Field(i)
		n.Set(reflect.ValueOf(value))
	}

	r.visitIdx = r.visitIdx + 1

	return nil
}

func (r *MockRows) Values() ([]any, error) {
	return r.values[r.visitIdx], nil
}

func (r *MockRows) RawValues() [][]byte {
	return nil
}

func (r *MockRows) Conn() *pgx.Conn {
	return nil
}

func TestLookupByName(t *testing.T) {
	mockName := "seattle"
	mockPool := InMemoryDbPool{
		QueryFunc: func(ctx context.Context, sql string, args ...any) (pgx.Rows, error) {
			pgxrows := MockRows{
				values: [][]any{
					{
						"meal",
						mockName,
					},
					{
						"food bank",
						"Fremont " + mockName,
					},
				},
			}
			return &pgxrows, nil
		},
	}
	s := PgPlaceService{dbpool: mockPool}
	records, _ := s.LookupByName(mockName)
	record := records[0]
	if record.Agency != mockName {
		t.Errorf("Not expected: %v", record.Agency)
	}
}
```

## Dockerfile

Running a database container with your webserver means you need networking.

Docker-compose is a straightforward way to handle this networking.

A go application can be built and ran in a Docker container, optionally distroless (comment last `FROM` and `COPY` steps to maintain shell access).

```docker file="backend/Dockerfile"
FROM golang:1.19.3-buster AS build

WORKDIR /src/github.com/gerardrbentley/places/

COPY go.mod .
COPY go.sum .

RUN go mod download

COPY . /src/github.com/gerardrbentley/places/
RUN CGO_ENABLED=0 GO111MODULE=on GOOS=linux go build -o /bin/app && \
    chmod 111 /bin/app

FROM gcr.io/distroless/base as final
COPY --from=build /bin/app /bin/app
CMD ["/bin/app"]
```

## Docker Compose File

This allows one command to spin up and down all or individual database and webserver.

```yaml file="docker-compose.yml"
services:
  backend:
    build: ./backend
    environment:
      - DB_CONNECTION=postgres://places_user:places_password@database:5432/places
    ports:
      - "5000:5000"
    restart: always
  database:
    image: postgres:15.1
    command: ["postgres", "-c", "log_statement=all", "-c", "log_destination=stderr"]
    environment:
      PGDATA: /var/lib/postgresql/data/pgdata/
      POSTGRES_HOST: database
      POSTGRES_PORT: 5432
      POSTGRES_DB: places
      POSTGRES_USER: places_user
      POSTGRES_PASSWORD: places_password
    ports:
      - "5432:5432"
    restart: always
    volumes:
      - ./sample_data:/tmp/sample_data
      - postgres_data:/var/lib/postgresql/data/pgdata

volumes:
  postgres_data:
```

## Database Management Script

Data source from [http://www.seattle.gov/humanservices/](http://www.seattle.gov/humanservices/): `sample_data/Emergency_Food_and_Meals_Seattle_and_King_County.csv`

To load the table into postgres and add a text search index we can use a sql script such as the following:

```sql file="sample_data/load_places_data.sql"
drop table if exists place;

create table place (
    "food_resource_type" text,
    "agency" text,
    "location" text,
    "operational_status" text,
    "operational_notes" text,
    "who_they_serve" text,
    "address" text,
    "latitude" text,
    "longitude" text,
    "phone_number" text,
    "website" text,
    "days_or_hours" text,
    "date_updated" text,
    "tsv"         tsvector
);

create trigger tsvectorupdate before insert or update
on place for each row execute procedure
tsvector_update_trigger(
	tsv, 'pg_catalog.english', "agency", "location", "operational_notes"
);

create index index_pages_on_tsv on place using gin (tsv);

\copy place("food_resource_type", "agency", "location", "operational_status", "operational_notes", "who_they_serve", "address", "latitude", "longitude", "phone_number", "website", "days_or_hours", "date_updated") from '/tmp/sample_data/Emergency_Food_and_Meals_Seattle_and_King_County.csv' with null as E'\'\'' delimiter ',' CSV HEADER
```
