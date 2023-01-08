---
title: "Time Series Data Part 2: Darts and Streamlit"
description: Predicting the future (in some cases)
categories: 
  - time-series
tags:
  - time-series
  - darts
  - streamlit
  - python
date: 2022-03-10
---

# Time Series Data Part 2: Darts and Streamlit



![Screenshot of app forecasting gasoline price](/images/time_series/2022-03-10-15-58-35.png)


[Streamlit + Darts Demo live](https://share.streamlit.io/gerardrbentley/timeseries-examples/main/streamlit_apps/02_darts.py)

I wanted to explore the claim of "Time Series Made Easy in Python" by the [Darts](https://unit8co.github.io/darts/) library.

I knew from their [pydata talk](https://www.youtube.com/watch?v=g6OXDnXEtFA) that making something interactive around the training API would be straightforward.

Adding interactive web elements with [Streamlit](https://streamlit.io) to the Darts documentation example led to this quick demo project that lets you explore any univariate Timeseries CSV and make forecasts with Exponential Smoothing.
This version will resample and sum values to get to monthly samples (or change to weekly / quarterly / etc); there are other Pandas resampling aggregation options though!

See the [app script source](https://github.com/gerardrbentley/timeseries-examples/blob/main/streamlit_apps/02_darts.py)


[Free CSV Entry Direct Link](https://share.streamlit.io/gerardrbentley/timeseries-examples/main/streamlit_apps/02_darts.py#go-wild)

![darts demo on example data](/images/time_series/darts_demo.gif)
![darts demo on custom data](/images/time_series/darts_custom.gif)

Next steps on this would be:

- Series / Data info and timeseries attributes
- Exposing configuration options for the model
- Adding other [model options](https://unit8co.github.io/darts/generated_api/darts.models.forecasting.html) from Darts
- Backtest / Historical Forecast view
- Grid search result view