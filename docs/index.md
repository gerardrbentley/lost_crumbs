---
title: Home
description: Gerard Bentley software engineer blog and technical notes home page.
hide:
  - navigation
  - toc
---

## Welcome :beers:

I'm Gerard Bentley, a software engineer interested in the web, machine learning, and how both impact us.
This is my blog and technical notes; feel free to poke around.

Currently working at [Sensible Weather](https://www.sensibleweather.com/) with a focus on Golang, Python, and Postgres webservices.

Most excited about time series data for environmental and social impact.

- [Github](https://github.com/gerardrbentley)
- [Fediverse](https://gerardbentley.com/@gar)
- [Linkedin](https://www.linkedin.com/in/gerardrbentley/) if that's how you connect
- [Resume](https://tech.gerardbentley.com/assets/gerard_bentley_resume.pdf) 

This site is generated from Markdown files with [MkDocs](https://www.mkdocs.org/) along with [MkDocs Material](https://squidfunk.github.io/mkdocs-material/).

## Some Demos

Here are some side projects I worked on in the recent year or so.

## :dart: Darts API Playground

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/gerardrbentley/darts-playground/main)

Explore the Datasets, Metrics, and Models of the Darts Time Series library.

See: [Github Repo](https://github.com/gerardrbentley/darts-playground)

![/images/demos/darts_playground.gif](/images/demos/darts_playground.gif)

## :link: URL Scanner

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/gerardrbentley/streamlit-url-scanner/main/streamlit_app/streamlit_app.py)

Using AWS Rekognition + Streamlit to provide interactive OCR URL Scanner / Text Extraction on real world images.

See: [Github Repo](https://github.com/gerardrbentley/streamlit-url-scanner)

![/images/demos/rekog_demo.gif](/images/demos/rekog_demo.gif)

## 🥞 WSGI Stack vs Streamlit

Comparing an interactive web app built with `bottle` + `htmx` to the same idea built with `streamlit`.

In folder `wsgi_comparison`

🎥 Watch: [Youtube Breakdown](https://www.youtube.com/watch?v=4V3VACzOmrI&t=2s)
✍🏻 Read: [Blog Post](https://tech.gerardbentley.com/streamlit/python/beginner/2022/03/23/bottle-htmx-streamlit.html)

Left: ~50 lines of Python and HTML

Right: ~15 lines of Python

![/images/demos/wsgi_compare_demo.gif](/images/demos/wsgi_compare_demo.gif)

## 🎸 Guitar Tuner

Simple guitar tuner powered by `streamlit-webrtc`

![/images/demos/trim_guitar.gif](/images/demos/trim_guitar.gif)

## :computer: Streamlit Full Stack 3 Ways

Demo of Full Stack Streamlit Concept.
Deployed with 3 increasingly complicated backends.

See: [Github Repo](https://github.com/gerardrbentley/streamlit-fullstack)

#### :mouse: Littlest

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/gerardrbentley/streamlit-fullstack/app.py)

#### :elephant: Postgres Version

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://streamlit-postgres.gerardbentley.com/)

#### :rat: Go Backend Version

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://st-pg-go.gerardbentley.com/)

## :chart_with_upwards_trend: Fidelity / Personal Stock Account Dashboard

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/gerardrbentley/fidelity-account-overview/main/app.py)

Upload a CSV export from Fidelity investment account(s) and visualize profits and losses from select tickers and accounts.

See: [Github Repo](https://github.com/gerardrbentley/fidelity-account-overview)

![/images/demos/account_overview.gif](/images/demos/account_overview.gif)

## 💾 Pipreqs API + Streamlit Frontend

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/gerardrbentley/pipreqs-api/streamlit_deploy/streamlit_app/streamlit_app.py)

FastAPI backend hosted on Heroku to parse repos and use `pipreqs` to spit out a minimal `requirements.txt`!

See: [Github Repo](https://github.com/gerardrbentley/pipreqs-api)

## 🚰 LightGBM Water Pump Predictions

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/gerardrbentley/pump-it-up/main)

Data Science project based on DrivenData "Pump It Up" competition.
Includes Data Exploration, Feature Engineering, and training and predicting functionality of water pumps with LightGBM

See: [Github Repo](https://github.com/gerardrbentley/pump-it-up)


## 💰 Personal Spending Dashboard

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/gerardrbentley/streamlit-random/main/personal_spending.py)

Upload a CSV or excel with at least a date column and spending amount column to analyze maximum and average spending over different time periods.

![/images/demos/personal_spending.gif](/images/demos/personal_spending.gif)

## :mount_fuji: Peak Weather: NH 4,000 Footers

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/gerardrbentley/peak-weather/main/streamlit_app/streamlit_app.py)

Use async http request library `httpx` to make 48 api calls roughly simultaneously in one Python process.
Feed a dashboard of weather for all 4,000 foot mountains in New Hampshire.

See: [Github Repo](https://github.com/gerardrbentley/peak-weather)

## 🐼 Pandas Power

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/gerardrbentley/streamlit-random/main/pandas_power.py)

Demoing useful functionalities of Pandas library in a web app.

Currently:

- `read_html`: Parse dataframes from html (url, upload, or raw copy+paste)

![/images/demos/pandas_html.gif](/images/demos/pandas_html.gif)

## ✍🏻 Text Recognition Dataset Generator App

Putting a frontend on TRDG CLI tool.
Primary goal: creating classic videogame text screenshots with known ground truth labels

![/images/demos/text_generator.gif](/images/demos/text_generator.gif)

## 🐙 Github Lines of Code Analyzer

Shallow clone a repo then use unix + pandas tools to count how many lines of each file type are present

`streamlit run github_code_analyze.py`

![/images/demos/github_lines_of_code.gif](/images/demos/github_lines_of_code.gif)

## :books: AWS Textract Document Text Scan

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/gerardrbentley/textract-streamlit-example/main/streamlit_app/streamlit_app.py)

Using AWS Textract + S3 + Streamlit to provide interactive OCR Web App.

See: [Github Repo](https://github.com/gerardrbentley/textract-streamlit-example)
