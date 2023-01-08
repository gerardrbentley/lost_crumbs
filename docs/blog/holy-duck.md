---
title: Holy 🦆uck! Fast Analysis with DuckDB + Pyarrow
description: Trying out some new speedy tools for data analysis
categories: 
    - libraries
tags:
    - python
    - data
    - intermediate
links:
  - Prerequisites:
    - setups/python.md
date: 2022-04-26
---

# Holy 🦆uck! Fast Analysis with DuckDB + Pyarrow



Turning to DuckDB when you need to crunch more numbers faster than pandas in your Streamlit app 🎈

Inspired by "DuckDB quacks Arrow" blogpost cross-posted on [duckdb](https://duckdb.org/2021/12/03/duck-arrow.html) and [arrow](https://arrow.apache.org/blog/2021/12/03/arrow-duckdb/)

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/gerardrbentley/uber-nyc-pickups-duckdb/main/streamlit_app_duck.py)

## Background

`streamlit` and Streamlit Cloud are fantastic for sharing your data exploration apps.
A very common pattern uses csv files with `pandas` to accomplish the necessary steps of:

- Load the data into the program
- Filter data by certain columns or attributes
- Compute analyses on the data (averages, counts, etc.)

## NYC Uber Data

- Streamlit DuckDB Uber NYC [repo](https://github.com/gerardrbentley/uber-nyc-pickups-duckdb)
  - Includes 10 Year, 1.5 Billion row Taxi data example as well
- Streamlit Original Uber NYC [repo](https://github.com/streamlit/demo-uber-nyc-pickups)

Let's take this NYC Uber dataset example from Streamlit.
We'll pay attention to:

- How much RAM / memory is used
- How long it takes to perform each step



```python
import pandas as pd
import numpy as np
# import streamlit as st

# singleton ignored because we're not in streamlit anymore
# @st.experimental_singleton
def load_data():
    data = pd.read_csv(
        "uber-raw-data-sep14.csv.gz",
        nrows=100000,  # approx. 10% of data
        names=[
            "date/time",
            "lat",
            "lon",
        ],  # specify names directly since they don't change
        skiprows=1,  # don't read header since names specified directly
        usecols=[0, 1, 2],  # doesn't load last column, constant value "B02512"
        parse_dates=[
            "date/time"
        ],  # set as datetime instead of converting after the fact
    )

    return data
```


```python
%%time
data = load_data()
```

    CPU times: user 2.99 s, sys: 48.1 ms, total: 3.04 s
    Wall time: 2.94 s



```python
data.info()
```

    <class 'pandas.core.frame.DataFrame'>
    RangeIndex: 100000 entries, 0 to 99999
    Data columns (total 3 columns):
     #   Column     Non-Null Count   Dtype         
    ---  ------     --------------   -----         
     0   date/time  100000 non-null  datetime64[ns]
     1   lat        100000 non-null  float64       
     2   lon        100000 non-null  float64       
    dtypes: datetime64[ns](1), float64(2)
    memory usage: 2.3 MB


Feel free to reference the `read_csv` [documentation](https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html), the focus of this post is on the `nrows=100000` argument though.

This `nrows` is used to limit the number of rows that get loaded into our application.
Taking in `100,000` rows landed us around `2.3 MB` of memory allocation for the data.

It loaded on my computer in `~3` seconds.

Let's see how that would go without our `nrows` limitation


```python
def load_full_data():
    data = pd.read_csv(
        "uber-raw-data-sep14.csv.gz",
        # nrows=100000,  # approx. 10% of data
        names=[
            "date/time",
            "lat",
            "lon",
        ],  # specify names directly since they don't change
        skiprows=1,  # don't read header since names specified directly
        usecols=[0, 1, 2],  # doesn't load last column, constant value "B02512"
        parse_dates=[
            "date/time"
        ],  # set as datetime instead of converting after the fact
    )

    return data
```


```python
%%time
full_data = load_full_data()
```

    CPU times: user 29.8 s, sys: 163 ms, total: 30 s
    Wall time: 30 s



```python
full_data.info()
```

    <class 'pandas.core.frame.DataFrame'>
    RangeIndex: 1028136 entries, 0 to 1028135
    Data columns (total 3 columns):
     #   Column     Non-Null Count    Dtype         
    ---  ------     --------------    -----         
     0   date/time  1028136 non-null  datetime64[ns]
     1   lat        1028136 non-null  float64       
     2   lon        1028136 non-null  float64       
    dtypes: datetime64[ns](1), float64(2)
    memory usage: 23.5 MB


Ok, so with `~10` times as much data (`1,028,136` vs `100,000`) we use:

- `~10` times as much memory (`23.5 MB` vs `2.3 MB`)
- `~10` times as much time (`30 s` vs `2.94 s`)

The first time this app loads in `streamlit` will be a bit slow either way, but the `singleton` decorator is designed to prevent having to re-compute objects like this.

(Also note that this is a single month of data... a year might include `~12,337,632` entries based on this september 2014 data)

## Enter the Duck

Using `pyarrow` and `duckdb` let's see if we get any improvement


```python
import duckdb
import pyarrow as pa
from pyarrow import csv
import pyarrow.dataset as ds

def load_data_duckdb():
    data = csv.read_csv('uber-raw-data-sep14.csv.gz', convert_options=csv.ConvertOptions(
        include_columns=["Date/Time","Lat","Lon"],
        timestamp_parsers=['%m/%d/%Y %H:%M:%S']
    )).rename_columns(['date/time', 'lat', 'lon'])

    # `dataset` is for partitioning larger datasets. Can't include timestamp parsing directly though
    # data = ds.dataset("uber-raw-data-sep14.csv.gz", schema=pa.schema([
    #     ("Date/Time", pa.timestamp('s')),
    #     ('Lat', pa.float32()),
    #     ('Lon', pa.float32())
    # ]), format='csv')

    # DuckDB can query Arrow tables, so we'll just return the table and a connection for flexible querying
    return data, duckdb.connect(":memory:")
arrow_data, con = load_data_duckdb()
arrow_data[:5]
```




    pyarrow.Table
    date/time: timestamp[s]
    lat: double
    lon: double
    ----
    date/time: [[2014-09-01 00:01:00,2014-09-01 00:01:00,2014-09-01 00:03:00,2014-09-01 00:06:00,2014-09-01 00:11:00]]
    lat: [[40.2201,40.75,40.7559,40.745,40.8145]]
    lon: [[-74.0021,-74.0027,-73.9864,-73.9889,-73.9444]]




```python
%%timeit
load_data_duckdb()
```

    153 ms ± 121 µs per loop (mean ± std. dev. of 7 runs, 10 loops each)


Holy Smokes! Well that was fast and fun!

`pyarrow` read the whole dataset in `153 ms`.
That's `0.153 s` compared to `30 s` with `pandas`!

So how much memory are `pyarrow` and `duckdb` using?


```python
def format_bytes(size):
    """from https://stackoverflow.com/a/49361727/15685218"""
    # 2**10 = 1024
    power = 2**10
    n = 0
    power_labels = {0 : '', 1: 'kilo', 2: 'mega', 3: 'giga', 4: 'tera'}
    while size > power:
        size /= power
        n += 1
    return size, power_labels[n]+'bytes'
```


```python
format_bytes(arrow_data.nbytes)
```




    (23.53216552734375, 'megabytes')



Ok, the `pyarrow` table has roughly the same size as the full `pandas` Dataframe


```python
con.execute('PRAGMA database_size;')
"""
database_size VARCHAR, -- total block count times the block size
block_size BIGINT,     -- database block size
total_blocks BIGINT,   -- total blocks in the database
used_blocks BIGINT,    -- used blocks in the database
free_blocks BIGINT,    -- free blocks in the database
wal_size VARCHAR,      -- write ahead log size
memory_usage VARCHAR,  -- memory used by the database buffer manager
memory_limit VARCHAR   -- maximum memory allowed for the database
"""
database_size, block_size, total_blocks, used_blocks, free_blocks, wal_size, memory_usage, memory_limit = con.fetchall()[0]
memory_usage
```




    '0 bytes'



We haven't told `duckdb` to load anything into its own tables, so it still has no memory usage.
Nevertheless, `duckdb` can query the `arrow_data` since it's a `pyarrow` table.
(`duckdb` can also load directly [from csv](https://duckdb.org/docs/data/csv)).

So where does that leave us on loading the full `1,000,000` row dataset?

- `pandas`: `~30 s` of time and `23.5 MB`
- `pyarrow`: `~.1 s` of time (`153 ms`) and `23.9 MB`

In fairness, I tried `pandas` with the `pyarrow` engine.
At the time of writing I can't find a fast datetime parse and `usecols` throws an error in `pyarrow` (see end of post).
Reading the full CSV without datetime parsing is in line in terms of speed though.

(also see why the best CSV [is not a CSV at all](https://pythonspeed.com/articles/pandas-read-csv-fast/) for more on this path)


```python
%%time
arrow_df = pd.read_csv(
    "uber-raw-data-sep14.csv.gz",
    engine='pyarrow',
    names=[
        "date/time",
        "lat",
        "lon",
        "CONST"
    ],  # specify names directly since they don't change
    skiprows=1,  # don't read header since names specified directly
    # usecols=[1, 2],  # doesn't load last column, constant value "B02512"
    parse_dates=[
        "date/time"
    ],  # set as datetime instead of converting after the fact
    # infer_datetime_format=True  # Unsupported for pyarrow
    date_parser=lambda x: pd.to_datetime(x)
)
```

    CPU times: user 30.2 s, sys: 193 ms, total: 30.4 s
    Wall time: 30.2 s



```python
arrow_df.info()
```

    <class 'pandas.core.frame.DataFrame'>
    RangeIndex: 1028136 entries, 0 to 1028135
    Data columns (total 4 columns):
     #   Column     Non-Null Count    Dtype         
    ---  ------     --------------    -----         
     0   date/time  1028136 non-null  datetime64[ns]
     1   lat        1028136 non-null  float64       
     2   lon        1028136 non-null  float64       
     3   CONST      1028136 non-null  object        
    dtypes: datetime64[ns](1), float64(2), object(1)
    memory usage: 31.4+ MB



```python
%%timeit
arrow_df_no_datetime = pd.read_csv(
    "uber-raw-data-sep14.csv.gz",
    engine='pyarrow',
    names=[
        "date/time",
        "lat",
        "lon",
        "CONST"
    ],  # specify names directly since they don't change
    skiprows=1,  # don't read header since names specified directly
    # usecols=[1, 2],  # doesn't load last column, constant value "B02512"
)
```

    139 ms ± 568 µs per loop (mean ± std. dev. of 7 runs, 10 loops each)


## Filtration

We have 3 main analysis functions to compare between `pandas` and `duckdb` for this app, laid out below:


```python
# FILTER DATA FOR A SPECIFIC HOUR, CACHE
# @st.experimental_memo
def filterdata(df, hour_selected):
    return df[df["date/time"].dt.hour == hour_selected]


# CALCULATE MIDPOINT FOR GIVEN SET OF DATA
# @st.experimental_memo
def mpoint(lat, lon):
    return (np.average(lat), np.average(lon))


# FILTER DATA BY HOUR
# @st.experimental_memo
def histdata(df, hr):
    filtered = data[
        (df["date/time"].dt.hour >= hr) & (df["date/time"].dt.hour < (hr + 1))
    ]

    hist = np.histogram(filtered["date/time"].dt.minute, bins=60, range=(0, 60))[0]

    return pd.DataFrame({"minute": range(60), "pickups": hist})
```


```python
%%timeit
# For fairness, we'll use the full dataframe
filterdata(full_data, 14)
```

    18 ms ± 65.4 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)



```python
%%timeit
mpoint(full_data["lat"], full_data["lon"])
```

    404 µs ± 1.65 µs per loop (mean ± std. dev. of 7 runs, 1,000 loops each)



```python
%%timeit
histdata(full_data, 14)
```

    /var/folders/cp/ktx4zddx7q3bqctqfjykn5700000gn/T/ipykernel_302/2026438809.py:16: UserWarning: Boolean Series key will be reindexed to match DataFrame index.
      filtered = data[


    39.9 ms ± 111 µs per loop (mean ± std. dev. of 7 runs, 10 loops each)


How about Duckdb (with conversion back to `pandas` for fairness)


```python
def duck_filterdata(con, hour_selected):
    return con.query(
        f'SELECT "date/time", lat, lon FROM arrow_data WHERE hour("date/time") = {hour_selected}'
    ).to_df()


def duck_mpoint(con):
    return con.query("SELECT AVG(lat), AVG(lon) FROM arrow_data").fetchone()


def duck_histdata(con, hr):
    hist_query = f'SELECT histogram(minute("date/time")) FROM arrow_data WHERE hour("date/time") >= {hr} and hour("date/time") < {hr + 1}'
    results, *_ = con.query(hist_query).fetchone()
    return pd.DataFrame(results)
```


```python
%%timeit
duck_filterdata(con, 14)
```

    6.03 ms ± 10.9 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)



```python
%%timeit
duck_mpoint(con)
```

    1.62 ms ± 16.6 µs per loop (mean ± std. dev. of 7 runs, 1,000 loops each)



```python
%%timeit
duck_histdata(con, 14)
```

    2.86 ms ± 19.5 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)



We got a modest improvement in `filterdata` and more than 10x speedup in `histdata`, but actually lost out to `numpy` for finding the average of 2 arrays in `mpoint`!

- `filterdata`:
  - `pandas`: 18 ms ± 65.4 µs
  - `duckdb`: 6.03 ms ± 10.9 µs
- `mpoint`:
  - `numpy`: 404 µs ± 1.65 µs
  - `duckdb`: 1.62 ms ± 16.6 µs
- `histdata`:
  - `pandas` + `numpy`: 39.9 ms ± 111 µs
  - `duckdb`: 2.86 ms ± 19.5 µs


```python
18 / 6.03
```




    2.9850746268656714




```python
404 / 1620
```




    0.24938271604938272




```python
39.9 / 2.86
```




    13.951048951048952



## Larger Than Memory Data

Where this DuckDB + Arrow combo really shines is analyzing data that can't be handled by Pandas on your machine.

In many cases if the data doesn't fit in your computer's memory (RAM) then using Pandas will consume disk (Swap) to try and fit it, which will slow things down.

With the 10 Year dataset below the DuckDB authors found Pandas used `248 GBs` (!!!) of memory to read out `~300,000` rows from the `~1,500,000,000`.
In this case it just crashes most laptops.

So there evolved libraries such as Dask for handling these out-of-core situations through multiprocessing and distributed computing.
Pandas has a whole list of [related ecosystem projects](https://pandas.pydata.org/pandas-docs/stable/ecosystem.html#ecosystem-out-of-core).

To cut through data on a single laptop, DuckDB + Arrow + the Parquet format provide some impressive optimizations to where we don't need those `248 GBs` on any number of machines.


```python
def load_from_10_year():
    nyc = ds.dataset("nyc-taxi/", partitioning=["year", "month"])
    # Get database connection
    con = duckdb.connect()

    # Run query that selects part of the data
    query = con.execute(
        f"SELECT total_amount, passenger_count,year FROM nyc where total_amount > 100 and year > 2014"
    )

    # Create Record Batch Reader from Query Result.
    # "fetch_record_batch()" also accepts an extra parameter related to the desired produced chunk size.
    record_batch_reader = query.fetch_record_batch()

    # Retrieve all batch chunks
    all_chunks = []
    while True:
        try:
            # Process a single chunk here
            # pyarrow.lib.RecordBatch
            chunk = record_batch_reader.read_next_batch()
            all_chunks.append(chunk)
        except StopIteration:
            break
    data = pa.Table.from_batches(all_chunks)
    return data

load_from_10_year()
```




    pyarrow.Table
    total_amount: float
    passenger_count: int8
    year: int32
    ----
    total_amount: [[149.3,132.18,205.05,137.55,106.57,107.3,187.85,145.55,230.3,118.3,...,104.42,110.8,102.04,112.56,209.9,103.41,175.8,144.95,241.92,102.8]]
    passenger_count: [[1,1,1,1,1,2,1,4,2,1,...,5,1,1,8,2,2,1,1,3,2]]
    year: [[2015,2015,2015,2015,2015,2015,2015,2015,2015,2015,...,2019,2019,2019,2019,2019,2019,2019,2019,2019,2019]]




```python
%%timeit
load_from_10_year()
```

    2.4 s ± 127 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)


Less than 3 seconds to sift through 1.5 Billion rows of data...

Let's look at how long it takes to iterate over the whole set in chunks (the inefficient solution to most out-of-memory issues)


```python
%%time
nyc = ds.dataset("nyc-taxi/", partitioning=["year", "month"])
# Get database connection
con = duckdb.connect()
query = con.execute(
    "SELECT total_amount FROM nyc"
)

record_batch_reader = query.fetch_record_batch()

total_rows = 0
while True:
    try:
        chunk = record_batch_reader.read_next_batch()
        total_rows += len(chunk)
    except StopIteration:
        break
total_rows
```

    CPU times: user 1min 30s, sys: 1min 54s, total: 3min 25s
    Wall time: 3min 53s





    1547741381



Iterating is definitely not going to work for user interactive apps.
2 - 3 seconds is bearable for most users (with a loading indicator), but 4 minutes is far too long to be engaging.

Pandas currently would need to perform this whole iteration or load the whole dataset to process the query we asked before.

Download instructions (from Ursa Labs S3 bucket) and Streamlit demo using the 10 year set is available in the [same repo](https://github.com/gerardrbentley/uber-nyc-pickups-duckdb)

## Conclusions

It's no secret that Python is not a fast language, but there are tricks to speed it up.
Common advice is to utilize C optimizations via `numpy` and `pandas`.

Another new contender is utilizing the C++ driven `duckdb` as an in-process OLAP database manager.
It takes some re-writing of Python code into SQL (or utilize the [Relational API](https://github.com/duckdb/duckdb/blob/master/examples/python/duckdb-python.py) or another library such as [Ibis Project](https://ibis-project.org/docs/3.0.2/)), but can play nicely with `pandas` and `pyarrow`.

Speaking of Arrow 🏹, it seems to be efficient and growing in popularity and adoption.
`streamlit` 🎈 utilizes it to simplify objects in protobufs [between browser and server](https://blog.streamlit.io/all-in-on-apache-arrow/).
`pandas` 🐼 has further integrations on [their roadmap](https://pandas.pydata.org/docs/development/roadmap.html#apache-arrow-interoperability).
`polars` 🐻‍❄️ uses it to power their Rust-written [DataFrame library](https://github.com/pola-rs/polars).

This post explores an example `streamlit` app that utilizes some `pandas` and `numpy` functions such as `read_csv`, `average`, and DataFrame slicing.

Using `pyarrow` to load data gives a speedup over the default `pandas` engine.
Using `duckdb` to generate new views of data also speeds up difficult computations.

It also touches on the power of this combination for processing larger than memory datasets efficiently on a single machine.


```python
pd.read_csv(
    "uber-raw-data-sep14.csv.gz",
    # nrows=100000,  # approx. 10% of data
    engine='pyarrow',
    names=[
        "date/time",
        "lat",
        "lon",
        # "CONST"
    ],  # specify names directly since they don't change
    skiprows=1,  # don't read header since names specified directly
    # usecols=[1, 2],  # doesn't load last column, constant value "B02512"
    parse_dates=[
        "date/time"
    ],  # set as datetime instead of converting after the fact
    # # infer_datetime_format=True  # Unsupported for pyarrow
    date_parser=lambda x: pd.to_datetime(x)
)
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>0</th>
      <th>date/time</th>
      <th>lat</th>
      <th>lon</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>9/1/2014 0:01:00</td>
      <td>1970-01-01 00:00:00.000000040</td>
      <td>-74.0021</td>
      <td>B02512</td>
    </tr>
    <tr>
      <th>1</th>
      <td>9/1/2014 0:01:00</td>
      <td>1970-01-01 00:00:00.000000040</td>
      <td>-74.0027</td>
      <td>B02512</td>
    </tr>
    <tr>
      <th>2</th>
      <td>9/1/2014 0:03:00</td>
      <td>1970-01-01 00:00:00.000000040</td>
      <td>-73.9864</td>
      <td>B02512</td>
    </tr>
    <tr>
      <th>3</th>
      <td>9/1/2014 0:06:00</td>
      <td>1970-01-01 00:00:00.000000040</td>
      <td>-73.9889</td>
      <td>B02512</td>
    </tr>
    <tr>
      <th>4</th>
      <td>9/1/2014 0:11:00</td>
      <td>1970-01-01 00:00:00.000000040</td>
      <td>-73.9444</td>
      <td>B02512</td>
    </tr>
    <tr>
      <th>...</th>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
    </tr>
    <tr>
      <th>1028131</th>
      <td>9/30/2014 22:57:00</td>
      <td>1970-01-01 00:00:00.000000040</td>
      <td>-73.9845</td>
      <td>B02764</td>
    </tr>
    <tr>
      <th>1028132</th>
      <td>9/30/2014 22:57:00</td>
      <td>1970-01-01 00:00:00.000000040</td>
      <td>-74.1773</td>
      <td>B02764</td>
    </tr>
    <tr>
      <th>1028133</th>
      <td>9/30/2014 22:58:00</td>
      <td>1970-01-01 00:00:00.000000040</td>
      <td>-73.9319</td>
      <td>B02764</td>
    </tr>
    <tr>
      <th>1028134</th>
      <td>9/30/2014 22:58:00</td>
      <td>1970-01-01 00:00:00.000000040</td>
      <td>-74.0066</td>
      <td>B02764</td>
    </tr>
    <tr>
      <th>1028135</th>
      <td>9/30/2014 22:58:00</td>
      <td>1970-01-01 00:00:00.000000040</td>
      <td>-73.9496</td>
      <td>B02764</td>
    </tr>
  </tbody>
</table>
<p>1028136 rows × 4 columns</p>
</div>




```python
pd.read_csv(
    "uber-raw-data-sep14.csv.gz",
    # nrows=100000,  # approx. 10% of data
    engine='pyarrow',
    # names=[
    #     "date/time",
    #     "lat",
    #     "lon",
    #     "CONST"
    # ],  # specify names directly since they don't change
    # skiprows=1,  # don't read header since names specified directly
    usecols=[0,1],  # doesn't load last column, constant value "B02512"
    # parse_dates=[
    #     "date/time"
    # ],  # set as datetime instead of converting after the fact
    # # infer_datetime_format=True  # Unsupported for pyarrow
    # date_parser=lambda x: pd.to_datetime(x)
).info()
```


    ---------------------------------------------------------------------------

    TypeError                                 Traceback (most recent call last)

    /Users/gar/projects/tech-blog/_notebooks/2022-04-26-holy-duck.ipynb Cell 44' in <cell line: 1>()
    ----> <a href='vscode-notebook-cell:/Users/gar/projects/tech-blog/_notebooks/2022-04-26-holy-duck.ipynb#ch0000038?line=0'>1</a> pd.read_csv(
          <a href='vscode-notebook-cell:/Users/gar/projects/tech-blog/_notebooks/2022-04-26-holy-duck.ipynb#ch0000038?line=1'>2</a>     "uber-raw-data-sep14.csv.gz",
          <a href='vscode-notebook-cell:/Users/gar/projects/tech-blog/_notebooks/2022-04-26-holy-duck.ipynb#ch0000038?line=2'>3</a>     # nrows=100000,  # approx. 10% of data
          <a href='vscode-notebook-cell:/Users/gar/projects/tech-blog/_notebooks/2022-04-26-holy-duck.ipynb#ch0000038?line=3'>4</a>     engine='pyarrow',
          <a href='vscode-notebook-cell:/Users/gar/projects/tech-blog/_notebooks/2022-04-26-holy-duck.ipynb#ch0000038?line=4'>5</a>     # names=[
          <a href='vscode-notebook-cell:/Users/gar/projects/tech-blog/_notebooks/2022-04-26-holy-duck.ipynb#ch0000038?line=5'>6</a>     #     "date/time",
          <a href='vscode-notebook-cell:/Users/gar/projects/tech-blog/_notebooks/2022-04-26-holy-duck.ipynb#ch0000038?line=6'>7</a>     #     "lat",
          <a href='vscode-notebook-cell:/Users/gar/projects/tech-blog/_notebooks/2022-04-26-holy-duck.ipynb#ch0000038?line=7'>8</a>     #     "lon",
          <a href='vscode-notebook-cell:/Users/gar/projects/tech-blog/_notebooks/2022-04-26-holy-duck.ipynb#ch0000038?line=8'>9</a>     #     "CONST"
         <a href='vscode-notebook-cell:/Users/gar/projects/tech-blog/_notebooks/2022-04-26-holy-duck.ipynb#ch0000038?line=9'>10</a>     # ],  # specify names directly since they don't change
         <a href='vscode-notebook-cell:/Users/gar/projects/tech-blog/_notebooks/2022-04-26-holy-duck.ipynb#ch0000038?line=10'>11</a>     # skiprows=1,  # don't read header since names specified directly
         <a href='vscode-notebook-cell:/Users/gar/projects/tech-blog/_notebooks/2022-04-26-holy-duck.ipynb#ch0000038?line=11'>12</a>     usecols=[0,1],  # doesn't load last column, constant value "B02512"
         <a href='vscode-notebook-cell:/Users/gar/projects/tech-blog/_notebooks/2022-04-26-holy-duck.ipynb#ch0000038?line=12'>13</a>     # parse_dates=[
         <a href='vscode-notebook-cell:/Users/gar/projects/tech-blog/_notebooks/2022-04-26-holy-duck.ipynb#ch0000038?line=13'>14</a>     #     "date/time"
         <a href='vscode-notebook-cell:/Users/gar/projects/tech-blog/_notebooks/2022-04-26-holy-duck.ipynb#ch0000038?line=14'>15</a>     # ],  # set as datetime instead of converting after the fact
         <a href='vscode-notebook-cell:/Users/gar/projects/tech-blog/_notebooks/2022-04-26-holy-duck.ipynb#ch0000038?line=15'>16</a>     # # infer_datetime_format=True  # Unsupported for pyarrow
         <a href='vscode-notebook-cell:/Users/gar/projects/tech-blog/_notebooks/2022-04-26-holy-duck.ipynb#ch0000038?line=16'>17</a>     # date_parser=lambda x: pd.to_datetime(x)
         <a href='vscode-notebook-cell:/Users/gar/projects/tech-blog/_notebooks/2022-04-26-holy-duck.ipynb#ch0000038?line=17'>18</a> ).info()


    File ~/miniconda3/envs/py39/lib/python3.9/site-packages/pandas/util/_decorators.py:311, in deprecate_nonkeyword_arguments.<locals>.decorate.<locals>.wrapper(*args, **kwargs)
        <a href='file:///Users/gar/miniconda3/envs/py39/lib/python3.9/site-packages/pandas/util/_decorators.py?line=304'>305</a> if len(args) > num_allow_args:
        <a href='file:///Users/gar/miniconda3/envs/py39/lib/python3.9/site-packages/pandas/util/_decorators.py?line=305'>306</a>     warnings.warn(
        <a href='file:///Users/gar/miniconda3/envs/py39/lib/python3.9/site-packages/pandas/util/_decorators.py?line=306'>307</a>         msg.format(arguments=arguments),
        <a href='file:///Users/gar/miniconda3/envs/py39/lib/python3.9/site-packages/pandas/util/_decorators.py?line=307'>308</a>         FutureWarning,
        <a href='file:///Users/gar/miniconda3/envs/py39/lib/python3.9/site-packages/pandas/util/_decorators.py?line=308'>309</a>         stacklevel=stacklevel,
        <a href='file:///Users/gar/miniconda3/envs/py39/lib/python3.9/site-packages/pandas/util/_decorators.py?line=309'>310</a>     )
    --> <a href='file:///Users/gar/miniconda3/envs/py39/lib/python3.9/site-packages/pandas/util/_decorators.py?line=310'>311</a> return func(*args, **kwargs)


    File ~/miniconda3/envs/py39/lib/python3.9/site-packages/pandas/io/parsers/readers.py:680, in read_csv(filepath_or_buffer, sep, delimiter, header, names, index_col, usecols, squeeze, prefix, mangle_dupe_cols, dtype, engine, converters, true_values, false_values, skipinitialspace, skiprows, skipfooter, nrows, na_values, keep_default_na, na_filter, verbose, skip_blank_lines, parse_dates, infer_datetime_format, keep_date_col, date_parser, dayfirst, cache_dates, iterator, chunksize, compression, thousands, decimal, lineterminator, quotechar, quoting, doublequote, escapechar, comment, encoding, encoding_errors, dialect, error_bad_lines, warn_bad_lines, on_bad_lines, delim_whitespace, low_memory, memory_map, float_precision, storage_options)
        <a href='file:///Users/gar/miniconda3/envs/py39/lib/python3.9/site-packages/pandas/io/parsers/readers.py?line=664'>665</a> kwds_defaults = _refine_defaults_read(
        <a href='file:///Users/gar/miniconda3/envs/py39/lib/python3.9/site-packages/pandas/io/parsers/readers.py?line=665'>666</a>     dialect,
        <a href='file:///Users/gar/miniconda3/envs/py39/lib/python3.9/site-packages/pandas/io/parsers/readers.py?line=666'>667</a>     delimiter,
       (...)
        <a href='file:///Users/gar/miniconda3/envs/py39/lib/python3.9/site-packages/pandas/io/parsers/readers.py?line=675'>676</a>     defaults={"delimiter": ","},
        <a href='file:///Users/gar/miniconda3/envs/py39/lib/python3.9/site-packages/pandas/io/parsers/readers.py?line=676'>677</a> )
        <a href='file:///Users/gar/miniconda3/envs/py39/lib/python3.9/site-packages/pandas/io/parsers/readers.py?line=677'>678</a> kwds.update(kwds_defaults)
    --> <a href='file:///Users/gar/miniconda3/envs/py39/lib/python3.9/site-packages/pandas/io/parsers/readers.py?line=679'>680</a> return _read(filepath_or_buffer, kwds)


    File ~/miniconda3/envs/py39/lib/python3.9/site-packages/pandas/io/parsers/readers.py:581, in _read(filepath_or_buffer, kwds)
        <a href='file:///Users/gar/miniconda3/envs/py39/lib/python3.9/site-packages/pandas/io/parsers/readers.py?line=577'>578</a>     return parser
        <a href='file:///Users/gar/miniconda3/envs/py39/lib/python3.9/site-packages/pandas/io/parsers/readers.py?line=579'>580</a> with parser:
    --> <a href='file:///Users/gar/miniconda3/envs/py39/lib/python3.9/site-packages/pandas/io/parsers/readers.py?line=580'>581</a>     return parser.read(nrows)


    File ~/miniconda3/envs/py39/lib/python3.9/site-packages/pandas/io/parsers/readers.py:1243, in TextFileReader.read(self, nrows)
       <a href='file:///Users/gar/miniconda3/envs/py39/lib/python3.9/site-packages/pandas/io/parsers/readers.py?line=1240'>1241</a> if self.engine == "pyarrow":
       <a href='file:///Users/gar/miniconda3/envs/py39/lib/python3.9/site-packages/pandas/io/parsers/readers.py?line=1241'>1242</a>     try:
    -> <a href='file:///Users/gar/miniconda3/envs/py39/lib/python3.9/site-packages/pandas/io/parsers/readers.py?line=1242'>1243</a>         df = self._engine.read()
       <a href='file:///Users/gar/miniconda3/envs/py39/lib/python3.9/site-packages/pandas/io/parsers/readers.py?line=1243'>1244</a>     except Exception:
       <a href='file:///Users/gar/miniconda3/envs/py39/lib/python3.9/site-packages/pandas/io/parsers/readers.py?line=1244'>1245</a>         self.close()


    File ~/miniconda3/envs/py39/lib/python3.9/site-packages/pandas/io/parsers/arrow_parser_wrapper.py:153, in ArrowParserWrapper.read(self)
        <a href='file:///Users/gar/miniconda3/envs/py39/lib/python3.9/site-packages/pandas/io/parsers/arrow_parser_wrapper.py?line=145'>146</a> pyarrow_csv = import_optional_dependency("pyarrow.csv")
        <a href='file:///Users/gar/miniconda3/envs/py39/lib/python3.9/site-packages/pandas/io/parsers/arrow_parser_wrapper.py?line=146'>147</a> self._get_pyarrow_options()
        <a href='file:///Users/gar/miniconda3/envs/py39/lib/python3.9/site-packages/pandas/io/parsers/arrow_parser_wrapper.py?line=148'>149</a> table = pyarrow_csv.read_csv(
        <a href='file:///Users/gar/miniconda3/envs/py39/lib/python3.9/site-packages/pandas/io/parsers/arrow_parser_wrapper.py?line=149'>150</a>     self.src,
        <a href='file:///Users/gar/miniconda3/envs/py39/lib/python3.9/site-packages/pandas/io/parsers/arrow_parser_wrapper.py?line=150'>151</a>     read_options=pyarrow_csv.ReadOptions(**self.read_options),
        <a href='file:///Users/gar/miniconda3/envs/py39/lib/python3.9/site-packages/pandas/io/parsers/arrow_parser_wrapper.py?line=151'>152</a>     parse_options=pyarrow_csv.ParseOptions(**self.parse_options),
    --> <a href='file:///Users/gar/miniconda3/envs/py39/lib/python3.9/site-packages/pandas/io/parsers/arrow_parser_wrapper.py?line=152'>153</a>     convert_options=pyarrow_csv.ConvertOptions(**self.convert_options),
        <a href='file:///Users/gar/miniconda3/envs/py39/lib/python3.9/site-packages/pandas/io/parsers/arrow_parser_wrapper.py?line=153'>154</a> )
        <a href='file:///Users/gar/miniconda3/envs/py39/lib/python3.9/site-packages/pandas/io/parsers/arrow_parser_wrapper.py?line=155'>156</a> frame = table.to_pandas()
        <a href='file:///Users/gar/miniconda3/envs/py39/lib/python3.9/site-packages/pandas/io/parsers/arrow_parser_wrapper.py?line=156'>157</a> return self._finalize_output(frame)


    File ~/miniconda3/envs/py39/lib/python3.9/site-packages/pyarrow/_csv.pyx:580, in pyarrow._csv.ConvertOptions.__init__()


    File ~/miniconda3/envs/py39/lib/python3.9/site-packages/pyarrow/_csv.pyx:734, in pyarrow._csv.ConvertOptions.include_columns.__set__()


    File stringsource:15, in string.from_py.__pyx_convert_string_from_py_std__in_string()


    TypeError: expected bytes, int found

