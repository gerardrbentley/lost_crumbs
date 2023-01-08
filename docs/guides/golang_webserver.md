---
title: Project Golang Webserver
description: Writing a backend webservice with golang.
links:
  - Prerequisites:
    - setup_golang
---

# Project Golang Webserver

```sh
# Open terminal to desired project directory
cd ~/projects
# Make directory for the project
mkdir days-until-api
# Enter the directory
cd days-until-api
# Initialize go project
go mod init github.com/gerardrbentley/days-until-api
# Make file for entrypoint and basic integration testing
touch main.go main_test.go
# Make package for API handlers
mkdir handler
# Make file for web app code
touch handler/daysuntil.go handler/daysuntil_test.go
# Run tests
go test ./...
# Run Server
go run main.go
# Manually request endpoint (from another terminal)
curl "localhost:5000/daysuntil?date=2024-01-03"
# Build and run executable
go build main.go
./main
```

## Main Entrypoint

```go title="main.go"
package main

import (
	"log"
	"net/http"

	. "github.com/gerardrbentley/days-until-api/handler"
)

func setupHandlers() *http.ServeMux {
	h := http.NewServeMux()
	h.Handle("/daysuntil", DaysUntilHandler())

	return h
}

func main() {
	log.Println("Starting Up....")
	h := setupHandlers()
	log.Fatal(http.ListenAndServe(":5000", h))
}
```

## Handler

```go title="handler/daysuntil.go"
package handler

import (
	"encoding/json"
	"log"
	"net/http"
	"time"
)

type DaysUntilError struct {
	Error string `json:"error"`
}

type DaysUntilResponse struct {
	Days int `json:"days"`
}

func DaysUntilHandler() http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")

		rawDate := r.URL.Query().Get("date")
		layout := "2006-01-02"
		requestedDate, err := time.Parse(layout, rawDate)

		if err != nil {
			log.Println(err.Error())
			w.WriteHeader(http.StatusBadRequest)
			p := DaysUntilError{Error: "not a valid date in format YYYY-MM-DD"}
			if err := json.NewEncoder(w).Encode(p); err != nil {
				log.Println(err.Error())
				w.WriteHeader(http.StatusInternalServerError)
			}
			return
		}

		now := time.Now()
		today := time.Date(now.Year(), now.Month(), now.Day(), 0, 0, 0, 0, time.UTC)
		difference := requestedDate.Sub(today)
		numDays := int(difference.Hours() / 24)

		p := DaysUntilResponse{Days: numDays}
		if err := json.NewEncoder(w).Encode(p); err != nil {
			log.Println(err.Error())
			w.WriteHeader(http.StatusInternalServerError)
		}
	})
}
```

## Happy Path Integration Test

```go title="main_test.go"
package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	. "github.com/gerardrbentley/days-until-api/handler"
)

func TestDaysUntilRoute(t *testing.T) {
	h := setupHandlers()

	w := httptest.NewRecorder()
	twoDaysFuture := time.Now().Add(time.Hour * 24 * 2).Format("2006-01-02")
	req, _ := http.NewRequest("GET", fmt.Sprintf("/daysuntil?date=%s", twoDaysFuture), nil)
	h.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("Not OK %v", w.Code)
	}
	result := DaysUntilResponse{}
	if err := json.NewDecoder(w.Body).Decode(&result); err != nil {
		log.Fatalln(err)
	}
	if result.Days != 2 {
		t.Errorf("Not 2 days: %v", result.Days)
	}
}
```

## Happy Path Handler Test

```go title="handler/daysuntil_test.go"
package handler

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestDaysUntilHandler(t *testing.T) {
	ctx := context.Background()
	twoDaysFuture := time.Now().Add(time.Hour * 24 * 2).Format("2006-01-02")

	req, _ := http.NewRequestWithContext(
		ctx,
		http.MethodPatch,
		fmt.Sprintf("/daysuntil?date=%s", twoDaysFuture),
		nil,
	)
	w := httptest.NewRecorder()

	r := http.NewServeMux()
	r.Handle("/daysuntil", DaysUntilHandler())
	r.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("Not OK %v", w.Code)
	}
	result := DaysUntilResponse{}
	if err := json.NewDecoder(w.Body).Decode(&result); err != nil {
		log.Fatalln(err)
	}
	if result.Days != 2 {
		t.Errorf("Not 2 days: %v", result.Days)
	}
}
```

## Gin Framework

Alternative to using standard library http servemux

```sh
go get -u github.com/gin-gonic/gin
```

```go title="main.go"
package main

import "github.com/gin-gonic/gin"

func ginHandler(c *gin.Context) {
    rawDate := c.Query("date")

		c.JSON(http.StatusOK, gin.H{"same_date": rawDate})
}

func setupRouter() *gin.Engine {
	r := gin.Default()
	r.GET("/daysuntil", ginHandler)
	return r
}

func main() {
	r := setupRouter()
	r.Run(":5000")
}
```
