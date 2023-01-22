---
title: Project Golang Postgres Streamlit Stack
description: Writing a frontend to consume backend webservice with golang, streamlit and postgres.
links:
  - Prerequisites:
    - project_golang_postgres_stack
    - setup_docker
---

This app looks up Seattle Emergency Food and Meal info from a static table.

Code available on Github branch [`streamlit-reader`](https://github.com/gerardrbentley/golang-webservices/tree/streamlit-reader)

![Gif of text input and data display](/images/seattle_food_lookup.gif)


## Preface

Starts from `golang_postgres_stack` leaves off.

```sh
# Starting in project directory
cd places
# Make folder for streamlit app
mkdir frontend
# Make files for app and building
touch frontend/streamlit_app.py frontend/requirements.txt frontend/Dockerfile
# Enter frontend to setup requirements
cd frontend
# establish virtual environment
python -m venv venv
. ./venv/bin/activate
# install necessary packages
python -m pip install streamlit httpx
```

## Frontend Consumer

Goals:

- web frontend to interact with backend API
- text box for entering search terms
- data display as a table
- map out locations that have latitude and longitude information

```py file="frontend/streamlit_app.py"
import streamlit as st
import httpx
import os
import json

BACKEND_HOST = os.getenv("BACKEND_HOST", "http://127.0.0.1:5000")

st.header("Search Seattle Emergency Food Locations")

query = st.text_input("Search term")
search_url = f"{BACKEND_HOST}/place"

response = httpx.get(search_url, params={"name": query})
try:
    records = response.json()
    st.dataframe(records)
except (json.decoder.JSONDecodeError, st.errors.StreamlitAPIException):
    st.warning(f"Error from Web Request Code: {response.status_code}")
    st.stop()

map_data = []
for record in records:
    try:
        record["latitude"] = float(record["latitude"])
        record["longitude"] = float(record["longitude"])
        map_data.append(record)
    except ValueError:
        pass

st.map(map_data)
```

## Requirements

Python `requirements.txt` file works fine for specifying package versions needed.

```txt file="frontend/requirements.txt"
httpx==0.23.3
streamlit==1.17.0
```

## Dockerfile

To build the streamlit app in docker we need a dockerfile

```docker file="frontend/Dockerfile"
# pull official base image
FROM python:3.10-buster

# Don't buffer logs or write pyc
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Set Virtual env as active python environment
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install all requirements
COPY requirements.txt /tmp/
RUN pip install --upgrade pip && pip install --no-cache-dir -r /tmp/requirements.txt

# Run as non-root user
RUN useradd --create-home appuser
WORKDIR /home/appuser
USER appuser

COPY . .

ENTRYPOINT [ "python", "-m", "streamlit", "run", "streamlit_app.py"]
```

## Compose Update

Adding a new `service` entry is all that's needed to get this spun up with `docker-compose up --build`

```yaml file="docker-compose.yml"
services:
  frontend:
    ports:
      - "8501:8501"
    build: ./frontend
    environment:
      - BACKEND_HOST=http://backend:5000
```

*BONUS:* mount the frontend folder as a volume for hot-reloading on code changes.
