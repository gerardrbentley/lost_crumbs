---
title: "Time Series Data Part 4: A Full Stack Use Case"
description: Data Analysis meets Data Science meets Data Engineering meets Data Operations
categories: 
  - time-series
tags:
  - time-series
  - darts
  - streamlit
  - python
  - intermediate
date: 2022-03-15
---

# Time Series Data Part 4: A Full Stack Use Case


![Time series app screenshot](/images/time_series/2022-03-15-14-20-49.png)


## Roommate Spending Ledger Visualization

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/gerardrbentley/roommate-ledger/main/app.py)

Using Pandas + Plotly + SQLite to show a full stack use case of Time Series Data.

Analyze spending over time per person (could be adapted to categories / tags / etc).

See: [Github Repo](https://github.com/gerardrbentley/roommate-ledger)

## Idea

One time series that any financially independent person should pay attention to is their spending over time.

Tracking your spending gets complicated with roommates and budgets for different categories.
It also complicates your understanding of your data with a glance, which is where charts and graphs can help.

There are many personal budgeting and even group budgeting apps, but I wanted to make the simplest possible and stick to the Data and Visualizations as an MVP.

One way to get this data is from a CSV export from a bank account or credit card company.
In [Part 3]({% post_url 2022-03-11-timeseries-part-3 %}) is an app that uses this method on general time series data.
Upload a CSV with some column for time stamps and some column to forecast and tune your own prediction model!

The main drawbacks to this paradigm:

- Can't share data between people / sessions
- Can't persist data
- Can't incrementally add data
- Can't update data

Another way is the CRUD paradigm explored in my [Streamlit Full Stack Post]({% post_url 2022-02-10-streamlit-fullstack %}).
With this method we'll be able to operate on individual data points and let our friends / roommates add to it!

(Of course the CSV paradigm could be blended with this)

Now for each aspect of the app, from Backend to Front

## DevOps

There's not much real DataOps in this project since the data is self-contained.

That said, there are some DevOps aspects that are important in the time series world:

- Deployment: having a webserver accessible to multiple users
- Integration: how to get updated code into the deployment(s)

Leaning on Streamlit Cloud sharing checks both of these boxes with ease.

By including a `requirements.txt` and specifying a python version for the image, we get a free CI/CD pipeline from any push to a github branch (more providers to come).
It'll provide us with an Ubuntu-like container that installs all requirements and tries to perform `streamlit run streamlit_app.py`, yielding a live webserver accessible to the public for public repos!

## Backend

The Data Engineering aspect involves a bit of data design and a bit of service writing.

I decided the minimum data to track expenses are:

- `purchased_date`
  - The day on which the purchase was made
- `purchased_by`
  - The name of the person who made the purchase
- `price_in_cents`
  - Price of the purchase. Tracked in cents to avoid [floating point perils](https://www.lahey.com/float.htm)

Relying on SQLite, we'll have to represent the date as a string, but `pandas` will help us transform it to a date / datetime object.
A table creation routine with SQLite for this might look like:


```python
import sqlite3
from typing import Optional

def get_connection(connection_string: str = ":memory:") -> sqlite3.Connection:
    """Make a connection object to sqlite3 with key-value Rows as outputs
    - https://stackoverflow.com/questions/48218065/programmingerror-sqlite-objects-created-in-a-thread-can-only-be-used-in-that-sa
    """
    connection = sqlite3.connect(connection_string)
    connection.row_factory = sqlite3.Row
    return connection

def execute_query(
    connection: sqlite3.Connection, query: str, args: Optional[dict] = None
) -> list:
    """Given sqlite3.Connection and a string query (and optionally necessary query args as a dict),
    Attempt to execute query with cursor, commit transaction, and return fetched rows"""
    cur = connection.cursor()
    if args is not None:
        cur.execute(query, args)
    else:
        cur.execute(query)
    connection.commit()
    results = cur.fetchall()
    cur.close()
    return results

def create_expenses_table(connection: sqlite3.Connection) -> None:
    """Create Expenses Table in the database if it doesn't already exist"""
    init_expenses_query = f"""CREATE TABLE IF NOT EXISTS expenses(
   purchased_date VARCHAR(10) NOT NULL,
   purchased_by VARCHAR(120) NOT NULL,
   price_in_cents INT NOT NULL);"""
    execute_query(connection, init_expenses_query)

connection = get_connection()
create_expenses_table(connection)
info_results = execute_query(connection, "SELECT name, type, sql FROM sqlite_schema WHERE name = 'expenses'")
info = info_results[0]
info['name'], info['type'], info['sql']
```




    ('expenses',
     'table',
     'CREATE TABLE expenses(\n   purchased_date VARCHAR(10) NOT NULL,\n   purchased_by VARCHAR(120) NOT NULL,\n   price_in_cents INT NOT NULL)')



We also get a free autoincrementing `rowid` from SQLite, which will differentiate any purchases by the same person on the same day for the same amount!

### Python Object Model

That's all well and good for a DBA, but what about the Python glue?

Using `pydantic` / `dataclasses` is my preferred way to make Python classes that represent database objects or API responses.
Splitting the Model into a child class for the internal application usage and parent class for database syncing is one way to handle auto-created id's and optional vs. required arguments.


```python
from datetime import date
from pydantic import BaseModel

class BaseExpense(BaseModel):
    price_in_cents: int
    purchased_date: date
    purchased_by: str

class Expense(BaseExpense):
    rowid: int

Expense(rowid=1, price_in_cents=100, purchased_date=date(2022, 3, 15), purchased_by='gar')
```




    Expense(price_in_cents=100, purchased_date=datetime.date(2022, 3, 15), purchased_by='gar', rowid=1)



### Seeding

To get some values for playing around with and demonstrating Create / Update, here's a snippet of seeding the database


```python
import random
def seed_expenses_table(connection: sqlite3.Connection) -> None:
    """Insert sample Expense rows into the database"""
    for i in range(200):
        seed_expense = Expense(
            rowid=i,
            purchased_date=date(
                random.randint(2020, 2022), random.randint(1, 12), random.randint(1, 28)
            ).strftime("%Y-%m-%d"),
            purchased_by=random.choice(["Alice", "Bob", "Chuck"]),
            price_in_cents=random.randint(50, 100_00),
        )
        seed_expense_query = f"""REPLACE into expenses(rowid, purchased_date, purchased_by, price_in_cents)
        VALUES(:rowid, :purchased_date, :purchased_by, :price_in_cents);"""
        execute_query(connection, seed_expense_query, seed_expense.dict())

seed_expenses_table(connection)
print('Seeded 200 rows')
```

    Seeded 200 rows



200 times we'll create and save an Expense object with a hardcoded id and some random values for date, purchaser, and price.
(Note the randomized days max out at 28 to avoid headaches with february being short. There's probably a builtin to help with random days, maybe just timedelta with random amount is easier)

Using `kwarg` placeholders of the form `:keyname` lets us pass the dictionary / JSON representation of our Python object instead of specifying each invidual field in the correct order.

The rest of the CRUD operations follow a similar pattern.
Reading is the only hacky function to allow filtering / querying at database level before pulling **ALL** records into memory.

## Reshaping the Data

The Data Science aspect of this involves massaging the data into something useful to display.

The data as it stands is not actually the well formed time series you might have thought.

Sure the date stamps are all real, but what value do we read from them?
The goal is to track spending (`price_in_cents` in the database).

But what if we have multiple purchases on the same day?
Then we might start treating all the purchases on a given day as stochastic samples and that is not our use case. (But that might fit your use case if you are trying to model behaviour based off of **many** people's purchases)

### Enter the Pandas

Utilizing Pydantic to parse / validate our database data then dumping as a list of dictionaries for Pandas to handle gets us a dataframe with all the expenses we want to see.
Passing a `start_date`, `end_date`, and `selections` will limit the data to certain time range and `purchased_by` users.


```python
#collapse-hide
from typing import List

class ExpenseService:
    """Namespace for Database Related Expense Operations"""

    def list_all_purchasers(connection: sqlite3.Connection) -> List[str]:
        select_purchasers = "SELECT DISTINCT purchased_by FROM expenses"
        expense_rows = execute_query(connection, select_purchasers)
        return [x["purchased_by"] for x in expense_rows]

    def list_all_expenses(
        connection: sqlite3.Connection,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        selections: Optional[list[str]] = None,
    ) -> List[sqlite3.Row]:
        """Returns rows from all expenses. Ordered in reverse creation order"""
        select = (
            "SELECT rowid, purchased_date, purchased_by, price_in_cents FROM expenses"
        )
        where = ""
        do_and = False
        kwargs = {}
        if any(x is not None for x in (start_date, end_date, selections)):
            where = "WHERE"
        if start_date is not None:
            where += " purchased_date >= :start_date"
            kwargs["start_date"] = start_date
            do_and = True
        if end_date is not None:
            if do_and:
                where += " and"
            where += " purchased_date <= :end_date"
            kwargs["end_date"] = end_date
            do_and = True
        if selections is not None:
            if do_and:
                where += " and"
            selection_map = {str(i): x for i, x in enumerate(selections)}
            where += (
                f" purchased_by IN ({','.join(':' + x for x in selection_map.keys())})"
            )
            kwargs.update(selection_map)

        order_by = "ORDER BY purchased_date DESC;"
        query = " ".join((select, where, order_by))
        expense_rows = execute_query(connection, query, kwargs)
        return expense_rows
```


```python
import pandas as pd
expense_rows = ExpenseService.list_all_expenses(
    connection, date(1900, 1, 1), date(2023, 1, 1), ['Alice', 'Bob', 'Chuck']
)
expenses = [Expense(**row) for row in expense_rows]
raw_df = pd.DataFrame([x.dict() for x in expenses])
raw_df.iloc[:3]

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
      <th>price_in_cents</th>
      <th>purchased_date</th>
      <th>purchased_by</th>
      <th>rowid</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>9662</td>
      <td>2022-12-13</td>
      <td>Alice</td>
      <td>2</td>
    </tr>
    <tr>
      <th>1</th>
      <td>9925</td>
      <td>2022-12-12</td>
      <td>Alice</td>
      <td>138</td>
    </tr>
    <tr>
      <th>2</th>
      <td>6287</td>
      <td>2022-12-10</td>
      <td>Bob</td>
      <td>92</td>
    </tr>
  </tbody>
</table>
</div>



For this analysis I mainly care about total purchase amount per day per person.
This means the rowid doesn't really matter to me as a unique identifier, so let's drop it.

(This indexing selection will also re-order your columns if you do or do not want that)


```python
df = raw_df[["purchased_date", "purchased_by", "price_in_cents"]]
df.iloc[:3]
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
      <th>purchased_date</th>
      <th>purchased_by</th>
      <th>price_in_cents</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>2022-12-13</td>
      <td>Alice</td>
      <td>9662</td>
    </tr>
    <tr>
      <th>1</th>
      <td>2022-12-12</td>
      <td>Alice</td>
      <td>9925</td>
    </tr>
    <tr>
      <th>2</th>
      <td>2022-12-10</td>
      <td>Bob</td>
      <td>6287</td>
    </tr>
  </tbody>
</table>
</div>



To handle the summation of each person's purchase per day, pandas `pivot_table` provides us the grouping and sum in one function call.

This will get us roughly columnar shaped data for each person


```python
pivot_df = df.pivot_table(
    index="purchased_date", columns="purchased_by", aggfunc="sum", fill_value=0
)
pivot_df.iloc[:3]
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead tr th {
        text-align: left;
    }

    .dataframe thead tr:last-of-type th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr>
      <th></th>
      <th colspan="3" halign="left">price_in_cents</th>
    </tr>
    <tr>
      <th>purchased_by</th>
      <th>Alice</th>
      <th>Bob</th>
      <th>Chuck</th>
    </tr>
    <tr>
      <th>purchased_date</th>
      <th></th>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>2020-01-01</th>
      <td>0</td>
      <td>0</td>
      <td>1566</td>
    </tr>
    <tr>
      <th>2020-01-20</th>
      <td>0</td>
      <td>7072</td>
      <td>0</td>
    </tr>
    <tr>
      <th>2020-01-26</th>
      <td>0</td>
      <td>0</td>
      <td>9982</td>
    </tr>
  </tbody>
</table>
</div>



Looking more like a time series!

`pivot_table` had the minor side effect of adding a multi index, which can be popped off if not relevant


```python
pivot_df.columns = pivot_df.columns.droplevel(0)
pivot_df.iloc[:3]
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
      <th>purchased_by</th>
      <th>Alice</th>
      <th>Bob</th>
      <th>Chuck</th>
    </tr>
    <tr>
      <th>purchased_date</th>
      <th></th>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>2020-01-01</th>
      <td>0</td>
      <td>0</td>
      <td>1566</td>
    </tr>
    <tr>
      <th>2020-01-20</th>
      <td>0</td>
      <td>7072</td>
      <td>0</td>
    </tr>
    <tr>
      <th>2020-01-26</th>
      <td>0</td>
      <td>0</td>
      <td>9982</td>
    </tr>
  </tbody>
</table>
</div>



Side note:
I also added a feature where "All" is a valid selection in addition to all `purchased_by` users.

The "All" spending per day is the sum of each row!

(We can sanity check this by checking for rows with 2 non-zero values and sum those up to check the All column)


```python
pivot_df['All'] = pivot_df.sum(axis=1)
pivot_df[(pivot_df.Alice > 0) & (pivot_df.Bob > 0)]
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
      <th>purchased_by</th>
      <th>Alice</th>
      <th>Bob</th>
      <th>Chuck</th>
      <th>All</th>
    </tr>
    <tr>
      <th>purchased_date</th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>2020-08-12</th>
      <td>3716</td>
      <td>5896</td>
      <td>0</td>
      <td>9612</td>
    </tr>
    <tr>
      <th>2020-10-09</th>
      <td>4881</td>
      <td>2595</td>
      <td>0</td>
      <td>7476</td>
    </tr>
    <tr>
      <th>2021-04-11</th>
      <td>3965</td>
      <td>3623</td>
      <td>0</td>
      <td>7588</td>
    </tr>
    <tr>
      <th>2021-10-19</th>
      <td>3332</td>
      <td>627</td>
      <td>611</td>
      <td>4570</td>
    </tr>
    <tr>
      <th>2022-01-08</th>
      <td>5021</td>
      <td>11061</td>
      <td>0</td>
      <td>16082</td>
    </tr>
    <tr>
      <th>2022-03-01</th>
      <td>6895</td>
      <td>4857</td>
      <td>0</td>
      <td>11752</td>
    </tr>
    <tr>
      <th>2022-08-03</th>
      <td>8642</td>
      <td>258</td>
      <td>0</td>
      <td>8900</td>
    </tr>
    <tr>
      <th>2022-09-11</th>
      <td>4751</td>
      <td>1617</td>
      <td>0</td>
      <td>6368</td>
    </tr>
  </tbody>
</table>
</div>



To fill in date gaps (make the time series have a well defined period of one day), one way is to build your own range of dates and then reindex the time series dataframe with the full range of dates.

Grabbing the min and max of the current index gets the start and end points for the range.
Filling with 0 is fine by me since there were no purchases on those days



```python
min_date = pivot_df.index.min()
max_date = pivot_df.index.max()
all_dates = pd.date_range(min_date, max_date, freq="D", name="purchased_date")
pivot_df = pivot_df.reindex(all_dates, fill_value=0)
pivot_df.iloc[:3]
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
      <th>purchased_by</th>
      <th>Alice</th>
      <th>Bob</th>
      <th>Chuck</th>
      <th>All</th>
    </tr>
    <tr>
      <th>purchased_date</th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>2020-01-01</th>
      <td>0</td>
      <td>0</td>
      <td>1566</td>
      <td>1566</td>
    </tr>
    <tr>
      <th>2020-01-02</th>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>2020-01-03</th>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
  </tbody>
</table>
</div>



To get the cumulative spend up to each point in time, pandas provides `cumsum()`


```python
cumulative = pivot_df.cumsum()
cumulative.iloc[:5]
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
      <th>purchased_by</th>
      <th>Alice</th>
      <th>Bob</th>
      <th>Chuck</th>
      <th>All</th>
    </tr>
    <tr>
      <th>purchased_date</th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>2020-01-01</th>
      <td>0</td>
      <td>0</td>
      <td>1566</td>
      <td>1566</td>
    </tr>
    <tr>
      <th>2020-01-02</th>
      <td>0</td>
      <td>0</td>
      <td>1566</td>
      <td>1566</td>
    </tr>
    <tr>
      <th>2020-01-03</th>
      <td>0</td>
      <td>0</td>
      <td>1566</td>
      <td>1566</td>
    </tr>
    <tr>
      <th>2020-01-04</th>
      <td>0</td>
      <td>0</td>
      <td>1566</td>
      <td>1566</td>
    </tr>
    <tr>
      <th>2020-01-05</th>
      <td>0</td>
      <td>0</td>
      <td>1566</td>
      <td>1566</td>
    </tr>
  </tbody>
</table>
</div>



And to analyze percentage contributed to the whole group's cumulative spending we can divide by the sum of each cumulative row.

(We included the "All" summation already, so this case is actually slightly over-complicated)


```python
percentages = (
    cumulative[cumulative.columns.drop("All", errors="ignore")]
    .divide(cumulative.sum(axis=1), axis=0)
    .multiply(100)
)
percentages.iloc[:5]
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
      <th>purchased_by</th>
      <th>Alice</th>
      <th>Bob</th>
      <th>Chuck</th>
    </tr>
    <tr>
      <th>purchased_date</th>
      <th></th>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>2020-01-01</th>
      <td>0.0</td>
      <td>0.0</td>
      <td>50.0</td>
    </tr>
    <tr>
      <th>2020-01-02</th>
      <td>0.0</td>
      <td>0.0</td>
      <td>50.0</td>
    </tr>
    <tr>
      <th>2020-01-03</th>
      <td>0.0</td>
      <td>0.0</td>
      <td>50.0</td>
    </tr>
    <tr>
      <th>2020-01-04</th>
      <td>0.0</td>
      <td>0.0</td>
      <td>50.0</td>
    </tr>
    <tr>
      <th>2020-01-05</th>
      <td>0.0</td>
      <td>0.0</td>
      <td>50.0</td>
    </tr>
  </tbody>
</table>
</div>



Grabbing the totals of each spender might be a nice metric to display.

This could also be grabbed from the end of the cumulative data


```python
totals = pivot_df.sum()
totals.index.name = "purchased_by"
totals.name = "value"
totals = totals.div(100).reset_index()
totals
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
      <th>purchased_by</th>
      <th>value</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>Alice</td>
      <td>3565.16</td>
    </tr>
    <tr>
      <th>1</th>
      <td>Bob</td>
      <td>3019.81</td>
    </tr>
    <tr>
      <th>2</th>
      <td>Chuck</td>
      <td>3826.65</td>
    </tr>
    <tr>
      <th>3</th>
      <td>All</td>
      <td>10411.62</td>
    </tr>
  </tbody>
</table>
</div>



Pandas also provides a convenient `rolling()` function for applying tranformations on moving windows.

In this case let's get the cumulative spending per 7 days per person.

Notice that the value will stay the same on days when the person made `$0.00` of purchases, since `x + 0 = x`!


```python
rolling_df = pivot_df.rolling(7, min_periods=1).sum()
rolling_df.iloc[:8]
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
      <th>purchased_by</th>
      <th>Alice</th>
      <th>Bob</th>
      <th>Chuck</th>
      <th>All</th>
    </tr>
    <tr>
      <th>purchased_date</th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>2020-01-01</th>
      <td>0.0</td>
      <td>0.0</td>
      <td>1566.0</td>
      <td>1566.0</td>
    </tr>
    <tr>
      <th>2020-01-02</th>
      <td>0.0</td>
      <td>0.0</td>
      <td>1566.0</td>
      <td>1566.0</td>
    </tr>
    <tr>
      <th>2020-01-03</th>
      <td>0.0</td>
      <td>0.0</td>
      <td>1566.0</td>
      <td>1566.0</td>
    </tr>
    <tr>
      <th>2020-01-04</th>
      <td>0.0</td>
      <td>0.0</td>
      <td>1566.0</td>
      <td>1566.0</td>
    </tr>
    <tr>
      <th>2020-01-05</th>
      <td>0.0</td>
      <td>0.0</td>
      <td>1566.0</td>
      <td>1566.0</td>
    </tr>
    <tr>
      <th>2020-01-06</th>
      <td>0.0</td>
      <td>0.0</td>
      <td>1566.0</td>
      <td>1566.0</td>
    </tr>
    <tr>
      <th>2020-01-07</th>
      <td>0.0</td>
      <td>0.0</td>
      <td>1566.0</td>
      <td>1566.0</td>
    </tr>
    <tr>
      <th>2020-01-08</th>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
    </tr>
  </tbody>
</table>
</div>



We don't have to sum the rolling values though.
Here we grab the biggest purchase each person made over each 30 day window.

Notice that a given value will stick around for up to 30 days, but will get replaced if a bigger purchase occurs!


```python
maxes_df = pivot_df.rolling(30, min_periods=1).max()
maxes_df.iloc[:31]
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
      <th>purchased_by</th>
      <th>Alice</th>
      <th>Bob</th>
      <th>Chuck</th>
      <th>All</th>
    </tr>
    <tr>
      <th>purchased_date</th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>2020-01-01</th>
      <td>0.0</td>
      <td>0.0</td>
      <td>1566.0</td>
      <td>1566.0</td>
    </tr>
    <tr>
      <th>2020-01-02</th>
      <td>0.0</td>
      <td>0.0</td>
      <td>1566.0</td>
      <td>1566.0</td>
    </tr>
    <tr>
      <th>2020-01-03</th>
      <td>0.0</td>
      <td>0.0</td>
      <td>1566.0</td>
      <td>1566.0</td>
    </tr>
    <tr>
      <th>2020-01-04</th>
      <td>0.0</td>
      <td>0.0</td>
      <td>1566.0</td>
      <td>1566.0</td>
    </tr>
    <tr>
      <th>2020-01-05</th>
      <td>0.0</td>
      <td>0.0</td>
      <td>1566.0</td>
      <td>1566.0</td>
    </tr>
    <tr>
      <th>2020-01-06</th>
      <td>0.0</td>
      <td>0.0</td>
      <td>1566.0</td>
      <td>1566.0</td>
    </tr>
    <tr>
      <th>2020-01-07</th>
      <td>0.0</td>
      <td>0.0</td>
      <td>1566.0</td>
      <td>1566.0</td>
    </tr>
    <tr>
      <th>2020-01-08</th>
      <td>0.0</td>
      <td>0.0</td>
      <td>1566.0</td>
      <td>1566.0</td>
    </tr>
    <tr>
      <th>2020-01-09</th>
      <td>0.0</td>
      <td>0.0</td>
      <td>1566.0</td>
      <td>1566.0</td>
    </tr>
    <tr>
      <th>2020-01-10</th>
      <td>0.0</td>
      <td>0.0</td>
      <td>1566.0</td>
      <td>1566.0</td>
    </tr>
    <tr>
      <th>2020-01-11</th>
      <td>0.0</td>
      <td>0.0</td>
      <td>1566.0</td>
      <td>1566.0</td>
    </tr>
    <tr>
      <th>2020-01-12</th>
      <td>0.0</td>
      <td>0.0</td>
      <td>1566.0</td>
      <td>1566.0</td>
    </tr>
    <tr>
      <th>2020-01-13</th>
      <td>0.0</td>
      <td>0.0</td>
      <td>1566.0</td>
      <td>1566.0</td>
    </tr>
    <tr>
      <th>2020-01-14</th>
      <td>0.0</td>
      <td>0.0</td>
      <td>1566.0</td>
      <td>1566.0</td>
    </tr>
    <tr>
      <th>2020-01-15</th>
      <td>0.0</td>
      <td>0.0</td>
      <td>1566.0</td>
      <td>1566.0</td>
    </tr>
    <tr>
      <th>2020-01-16</th>
      <td>0.0</td>
      <td>0.0</td>
      <td>1566.0</td>
      <td>1566.0</td>
    </tr>
    <tr>
      <th>2020-01-17</th>
      <td>0.0</td>
      <td>0.0</td>
      <td>1566.0</td>
      <td>1566.0</td>
    </tr>
    <tr>
      <th>2020-01-18</th>
      <td>0.0</td>
      <td>0.0</td>
      <td>1566.0</td>
      <td>1566.0</td>
    </tr>
    <tr>
      <th>2020-01-19</th>
      <td>0.0</td>
      <td>0.0</td>
      <td>1566.0</td>
      <td>1566.0</td>
    </tr>
    <tr>
      <th>2020-01-20</th>
      <td>0.0</td>
      <td>7072.0</td>
      <td>1566.0</td>
      <td>7072.0</td>
    </tr>
    <tr>
      <th>2020-01-21</th>
      <td>0.0</td>
      <td>7072.0</td>
      <td>1566.0</td>
      <td>7072.0</td>
    </tr>
    <tr>
      <th>2020-01-22</th>
      <td>0.0</td>
      <td>7072.0</td>
      <td>1566.0</td>
      <td>7072.0</td>
    </tr>
    <tr>
      <th>2020-01-23</th>
      <td>0.0</td>
      <td>7072.0</td>
      <td>1566.0</td>
      <td>7072.0</td>
    </tr>
    <tr>
      <th>2020-01-24</th>
      <td>0.0</td>
      <td>7072.0</td>
      <td>1566.0</td>
      <td>7072.0</td>
    </tr>
    <tr>
      <th>2020-01-25</th>
      <td>0.0</td>
      <td>7072.0</td>
      <td>1566.0</td>
      <td>7072.0</td>
    </tr>
    <tr>
      <th>2020-01-26</th>
      <td>0.0</td>
      <td>7072.0</td>
      <td>9982.0</td>
      <td>9982.0</td>
    </tr>
    <tr>
      <th>2020-01-27</th>
      <td>0.0</td>
      <td>7072.0</td>
      <td>9982.0</td>
      <td>9982.0</td>
    </tr>
    <tr>
      <th>2020-01-28</th>
      <td>0.0</td>
      <td>7072.0</td>
      <td>9982.0</td>
      <td>9982.0</td>
    </tr>
    <tr>
      <th>2020-01-29</th>
      <td>0.0</td>
      <td>7072.0</td>
      <td>9982.0</td>
      <td>9982.0</td>
    </tr>
    <tr>
      <th>2020-01-30</th>
      <td>0.0</td>
      <td>7072.0</td>
      <td>9982.0</td>
      <td>9982.0</td>
    </tr>
    <tr>
      <th>2020-01-31</th>
      <td>0.0</td>
      <td>7072.0</td>
      <td>9982.0</td>
      <td>9982.0</td>
    </tr>
  </tbody>
</table>
</div>



## Now Make it Pretty

Since we did most of the work in pandas already to shape the data, the Data Analysis of it should be more straightforward

We'll use a helper function to do one final transformation that applies to almost all our datasets


```python
def prep_df_for_display(df: pd.DataFrame) -> pd.DataFrame:
    return df.divide(100).reset_index().melt("purchased_date")

prepped_cumulative = prep_df_for_display(cumulative)
prepped_cumulative
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
      <th>purchased_date</th>
      <th>purchased_by</th>
      <th>value</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>2020-01-01</td>
      <td>Alice</td>
      <td>0.00</td>
    </tr>
    <tr>
      <th>1</th>
      <td>2020-01-02</td>
      <td>Alice</td>
      <td>0.00</td>
    </tr>
    <tr>
      <th>2</th>
      <td>2020-01-03</td>
      <td>Alice</td>
      <td>0.00</td>
    </tr>
    <tr>
      <th>3</th>
      <td>2020-01-04</td>
      <td>Alice</td>
      <td>0.00</td>
    </tr>
    <tr>
      <th>4</th>
      <td>2020-01-05</td>
      <td>Alice</td>
      <td>0.00</td>
    </tr>
    <tr>
      <th>...</th>
      <td>...</td>
      <td>...</td>
      <td>...</td>
    </tr>
    <tr>
      <th>4307</th>
      <td>2022-12-09</td>
      <td>All</td>
      <td>10152.88</td>
    </tr>
    <tr>
      <th>4308</th>
      <td>2022-12-10</td>
      <td>All</td>
      <td>10215.75</td>
    </tr>
    <tr>
      <th>4309</th>
      <td>2022-12-11</td>
      <td>All</td>
      <td>10215.75</td>
    </tr>
    <tr>
      <th>4310</th>
      <td>2022-12-12</td>
      <td>All</td>
      <td>10315.00</td>
    </tr>
    <tr>
      <th>4311</th>
      <td>2022-12-13</td>
      <td>All</td>
      <td>10411.62</td>
    </tr>
  </tbody>
</table>
<p>4312 rows × 3 columns</p>
</div>



Seems like it's undoing a lot of work we've already done, but this Long Format is generally easier for plotting software to work with.

In this case we keep `purchased_date` as a column (not index), get a value column called `value`, and a column we can use for trend highlighting which is `purchased_by`

After that, plotly express provides the easiest (but not most performant) visualizations in my experience


```python
import plotly.express as px
from IPython.display import HTML
line_chart = px.line(
    prepped_cumulative,
    x="purchased_date",
    y="value",
    color="purchased_by",
    labels={"value": "Cumulative Dollars Spent"},
)
line_chart.show()
```






<html>
<head><meta charset="utf-8" /></head>
<body>
    <div>                        <script type="text/javascript">window.PlotlyConfig = {MathJaxConfig: 'local'};</script>
        <script src="https://cdn.plot.ly/plotly-2.9.0.min.js"></script>                <div id="e376a278-d7dd-4793-9402-b260d670f2dd" class="plotly-graph-div" style="height:100%; width:100%;"></div>            <script type="text/javascript">                                    window.PLOTLYENV=window.PLOTLYENV || {};                                    if (document.getElementById("e376a278-d7dd-4793-9402-b260d670f2dd")) {                    Plotly.newPlot(                        "e376a278-d7dd-4793-9402-b260d670f2dd",                        [{"hovertemplate":"purchased_by=Alice<br>purchased_date=%{x}<br>Cumulative Dollars Spent=%{y}<extra></extra>","legendgroup":"Alice","line":{"color":"#636efa","dash":"solid"},"marker":{"symbol":"circle"},"mode":"lines","name":"Alice","showlegend":true,"x":["2020-01-01T00:00:00","2020-01-02T00:00:00","2020-01-03T00:00:00","2020-01-04T00:00:00","2020-01-05T00:00:00","2020-01-06T00:00:00","2020-01-07T00:00:00","2020-01-08T00:00:00","2020-01-09T00:00:00","2020-01-10T00:00:00","2020-01-11T00:00:00","2020-01-12T00:00:00","2020-01-13T00:00:00","2020-01-14T00:00:00","2020-01-15T00:00:00","2020-01-16T00:00:00","2020-01-17T00:00:00","2020-01-18T00:00:00","2020-01-19T00:00:00","2020-01-20T00:00:00","2020-01-21T00:00:00","2020-01-22T00:00:00","2020-01-23T00:00:00","2020-01-24T00:00:00","2020-01-25T00:00:00","2020-01-26T00:00:00","2020-01-27T00:00:00","2020-01-28T00:00:00","2020-01-29T00:00:00","2020-01-30T00:00:00","2020-01-31T00:00:00","2020-02-01T00:00:00","2020-02-02T00:00:00","2020-02-03T00:00:00","2020-02-04T00:00:00","2020-02-05T00:00:00","2020-02-06T00:00:00","2020-02-07T00:00:00","2020-02-08T00:00:00","2020-02-09T00:00:00","2020-02-10T00:00:00","2020-02-11T00:00:00","2020-02-12T00:00:00","2020-02-13T00:00:00","2020-02-14T00:00:00","2020-02-15T00:00:00","2020-02-16T00:00:00","2020-02-17T00:00:00","2020-02-18T00:00:00","2020-02-19T00:00:00","2020-02-20T00:00:00","2020-02-21T00:00:00","2020-02-22T00:00:00","2020-02-23T00:00:00","2020-02-24T00:00:00","2020-02-25T00:00:00","2020-02-26T00:00:00","2020-02-27T00:00:00","2020-02-28T00:00:00","2020-02-29T00:00:00","2020-03-01T00:00:00","2020-03-02T00:00:00","2020-03-03T00:00:00","2020-03-04T00:00:00","2020-03-05T00:00:00","2020-03-06T00:00:00","2020-03-07T00:00:00","2020-03-08T00:00:00","2020-03-09T00:00:00","2020-03-10T00:00:00","2020-03-11T00:00:00","2020-03-12T00:00:00","2020-03-13T00:00:00","2020-03-14T00:00:00","2020-03-15T00:00:00","2020-03-16T00:00:00","2020-03-17T00:00:00","2020-03-18T00:00:00","2020-03-19T00:00:00","2020-03-20T00:00:00","2020-03-21T00:00:00","2020-03-22T00:00:00","2020-03-23T00:00:00","2020-03-24T00:00:00","2020-03-25T00:00:00","2020-03-26T00:00:00","2020-03-27T00:00:00","2020-03-28T00:00:00","2020-03-29T00:00:00","2020-03-30T00:00:00","2020-03-31T00:00:00","2020-04-01T00:00:00","2020-04-02T00:00:00","2020-04-03T00:00:00","2020-04-04T00:00:00","2020-04-05T00:00:00","2020-04-06T00:00:00","2020-04-07T00:00:00","2020-04-08T00:00:00","2020-04-09T00:00:00","2020-04-10T00:00:00","2020-04-11T00:00:00","2020-04-12T00:00:00","2020-04-13T00:00:00","2020-04-14T00:00:00","2020-04-15T00:00:00","2020-04-16T00:00:00","2020-04-17T00:00:00","2020-04-18T00:00:00","2020-04-19T00:00:00","2020-04-20T00:00:00","2020-04-21T00:00:00","2020-04-22T00:00:00","2020-04-23T00:00:00","2020-04-24T00:00:00","2020-04-25T00:00:00","2020-04-26T00:00:00","2020-04-27T00:00:00","2020-04-28T00:00:00","2020-04-29T00:00:00","2020-04-30T00:00:00","2020-05-01T00:00:00","2020-05-02T00:00:00","2020-05-03T00:00:00","2020-05-04T00:00:00","2020-05-05T00:00:00","2020-05-06T00:00:00","2020-05-07T00:00:00","2020-05-08T00:00:00","2020-05-09T00:00:00","2020-05-10T00:00:00","2020-05-11T00:00:00","2020-05-12T00:00:00","2020-05-13T00:00:00","2020-05-14T00:00:00","2020-05-15T00:00:00","2020-05-16T00:00:00","2020-05-17T00:00:00","2020-05-18T00:00:00","2020-05-19T00:00:00","2020-05-20T00:00:00","2020-05-21T00:00:00","2020-05-22T00:00:00","2020-05-23T00:00:00","2020-05-24T00:00:00","2020-05-25T00:00:00","2020-05-26T00:00:00","2020-05-27T00:00:00","2020-05-28T00:00:00","2020-05-29T00:00:00","2020-05-30T00:00:00","2020-05-31T00:00:00","2020-06-01T00:00:00","2020-06-02T00:00:00","2020-06-03T00:00:00","2020-06-04T00:00:00","2020-06-05T00:00:00","2020-06-06T00:00:00","2020-06-07T00:00:00","2020-06-08T00:00:00","2020-06-09T00:00:00","2020-06-10T00:00:00","2020-06-11T00:00:00","2020-06-12T00:00:00","2020-06-13T00:00:00","2020-06-14T00:00:00","2020-06-15T00:00:00","2020-06-16T00:00:00","2020-06-17T00:00:00","2020-06-18T00:00:00","2020-06-19T00:00:00","2020-06-20T00:00:00","2020-06-21T00:00:00","2020-06-22T00:00:00","2020-06-23T00:00:00","2020-06-24T00:00:00","2020-06-25T00:00:00","2020-06-26T00:00:00","2020-06-27T00:00:00","2020-06-28T00:00:00","2020-06-29T00:00:00","2020-06-30T00:00:00","2020-07-01T00:00:00","2020-07-02T00:00:00","2020-07-03T00:00:00","2020-07-04T00:00:00","2020-07-05T00:00:00","2020-07-06T00:00:00","2020-07-07T00:00:00","2020-07-08T00:00:00","2020-07-09T00:00:00","2020-07-10T00:00:00","2020-07-11T00:00:00","2020-07-12T00:00:00","2020-07-13T00:00:00","2020-07-14T00:00:00","2020-07-15T00:00:00","2020-07-16T00:00:00","2020-07-17T00:00:00","2020-07-18T00:00:00","2020-07-19T00:00:00","2020-07-20T00:00:00","2020-07-21T00:00:00","2020-07-22T00:00:00","2020-07-23T00:00:00","2020-07-24T00:00:00","2020-07-25T00:00:00","2020-07-26T00:00:00","2020-07-27T00:00:00","2020-07-28T00:00:00","2020-07-29T00:00:00","2020-07-30T00:00:00","2020-07-31T00:00:00","2020-08-01T00:00:00","2020-08-02T00:00:00","2020-08-03T00:00:00","2020-08-04T00:00:00","2020-08-05T00:00:00","2020-08-06T00:00:00","2020-08-07T00:00:00","2020-08-08T00:00:00","2020-08-09T00:00:00","2020-08-10T00:00:00","2020-08-11T00:00:00","2020-08-12T00:00:00","2020-08-13T00:00:00","2020-08-14T00:00:00","2020-08-15T00:00:00","2020-08-16T00:00:00","2020-08-17T00:00:00","2020-08-18T00:00:00","2020-08-19T00:00:00","2020-08-20T00:00:00","2020-08-21T00:00:00","2020-08-22T00:00:00","2020-08-23T00:00:00","2020-08-24T00:00:00","2020-08-25T00:00:00","2020-08-26T00:00:00","2020-08-27T00:00:00","2020-08-28T00:00:00","2020-08-29T00:00:00","2020-08-30T00:00:00","2020-08-31T00:00:00","2020-09-01T00:00:00","2020-09-02T00:00:00","2020-09-03T00:00:00","2020-09-04T00:00:00","2020-09-05T00:00:00","2020-09-06T00:00:00","2020-09-07T00:00:00","2020-09-08T00:00:00","2020-09-09T00:00:00","2020-09-10T00:00:00","2020-09-11T00:00:00","2020-09-12T00:00:00","2020-09-13T00:00:00","2020-09-14T00:00:00","2020-09-15T00:00:00","2020-09-16T00:00:00","2020-09-17T00:00:00","2020-09-18T00:00:00","2020-09-19T00:00:00","2020-09-20T00:00:00","2020-09-21T00:00:00","2020-09-22T00:00:00","2020-09-23T00:00:00","2020-09-24T00:00:00","2020-09-25T00:00:00","2020-09-26T00:00:00","2020-09-27T00:00:00","2020-09-28T00:00:00","2020-09-29T00:00:00","2020-09-30T00:00:00","2020-10-01T00:00:00","2020-10-02T00:00:00","2020-10-03T00:00:00","2020-10-04T00:00:00","2020-10-05T00:00:00","2020-10-06T00:00:00","2020-10-07T00:00:00","2020-10-08T00:00:00","2020-10-09T00:00:00","2020-10-10T00:00:00","2020-10-11T00:00:00","2020-10-12T00:00:00","2020-10-13T00:00:00","2020-10-14T00:00:00","2020-10-15T00:00:00","2020-10-16T00:00:00","2020-10-17T00:00:00","2020-10-18T00:00:00","2020-10-19T00:00:00","2020-10-20T00:00:00","2020-10-21T00:00:00","2020-10-22T00:00:00","2020-10-23T00:00:00","2020-10-24T00:00:00","2020-10-25T00:00:00","2020-10-26T00:00:00","2020-10-27T00:00:00","2020-10-28T00:00:00","2020-10-29T00:00:00","2020-10-30T00:00:00","2020-10-31T00:00:00","2020-11-01T00:00:00","2020-11-02T00:00:00","2020-11-03T00:00:00","2020-11-04T00:00:00","2020-11-05T00:00:00","2020-11-06T00:00:00","2020-11-07T00:00:00","2020-11-08T00:00:00","2020-11-09T00:00:00","2020-11-10T00:00:00","2020-11-11T00:00:00","2020-11-12T00:00:00","2020-11-13T00:00:00","2020-11-14T00:00:00","2020-11-15T00:00:00","2020-11-16T00:00:00","2020-11-17T00:00:00","2020-11-18T00:00:00","2020-11-19T00:00:00","2020-11-20T00:00:00","2020-11-21T00:00:00","2020-11-22T00:00:00","2020-11-23T00:00:00","2020-11-24T00:00:00","2020-11-25T00:00:00","2020-11-26T00:00:00","2020-11-27T00:00:00","2020-11-28T00:00:00","2020-11-29T00:00:00","2020-11-30T00:00:00","2020-12-01T00:00:00","2020-12-02T00:00:00","2020-12-03T00:00:00","2020-12-04T00:00:00","2020-12-05T00:00:00","2020-12-06T00:00:00","2020-12-07T00:00:00","2020-12-08T00:00:00","2020-12-09T00:00:00","2020-12-10T00:00:00","2020-12-11T00:00:00","2020-12-12T00:00:00","2020-12-13T00:00:00","2020-12-14T00:00:00","2020-12-15T00:00:00","2020-12-16T00:00:00","2020-12-17T00:00:00","2020-12-18T00:00:00","2020-12-19T00:00:00","2020-12-20T00:00:00","2020-12-21T00:00:00","2020-12-22T00:00:00","2020-12-23T00:00:00","2020-12-24T00:00:00","2020-12-25T00:00:00","2020-12-26T00:00:00","2020-12-27T00:00:00","2020-12-28T00:00:00","2020-12-29T00:00:00","2020-12-30T00:00:00","2020-12-31T00:00:00","2021-01-01T00:00:00","2021-01-02T00:00:00","2021-01-03T00:00:00","2021-01-04T00:00:00","2021-01-05T00:00:00","2021-01-06T00:00:00","2021-01-07T00:00:00","2021-01-08T00:00:00","2021-01-09T00:00:00","2021-01-10T00:00:00","2021-01-11T00:00:00","2021-01-12T00:00:00","2021-01-13T00:00:00","2021-01-14T00:00:00","2021-01-15T00:00:00","2021-01-16T00:00:00","2021-01-17T00:00:00","2021-01-18T00:00:00","2021-01-19T00:00:00","2021-01-20T00:00:00","2021-01-21T00:00:00","2021-01-22T00:00:00","2021-01-23T00:00:00","2021-01-24T00:00:00","2021-01-25T00:00:00","2021-01-26T00:00:00","2021-01-27T00:00:00","2021-01-28T00:00:00","2021-01-29T00:00:00","2021-01-30T00:00:00","2021-01-31T00:00:00","2021-02-01T00:00:00","2021-02-02T00:00:00","2021-02-03T00:00:00","2021-02-04T00:00:00","2021-02-05T00:00:00","2021-02-06T00:00:00","2021-02-07T00:00:00","2021-02-08T00:00:00","2021-02-09T00:00:00","2021-02-10T00:00:00","2021-02-11T00:00:00","2021-02-12T00:00:00","2021-02-13T00:00:00","2021-02-14T00:00:00","2021-02-15T00:00:00","2021-02-16T00:00:00","2021-02-17T00:00:00","2021-02-18T00:00:00","2021-02-19T00:00:00","2021-02-20T00:00:00","2021-02-21T00:00:00","2021-02-22T00:00:00","2021-02-23T00:00:00","2021-02-24T00:00:00","2021-02-25T00:00:00","2021-02-26T00:00:00","2021-02-27T00:00:00","2021-02-28T00:00:00","2021-03-01T00:00:00","2021-03-02T00:00:00","2021-03-03T00:00:00","2021-03-04T00:00:00","2021-03-05T00:00:00","2021-03-06T00:00:00","2021-03-07T00:00:00","2021-03-08T00:00:00","2021-03-09T00:00:00","2021-03-10T00:00:00","2021-03-11T00:00:00","2021-03-12T00:00:00","2021-03-13T00:00:00","2021-03-14T00:00:00","2021-03-15T00:00:00","2021-03-16T00:00:00","2021-03-17T00:00:00","2021-03-18T00:00:00","2021-03-19T00:00:00","2021-03-20T00:00:00","2021-03-21T00:00:00","2021-03-22T00:00:00","2021-03-23T00:00:00","2021-03-24T00:00:00","2021-03-25T00:00:00","2021-03-26T00:00:00","2021-03-27T00:00:00","2021-03-28T00:00:00","2021-03-29T00:00:00","2021-03-30T00:00:00","2021-03-31T00:00:00","2021-04-01T00:00:00","2021-04-02T00:00:00","2021-04-03T00:00:00","2021-04-04T00:00:00","2021-04-05T00:00:00","2021-04-06T00:00:00","2021-04-07T00:00:00","2021-04-08T00:00:00","2021-04-09T00:00:00","2021-04-10T00:00:00","2021-04-11T00:00:00","2021-04-12T00:00:00","2021-04-13T00:00:00","2021-04-14T00:00:00","2021-04-15T00:00:00","2021-04-16T00:00:00","2021-04-17T00:00:00","2021-04-18T00:00:00","2021-04-19T00:00:00","2021-04-20T00:00:00","2021-04-21T00:00:00","2021-04-22T00:00:00","2021-04-23T00:00:00","2021-04-24T00:00:00","2021-04-25T00:00:00","2021-04-26T00:00:00","2021-04-27T00:00:00","2021-04-28T00:00:00","2021-04-29T00:00:00","2021-04-30T00:00:00","2021-05-01T00:00:00","2021-05-02T00:00:00","2021-05-03T00:00:00","2021-05-04T00:00:00","2021-05-05T00:00:00","2021-05-06T00:00:00","2021-05-07T00:00:00","2021-05-08T00:00:00","2021-05-09T00:00:00","2021-05-10T00:00:00","2021-05-11T00:00:00","2021-05-12T00:00:00","2021-05-13T00:00:00","2021-05-14T00:00:00","2021-05-15T00:00:00","2021-05-16T00:00:00","2021-05-17T00:00:00","2021-05-18T00:00:00","2021-05-19T00:00:00","2021-05-20T00:00:00","2021-05-21T00:00:00","2021-05-22T00:00:00","2021-05-23T00:00:00","2021-05-24T00:00:00","2021-05-25T00:00:00","2021-05-26T00:00:00","2021-05-27T00:00:00","2021-05-28T00:00:00","2021-05-29T00:00:00","2021-05-30T00:00:00","2021-05-31T00:00:00","2021-06-01T00:00:00","2021-06-02T00:00:00","2021-06-03T00:00:00","2021-06-04T00:00:00","2021-06-05T00:00:00","2021-06-06T00:00:00","2021-06-07T00:00:00","2021-06-08T00:00:00","2021-06-09T00:00:00","2021-06-10T00:00:00","2021-06-11T00:00:00","2021-06-12T00:00:00","2021-06-13T00:00:00","2021-06-14T00:00:00","2021-06-15T00:00:00","2021-06-16T00:00:00","2021-06-17T00:00:00","2021-06-18T00:00:00","2021-06-19T00:00:00","2021-06-20T00:00:00","2021-06-21T00:00:00","2021-06-22T00:00:00","2021-06-23T00:00:00","2021-06-24T00:00:00","2021-06-25T00:00:00","2021-06-26T00:00:00","2021-06-27T00:00:00","2021-06-28T00:00:00","2021-06-29T00:00:00","2021-06-30T00:00:00","2021-07-01T00:00:00","2021-07-02T00:00:00","2021-07-03T00:00:00","2021-07-04T00:00:00","2021-07-05T00:00:00","2021-07-06T00:00:00","2021-07-07T00:00:00","2021-07-08T00:00:00","2021-07-09T00:00:00","2021-07-10T00:00:00","2021-07-11T00:00:00","2021-07-12T00:00:00","2021-07-13T00:00:00","2021-07-14T00:00:00","2021-07-15T00:00:00","2021-07-16T00:00:00","2021-07-17T00:00:00","2021-07-18T00:00:00","2021-07-19T00:00:00","2021-07-20T00:00:00","2021-07-21T00:00:00","2021-07-22T00:00:00","2021-07-23T00:00:00","2021-07-24T00:00:00","2021-07-25T00:00:00","2021-07-26T00:00:00","2021-07-27T00:00:00","2021-07-28T00:00:00","2021-07-29T00:00:00","2021-07-30T00:00:00","2021-07-31T00:00:00","2021-08-01T00:00:00","2021-08-02T00:00:00","2021-08-03T00:00:00","2021-08-04T00:00:00","2021-08-05T00:00:00","2021-08-06T00:00:00","2021-08-07T00:00:00","2021-08-08T00:00:00","2021-08-09T00:00:00","2021-08-10T00:00:00","2021-08-11T00:00:00","2021-08-12T00:00:00","2021-08-13T00:00:00","2021-08-14T00:00:00","2021-08-15T00:00:00","2021-08-16T00:00:00","2021-08-17T00:00:00","2021-08-18T00:00:00","2021-08-19T00:00:00","2021-08-20T00:00:00","2021-08-21T00:00:00","2021-08-22T00:00:00","2021-08-23T00:00:00","2021-08-24T00:00:00","2021-08-25T00:00:00","2021-08-26T00:00:00","2021-08-27T00:00:00","2021-08-28T00:00:00","2021-08-29T00:00:00","2021-08-30T00:00:00","2021-08-31T00:00:00","2021-09-01T00:00:00","2021-09-02T00:00:00","2021-09-03T00:00:00","2021-09-04T00:00:00","2021-09-05T00:00:00","2021-09-06T00:00:00","2021-09-07T00:00:00","2021-09-08T00:00:00","2021-09-09T00:00:00","2021-09-10T00:00:00","2021-09-11T00:00:00","2021-09-12T00:00:00","2021-09-13T00:00:00","2021-09-14T00:00:00","2021-09-15T00:00:00","2021-09-16T00:00:00","2021-09-17T00:00:00","2021-09-18T00:00:00","2021-09-19T00:00:00","2021-09-20T00:00:00","2021-09-21T00:00:00","2021-09-22T00:00:00","2021-09-23T00:00:00","2021-09-24T00:00:00","2021-09-25T00:00:00","2021-09-26T00:00:00","2021-09-27T00:00:00","2021-09-28T00:00:00","2021-09-29T00:00:00","2021-09-30T00:00:00","2021-10-01T00:00:00","2021-10-02T00:00:00","2021-10-03T00:00:00","2021-10-04T00:00:00","2021-10-05T00:00:00","2021-10-06T00:00:00","2021-10-07T00:00:00","2021-10-08T00:00:00","2021-10-09T00:00:00","2021-10-10T00:00:00","2021-10-11T00:00:00","2021-10-12T00:00:00","2021-10-13T00:00:00","2021-10-14T00:00:00","2021-10-15T00:00:00","2021-10-16T00:00:00","2021-10-17T00:00:00","2021-10-18T00:00:00","2021-10-19T00:00:00","2021-10-20T00:00:00","2021-10-21T00:00:00","2021-10-22T00:00:00","2021-10-23T00:00:00","2021-10-24T00:00:00","2021-10-25T00:00:00","2021-10-26T00:00:00","2021-10-27T00:00:00","2021-10-28T00:00:00","2021-10-29T00:00:00","2021-10-30T00:00:00","2021-10-31T00:00:00","2021-11-01T00:00:00","2021-11-02T00:00:00","2021-11-03T00:00:00","2021-11-04T00:00:00","2021-11-05T00:00:00","2021-11-06T00:00:00","2021-11-07T00:00:00","2021-11-08T00:00:00","2021-11-09T00:00:00","2021-11-10T00:00:00","2021-11-11T00:00:00","2021-11-12T00:00:00","2021-11-13T00:00:00","2021-11-14T00:00:00","2021-11-15T00:00:00","2021-11-16T00:00:00","2021-11-17T00:00:00","2021-11-18T00:00:00","2021-11-19T00:00:00","2021-11-20T00:00:00","2021-11-21T00:00:00","2021-11-22T00:00:00","2021-11-23T00:00:00","2021-11-24T00:00:00","2021-11-25T00:00:00","2021-11-26T00:00:00","2021-11-27T00:00:00","2021-11-28T00:00:00","2021-11-29T00:00:00","2021-11-30T00:00:00","2021-12-01T00:00:00","2021-12-02T00:00:00","2021-12-03T00:00:00","2021-12-04T00:00:00","2021-12-05T00:00:00","2021-12-06T00:00:00","2021-12-07T00:00:00","2021-12-08T00:00:00","2021-12-09T00:00:00","2021-12-10T00:00:00","2021-12-11T00:00:00","2021-12-12T00:00:00","2021-12-13T00:00:00","2021-12-14T00:00:00","2021-12-15T00:00:00","2021-12-16T00:00:00","2021-12-17T00:00:00","2021-12-18T00:00:00","2021-12-19T00:00:00","2021-12-20T00:00:00","2021-12-21T00:00:00","2021-12-22T00:00:00","2021-12-23T00:00:00","2021-12-24T00:00:00","2021-12-25T00:00:00","2021-12-26T00:00:00","2021-12-27T00:00:00","2021-12-28T00:00:00","2021-12-29T00:00:00","2021-12-30T00:00:00","2021-12-31T00:00:00","2022-01-01T00:00:00","2022-01-02T00:00:00","2022-01-03T00:00:00","2022-01-04T00:00:00","2022-01-05T00:00:00","2022-01-06T00:00:00","2022-01-07T00:00:00","2022-01-08T00:00:00","2022-01-09T00:00:00","2022-01-10T00:00:00","2022-01-11T00:00:00","2022-01-12T00:00:00","2022-01-13T00:00:00","2022-01-14T00:00:00","2022-01-15T00:00:00","2022-01-16T00:00:00","2022-01-17T00:00:00","2022-01-18T00:00:00","2022-01-19T00:00:00","2022-01-20T00:00:00","2022-01-21T00:00:00","2022-01-22T00:00:00","2022-01-23T00:00:00","2022-01-24T00:00:00","2022-01-25T00:00:00","2022-01-26T00:00:00","2022-01-27T00:00:00","2022-01-28T00:00:00","2022-01-29T00:00:00","2022-01-30T00:00:00","2022-01-31T00:00:00","2022-02-01T00:00:00","2022-02-02T00:00:00","2022-02-03T00:00:00","2022-02-04T00:00:00","2022-02-05T00:00:00","2022-02-06T00:00:00","2022-02-07T00:00:00","2022-02-08T00:00:00","2022-02-09T00:00:00","2022-02-10T00:00:00","2022-02-11T00:00:00","2022-02-12T00:00:00","2022-02-13T00:00:00","2022-02-14T00:00:00","2022-02-15T00:00:00","2022-02-16T00:00:00","2022-02-17T00:00:00","2022-02-18T00:00:00","2022-02-19T00:00:00","2022-02-20T00:00:00","2022-02-21T00:00:00","2022-02-22T00:00:00","2022-02-23T00:00:00","2022-02-24T00:00:00","2022-02-25T00:00:00","2022-02-26T00:00:00","2022-02-27T00:00:00","2022-02-28T00:00:00","2022-03-01T00:00:00","2022-03-02T00:00:00","2022-03-03T00:00:00","2022-03-04T00:00:00","2022-03-05T00:00:00","2022-03-06T00:00:00","2022-03-07T00:00:00","2022-03-08T00:00:00","2022-03-09T00:00:00","2022-03-10T00:00:00","2022-03-11T00:00:00","2022-03-12T00:00:00","2022-03-13T00:00:00","2022-03-14T00:00:00","2022-03-15T00:00:00","2022-03-16T00:00:00","2022-03-17T00:00:00","2022-03-18T00:00:00","2022-03-19T00:00:00","2022-03-20T00:00:00","2022-03-21T00:00:00","2022-03-22T00:00:00","2022-03-23T00:00:00","2022-03-24T00:00:00","2022-03-25T00:00:00","2022-03-26T00:00:00","2022-03-27T00:00:00","2022-03-28T00:00:00","2022-03-29T00:00:00","2022-03-30T00:00:00","2022-03-31T00:00:00","2022-04-01T00:00:00","2022-04-02T00:00:00","2022-04-03T00:00:00","2022-04-04T00:00:00","2022-04-05T00:00:00","2022-04-06T00:00:00","2022-04-07T00:00:00","2022-04-08T00:00:00","2022-04-09T00:00:00","2022-04-10T00:00:00","2022-04-11T00:00:00","2022-04-12T00:00:00","2022-04-13T00:00:00","2022-04-14T00:00:00","2022-04-15T00:00:00","2022-04-16T00:00:00","2022-04-17T00:00:00","2022-04-18T00:00:00","2022-04-19T00:00:00","2022-04-20T00:00:00","2022-04-21T00:00:00","2022-04-22T00:00:00","2022-04-23T00:00:00","2022-04-24T00:00:00","2022-04-25T00:00:00","2022-04-26T00:00:00","2022-04-27T00:00:00","2022-04-28T00:00:00","2022-04-29T00:00:00","2022-04-30T00:00:00","2022-05-01T00:00:00","2022-05-02T00:00:00","2022-05-03T00:00:00","2022-05-04T00:00:00","2022-05-05T00:00:00","2022-05-06T00:00:00","2022-05-07T00:00:00","2022-05-08T00:00:00","2022-05-09T00:00:00","2022-05-10T00:00:00","2022-05-11T00:00:00","2022-05-12T00:00:00","2022-05-13T00:00:00","2022-05-14T00:00:00","2022-05-15T00:00:00","2022-05-16T00:00:00","2022-05-17T00:00:00","2022-05-18T00:00:00","2022-05-19T00:00:00","2022-05-20T00:00:00","2022-05-21T00:00:00","2022-05-22T00:00:00","2022-05-23T00:00:00","2022-05-24T00:00:00","2022-05-25T00:00:00","2022-05-26T00:00:00","2022-05-27T00:00:00","2022-05-28T00:00:00","2022-05-29T00:00:00","2022-05-30T00:00:00","2022-05-31T00:00:00","2022-06-01T00:00:00","2022-06-02T00:00:00","2022-06-03T00:00:00","2022-06-04T00:00:00","2022-06-05T00:00:00","2022-06-06T00:00:00","2022-06-07T00:00:00","2022-06-08T00:00:00","2022-06-09T00:00:00","2022-06-10T00:00:00","2022-06-11T00:00:00","2022-06-12T00:00:00","2022-06-13T00:00:00","2022-06-14T00:00:00","2022-06-15T00:00:00","2022-06-16T00:00:00","2022-06-17T00:00:00","2022-06-18T00:00:00","2022-06-19T00:00:00","2022-06-20T00:00:00","2022-06-21T00:00:00","2022-06-22T00:00:00","2022-06-23T00:00:00","2022-06-24T00:00:00","2022-06-25T00:00:00","2022-06-26T00:00:00","2022-06-27T00:00:00","2022-06-28T00:00:00","2022-06-29T00:00:00","2022-06-30T00:00:00","2022-07-01T00:00:00","2022-07-02T00:00:00","2022-07-03T00:00:00","2022-07-04T00:00:00","2022-07-05T00:00:00","2022-07-06T00:00:00","2022-07-07T00:00:00","2022-07-08T00:00:00","2022-07-09T00:00:00","2022-07-10T00:00:00","2022-07-11T00:00:00","2022-07-12T00:00:00","2022-07-13T00:00:00","2022-07-14T00:00:00","2022-07-15T00:00:00","2022-07-16T00:00:00","2022-07-17T00:00:00","2022-07-18T00:00:00","2022-07-19T00:00:00","2022-07-20T00:00:00","2022-07-21T00:00:00","2022-07-22T00:00:00","2022-07-23T00:00:00","2022-07-24T00:00:00","2022-07-25T00:00:00","2022-07-26T00:00:00","2022-07-27T00:00:00","2022-07-28T00:00:00","2022-07-29T00:00:00","2022-07-30T00:00:00","2022-07-31T00:00:00","2022-08-01T00:00:00","2022-08-02T00:00:00","2022-08-03T00:00:00","2022-08-04T00:00:00","2022-08-05T00:00:00","2022-08-06T00:00:00","2022-08-07T00:00:00","2022-08-08T00:00:00","2022-08-09T00:00:00","2022-08-10T00:00:00","2022-08-11T00:00:00","2022-08-12T00:00:00","2022-08-13T00:00:00","2022-08-14T00:00:00","2022-08-15T00:00:00","2022-08-16T00:00:00","2022-08-17T00:00:00","2022-08-18T00:00:00","2022-08-19T00:00:00","2022-08-20T00:00:00","2022-08-21T00:00:00","2022-08-22T00:00:00","2022-08-23T00:00:00","2022-08-24T00:00:00","2022-08-25T00:00:00","2022-08-26T00:00:00","2022-08-27T00:00:00","2022-08-28T00:00:00","2022-08-29T00:00:00","2022-08-30T00:00:00","2022-08-31T00:00:00","2022-09-01T00:00:00","2022-09-02T00:00:00","2022-09-03T00:00:00","2022-09-04T00:00:00","2022-09-05T00:00:00","2022-09-06T00:00:00","2022-09-07T00:00:00","2022-09-08T00:00:00","2022-09-09T00:00:00","2022-09-10T00:00:00","2022-09-11T00:00:00","2022-09-12T00:00:00","2022-09-13T00:00:00","2022-09-14T00:00:00","2022-09-15T00:00:00","2022-09-16T00:00:00","2022-09-17T00:00:00","2022-09-18T00:00:00","2022-09-19T00:00:00","2022-09-20T00:00:00","2022-09-21T00:00:00","2022-09-22T00:00:00","2022-09-23T00:00:00","2022-09-24T00:00:00","2022-09-25T00:00:00","2022-09-26T00:00:00","2022-09-27T00:00:00","2022-09-28T00:00:00","2022-09-29T00:00:00","2022-09-30T00:00:00","2022-10-01T00:00:00","2022-10-02T00:00:00","2022-10-03T00:00:00","2022-10-04T00:00:00","2022-10-05T00:00:00","2022-10-06T00:00:00","2022-10-07T00:00:00","2022-10-08T00:00:00","2022-10-09T00:00:00","2022-10-10T00:00:00","2022-10-11T00:00:00","2022-10-12T00:00:00","2022-10-13T00:00:00","2022-10-14T00:00:00","2022-10-15T00:00:00","2022-10-16T00:00:00","2022-10-17T00:00:00","2022-10-18T00:00:00","2022-10-19T00:00:00","2022-10-20T00:00:00","2022-10-21T00:00:00","2022-10-22T00:00:00","2022-10-23T00:00:00","2022-10-24T00:00:00","2022-10-25T00:00:00","2022-10-26T00:00:00","2022-10-27T00:00:00","2022-10-28T00:00:00","2022-10-29T00:00:00","2022-10-30T00:00:00","2022-10-31T00:00:00","2022-11-01T00:00:00","2022-11-02T00:00:00","2022-11-03T00:00:00","2022-11-04T00:00:00","2022-11-05T00:00:00","2022-11-06T00:00:00","2022-11-07T00:00:00","2022-11-08T00:00:00","2022-11-09T00:00:00","2022-11-10T00:00:00","2022-11-11T00:00:00","2022-11-12T00:00:00","2022-11-13T00:00:00","2022-11-14T00:00:00","2022-11-15T00:00:00","2022-11-16T00:00:00","2022-11-17T00:00:00","2022-11-18T00:00:00","2022-11-19T00:00:00","2022-11-20T00:00:00","2022-11-21T00:00:00","2022-11-22T00:00:00","2022-11-23T00:00:00","2022-11-24T00:00:00","2022-11-25T00:00:00","2022-11-26T00:00:00","2022-11-27T00:00:00","2022-11-28T00:00:00","2022-11-29T00:00:00","2022-11-30T00:00:00","2022-12-01T00:00:00","2022-12-02T00:00:00","2022-12-03T00:00:00","2022-12-04T00:00:00","2022-12-05T00:00:00","2022-12-06T00:00:00","2022-12-07T00:00:00","2022-12-08T00:00:00","2022-12-09T00:00:00","2022-12-10T00:00:00","2022-12-11T00:00:00","2022-12-12T00:00:00","2022-12-13T00:00:00"],"xaxis":"x","y":[0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,47.4,94.24,188.25,188.25,188.25,188.25,188.25,188.25,188.25,188.25,188.25,188.25,188.25,188.25,188.25,188.25,188.25,188.25,188.25,188.25,188.25,188.25,188.25,188.25,188.25,188.25,188.25,188.25,188.25,188.25,276.87,276.87,276.87,276.87,276.87,276.87,340.81,340.81,340.81,340.81,340.81,340.81,340.81,389.67,389.67,389.67,389.67,389.67,389.67,389.67,389.67,389.67,410.52,410.52,410.52,410.52,410.52,410.52,410.52,410.52,410.52,410.52,410.52,410.52,410.52,410.52,410.52,410.52,410.52,410.52,410.52,410.52,410.52,410.52,410.52,410.52,421.9,421.9,459.06,459.06,459.06,459.06,459.06,459.06,459.06,459.06,459.06,459.06,459.06,459.06,459.06,459.06,459.06,459.06,459.06,459.06,459.06,459.06,459.06,459.06,459.06,459.06,459.06,459.06,515.62,515.62,515.62,601.66,601.66,601.66,601.66,601.66,601.66,601.66,601.66,601.66,601.66,601.66,601.66,685.54,685.54,685.54,685.54,685.54,685.54,685.54,685.54,685.54,734.79,734.79,734.79,734.79,734.79,734.79,734.79,734.79,783.6,783.6,783.6,783.6,783.6,873.96,873.96,873.96,873.96,873.96,873.96,885.99,885.99,885.99,885.99,885.99,885.99,885.99,885.99,885.99,885.99,885.99,885.99,885.99,885.99,885.99,885.99,885.99,949.12,949.12,949.12,949.12,949.12,949.12,949.12,949.12,949.12,949.12,949.12,949.12,949.12,949.12,949.12,949.12,949.12,949.12,949.12,949.12,949.12,949.12,949.12,949.12,949.12,949.12,1027.38,1027.38,1027.38,1027.38,1027.38,1027.38,1027.38,1027.38,1027.38,1027.38,1027.38,1027.38,1027.38,1027.38,1027.38,1027.38,1027.38,1027.38,1027.38,1028.98,1028.98,1072.58,1072.58,1072.58,1072.58,1072.58,1072.58,1072.58,1072.58,1072.58,1072.58,1072.58,1072.58,1072.58,1072.58,1072.58,1072.58,1072.58,1072.58,1072.58,1072.58,1072.58,1072.58,1072.58,1072.58,1072.58,1072.58,1072.58,1072.58,1072.58,1098.66,1098.66,1098.66,1098.66,1098.66,1098.66,1098.66,1098.66,1098.66,1098.66,1098.66,1098.66,1098.66,1098.66,1098.66,1098.66,1098.66,1098.66,1098.66,1098.66,1098.66,1098.66,1098.66,1098.66,1098.66,1098.66,1098.66,1098.66,1098.66,1098.66,1098.66,1098.66,1098.66,1098.66,1098.66,1098.66,1098.66,1098.66,1183.34,1183.34,1183.34,1183.34,1183.34,1183.34,1183.34,1183.34,1198.95,1198.95,1198.95,1198.95,1296.81,1296.81,1296.81,1296.81,1296.81,1296.81,1296.81,1296.81,1296.81,1302.48,1302.48,1302.48,1302.48,1302.48,1345.84,1345.84,1345.84,1345.84,1345.84,1345.84,1345.84,1345.84,1345.84,1345.84,1345.84,1345.84,1345.84,1345.84,1345.84,1345.84,1385.49,1385.49,1385.49,1385.49,1385.49,1385.49,1454.54,1454.54,1454.54,1454.54,1454.54,1454.54,1454.54,1454.54,1454.54,1454.54,1454.54,1454.54,1454.54,1454.54,1454.54,1454.54,1454.54,1488.06,1488.06,1488.06,1488.06,1488.06,1488.06,1488.06,1488.06,1488.06,1488.06,1488.06,1488.06,1488.06,1488.06,1488.06,1488.06,1488.06,1488.06,1488.06,1495.17,1495.17,1495.17,1495.17,1495.17,1495.17,1495.17,1495.17,1495.17,1495.17,1495.17,1495.17,1495.17,1559.35,1559.35,1559.35,1559.35,1559.35,1559.35,1559.35,1559.35,1559.35,1638.66,1638.66,1638.66,1638.66,1638.66,1638.66,1638.66,1638.66,1638.66,1638.66,1638.66,1638.66,1638.66,1638.66,1638.66,1638.66,1638.66,1638.66,1638.66,1638.66,1748.76,1748.76,1748.76,1748.76,1748.76,1748.76,1748.76,1748.76,1748.76,1748.76,1748.76,1748.76,1748.76,1748.76,1748.76,1748.76,1748.76,1748.76,1748.76,1748.76,1748.76,1748.76,1748.76,1748.76,1748.76,1748.76,1748.76,1748.76,1748.76,1748.76,1748.76,1748.76,1748.76,1748.76,1748.76,1748.76,1748.76,1748.76,1748.76,1748.76,1748.76,1748.76,1748.76,1748.76,1748.76,1748.76,1748.76,1748.76,1748.76,1812.45,1812.45,1812.45,1812.45,1812.45,1812.45,1812.45,1812.45,1812.45,1812.45,1896.57,1896.57,1896.57,1896.57,1896.57,1896.57,1896.57,1896.57,1896.57,1936.66,1936.66,1936.66,1936.66,1936.66,2076.19,2076.19,2076.19,2156.23,2156.23,2156.23,2156.23,2156.23,2156.23,2156.23,2156.23,2156.23,2156.23,2156.23,2156.23,2156.23,2156.23,2156.23,2156.23,2157.18,2157.18,2157.18,2157.18,2157.18,2157.18,2157.18,2157.18,2157.18,2157.18,2157.18,2157.18,2157.18,2157.18,2157.18,2190.5,2190.5,2190.5,2190.5,2190.5,2190.5,2190.5,2190.5,2190.5,2190.5,2190.5,2190.5,2190.5,2190.5,2190.5,2190.5,2190.5,2190.5,2190.5,2190.5,2190.5,2190.5,2190.5,2190.5,2190.5,2190.5,2190.5,2190.5,2190.5,2190.5,2190.5,2262.35,2262.35,2262.35,2262.35,2262.35,2262.35,2262.35,2262.35,2262.35,2262.35,2262.35,2262.35,2262.35,2262.35,2262.35,2262.35,2262.35,2341.25,2341.25,2341.25,2341.25,2341.25,2341.25,2341.25,2341.25,2341.25,2341.25,2341.25,2341.25,2341.25,2341.25,2341.25,2341.25,2341.25,2341.25,2396.02,2396.02,2396.02,2396.02,2396.02,2396.02,2396.02,2396.02,2396.02,2396.02,2396.02,2396.02,2396.02,2396.02,2396.02,2446.23,2446.23,2446.23,2446.23,2446.23,2446.23,2492.38,2492.38,2492.38,2492.38,2492.38,2492.38,2492.38,2492.38,2492.38,2492.38,2492.38,2492.38,2492.38,2492.38,2492.38,2492.38,2492.38,2492.38,2492.38,2492.38,2492.38,2492.38,2492.38,2492.38,2492.38,2492.38,2492.38,2492.38,2492.38,2492.38,2492.38,2492.38,2492.38,2492.38,2492.38,2492.38,2492.38,2492.38,2492.38,2492.38,2492.38,2492.38,2492.38,2492.38,2492.38,2492.38,2561.33,2561.33,2561.33,2561.33,2561.33,2561.33,2561.33,2561.33,2561.33,2561.33,2561.33,2561.33,2561.33,2561.33,2561.33,2561.33,2561.33,2561.33,2561.33,2561.33,2630.5,2630.5,2630.5,2630.5,2630.5,2630.5,2630.5,2642.41,2642.41,2642.41,2642.41,2642.41,2642.41,2642.41,2642.41,2642.41,2642.41,2642.41,2642.41,2642.41,2642.41,2642.41,2642.41,2642.41,2657.55,2657.55,2657.55,2657.55,2657.55,2657.55,2657.55,2657.55,2657.55,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2713.47,2835.9,2835.9,2835.9,2835.9,2835.9,2883.61,2883.61,2883.61,2906.74,2906.74,2906.74,2906.74,2906.74,2906.74,2906.74,2906.74,2906.74,2906.74,2906.74,2906.74,2906.74,2993.16,2993.16,2993.16,2993.16,2993.16,2993.16,3069.73,3069.73,3069.73,3069.73,3069.73,3069.73,3069.73,3069.73,3069.73,3069.73,3069.73,3069.73,3069.73,3069.73,3069.73,3069.73,3069.73,3069.73,3069.73,3069.73,3069.73,3069.73,3069.73,3069.73,3069.73,3069.73,3069.73,3069.73,3069.73,3069.73,3069.73,3092.24,3092.24,3139.75,3201.23,3201.23,3201.23,3201.23,3201.23,3201.23,3201.23,3201.23,3201.23,3201.23,3201.23,3201.23,3201.23,3201.23,3201.23,3201.23,3201.23,3201.23,3201.23,3201.23,3201.23,3201.23,3201.23,3201.23,3201.23,3201.23,3201.23,3201.23,3201.23,3201.23,3201.23,3201.23,3201.23,3201.23,3201.23,3201.23,3201.23,3201.23,3201.23,3201.23,3201.23,3201.23,3201.23,3201.23,3294.18,3294.18,3294.18,3294.18,3294.18,3294.18,3294.18,3294.18,3294.18,3294.18,3294.18,3294.18,3294.18,3294.18,3294.18,3294.18,3294.18,3294.18,3294.18,3294.18,3294.18,3294.18,3294.18,3294.18,3294.18,3353.11,3353.11,3353.11,3353.11,3353.11,3353.11,3353.11,3353.11,3353.11,3353.11,3353.11,3353.11,3353.11,3353.11,3353.11,3353.11,3353.11,3369.29,3369.29,3369.29,3369.29,3369.29,3468.54,3565.16],"yaxis":"y","type":"scattergl"},{"hovertemplate":"purchased_by=Bob<br>purchased_date=%{x}<br>Cumulative Dollars Spent=%{y}<extra></extra>","legendgroup":"Bob","line":{"color":"#EF553B","dash":"solid"},"marker":{"symbol":"circle"},"mode":"lines","name":"Bob","showlegend":true,"x":["2020-01-01T00:00:00","2020-01-02T00:00:00","2020-01-03T00:00:00","2020-01-04T00:00:00","2020-01-05T00:00:00","2020-01-06T00:00:00","2020-01-07T00:00:00","2020-01-08T00:00:00","2020-01-09T00:00:00","2020-01-10T00:00:00","2020-01-11T00:00:00","2020-01-12T00:00:00","2020-01-13T00:00:00","2020-01-14T00:00:00","2020-01-15T00:00:00","2020-01-16T00:00:00","2020-01-17T00:00:00","2020-01-18T00:00:00","2020-01-19T00:00:00","2020-01-20T00:00:00","2020-01-21T00:00:00","2020-01-22T00:00:00","2020-01-23T00:00:00","2020-01-24T00:00:00","2020-01-25T00:00:00","2020-01-26T00:00:00","2020-01-27T00:00:00","2020-01-28T00:00:00","2020-01-29T00:00:00","2020-01-30T00:00:00","2020-01-31T00:00:00","2020-02-01T00:00:00","2020-02-02T00:00:00","2020-02-03T00:00:00","2020-02-04T00:00:00","2020-02-05T00:00:00","2020-02-06T00:00:00","2020-02-07T00:00:00","2020-02-08T00:00:00","2020-02-09T00:00:00","2020-02-10T00:00:00","2020-02-11T00:00:00","2020-02-12T00:00:00","2020-02-13T00:00:00","2020-02-14T00:00:00","2020-02-15T00:00:00","2020-02-16T00:00:00","2020-02-17T00:00:00","2020-02-18T00:00:00","2020-02-19T00:00:00","2020-02-20T00:00:00","2020-02-21T00:00:00","2020-02-22T00:00:00","2020-02-23T00:00:00","2020-02-24T00:00:00","2020-02-25T00:00:00","2020-02-26T00:00:00","2020-02-27T00:00:00","2020-02-28T00:00:00","2020-02-29T00:00:00","2020-03-01T00:00:00","2020-03-02T00:00:00","2020-03-03T00:00:00","2020-03-04T00:00:00","2020-03-05T00:00:00","2020-03-06T00:00:00","2020-03-07T00:00:00","2020-03-08T00:00:00","2020-03-09T00:00:00","2020-03-10T00:00:00","2020-03-11T00:00:00","2020-03-12T00:00:00","2020-03-13T00:00:00","2020-03-14T00:00:00","2020-03-15T00:00:00","2020-03-16T00:00:00","2020-03-17T00:00:00","2020-03-18T00:00:00","2020-03-19T00:00:00","2020-03-20T00:00:00","2020-03-21T00:00:00","2020-03-22T00:00:00","2020-03-23T00:00:00","2020-03-24T00:00:00","2020-03-25T00:00:00","2020-03-26T00:00:00","2020-03-27T00:00:00","2020-03-28T00:00:00","2020-03-29T00:00:00","2020-03-30T00:00:00","2020-03-31T00:00:00","2020-04-01T00:00:00","2020-04-02T00:00:00","2020-04-03T00:00:00","2020-04-04T00:00:00","2020-04-05T00:00:00","2020-04-06T00:00:00","2020-04-07T00:00:00","2020-04-08T00:00:00","2020-04-09T00:00:00","2020-04-10T00:00:00","2020-04-11T00:00:00","2020-04-12T00:00:00","2020-04-13T00:00:00","2020-04-14T00:00:00","2020-04-15T00:00:00","2020-04-16T00:00:00","2020-04-17T00:00:00","2020-04-18T00:00:00","2020-04-19T00:00:00","2020-04-20T00:00:00","2020-04-21T00:00:00","2020-04-22T00:00:00","2020-04-23T00:00:00","2020-04-24T00:00:00","2020-04-25T00:00:00","2020-04-26T00:00:00","2020-04-27T00:00:00","2020-04-28T00:00:00","2020-04-29T00:00:00","2020-04-30T00:00:00","2020-05-01T00:00:00","2020-05-02T00:00:00","2020-05-03T00:00:00","2020-05-04T00:00:00","2020-05-05T00:00:00","2020-05-06T00:00:00","2020-05-07T00:00:00","2020-05-08T00:00:00","2020-05-09T00:00:00","2020-05-10T00:00:00","2020-05-11T00:00:00","2020-05-12T00:00:00","2020-05-13T00:00:00","2020-05-14T00:00:00","2020-05-15T00:00:00","2020-05-16T00:00:00","2020-05-17T00:00:00","2020-05-18T00:00:00","2020-05-19T00:00:00","2020-05-20T00:00:00","2020-05-21T00:00:00","2020-05-22T00:00:00","2020-05-23T00:00:00","2020-05-24T00:00:00","2020-05-25T00:00:00","2020-05-26T00:00:00","2020-05-27T00:00:00","2020-05-28T00:00:00","2020-05-29T00:00:00","2020-05-30T00:00:00","2020-05-31T00:00:00","2020-06-01T00:00:00","2020-06-02T00:00:00","2020-06-03T00:00:00","2020-06-04T00:00:00","2020-06-05T00:00:00","2020-06-06T00:00:00","2020-06-07T00:00:00","2020-06-08T00:00:00","2020-06-09T00:00:00","2020-06-10T00:00:00","2020-06-11T00:00:00","2020-06-12T00:00:00","2020-06-13T00:00:00","2020-06-14T00:00:00","2020-06-15T00:00:00","2020-06-16T00:00:00","2020-06-17T00:00:00","2020-06-18T00:00:00","2020-06-19T00:00:00","2020-06-20T00:00:00","2020-06-21T00:00:00","2020-06-22T00:00:00","2020-06-23T00:00:00","2020-06-24T00:00:00","2020-06-25T00:00:00","2020-06-26T00:00:00","2020-06-27T00:00:00","2020-06-28T00:00:00","2020-06-29T00:00:00","2020-06-30T00:00:00","2020-07-01T00:00:00","2020-07-02T00:00:00","2020-07-03T00:00:00","2020-07-04T00:00:00","2020-07-05T00:00:00","2020-07-06T00:00:00","2020-07-07T00:00:00","2020-07-08T00:00:00","2020-07-09T00:00:00","2020-07-10T00:00:00","2020-07-11T00:00:00","2020-07-12T00:00:00","2020-07-13T00:00:00","2020-07-14T00:00:00","2020-07-15T00:00:00","2020-07-16T00:00:00","2020-07-17T00:00:00","2020-07-18T00:00:00","2020-07-19T00:00:00","2020-07-20T00:00:00","2020-07-21T00:00:00","2020-07-22T00:00:00","2020-07-23T00:00:00","2020-07-24T00:00:00","2020-07-25T00:00:00","2020-07-26T00:00:00","2020-07-27T00:00:00","2020-07-28T00:00:00","2020-07-29T00:00:00","2020-07-30T00:00:00","2020-07-31T00:00:00","2020-08-01T00:00:00","2020-08-02T00:00:00","2020-08-03T00:00:00","2020-08-04T00:00:00","2020-08-05T00:00:00","2020-08-06T00:00:00","2020-08-07T00:00:00","2020-08-08T00:00:00","2020-08-09T00:00:00","2020-08-10T00:00:00","2020-08-11T00:00:00","2020-08-12T00:00:00","2020-08-13T00:00:00","2020-08-14T00:00:00","2020-08-15T00:00:00","2020-08-16T00:00:00","2020-08-17T00:00:00","2020-08-18T00:00:00","2020-08-19T00:00:00","2020-08-20T00:00:00","2020-08-21T00:00:00","2020-08-22T00:00:00","2020-08-23T00:00:00","2020-08-24T00:00:00","2020-08-25T00:00:00","2020-08-26T00:00:00","2020-08-27T00:00:00","2020-08-28T00:00:00","2020-08-29T00:00:00","2020-08-30T00:00:00","2020-08-31T00:00:00","2020-09-01T00:00:00","2020-09-02T00:00:00","2020-09-03T00:00:00","2020-09-04T00:00:00","2020-09-05T00:00:00","2020-09-06T00:00:00","2020-09-07T00:00:00","2020-09-08T00:00:00","2020-09-09T00:00:00","2020-09-10T00:00:00","2020-09-11T00:00:00","2020-09-12T00:00:00","2020-09-13T00:00:00","2020-09-14T00:00:00","2020-09-15T00:00:00","2020-09-16T00:00:00","2020-09-17T00:00:00","2020-09-18T00:00:00","2020-09-19T00:00:00","2020-09-20T00:00:00","2020-09-21T00:00:00","2020-09-22T00:00:00","2020-09-23T00:00:00","2020-09-24T00:00:00","2020-09-25T00:00:00","2020-09-26T00:00:00","2020-09-27T00:00:00","2020-09-28T00:00:00","2020-09-29T00:00:00","2020-09-30T00:00:00","2020-10-01T00:00:00","2020-10-02T00:00:00","2020-10-03T00:00:00","2020-10-04T00:00:00","2020-10-05T00:00:00","2020-10-06T00:00:00","2020-10-07T00:00:00","2020-10-08T00:00:00","2020-10-09T00:00:00","2020-10-10T00:00:00","2020-10-11T00:00:00","2020-10-12T00:00:00","2020-10-13T00:00:00","2020-10-14T00:00:00","2020-10-15T00:00:00","2020-10-16T00:00:00","2020-10-17T00:00:00","2020-10-18T00:00:00","2020-10-19T00:00:00","2020-10-20T00:00:00","2020-10-21T00:00:00","2020-10-22T00:00:00","2020-10-23T00:00:00","2020-10-24T00:00:00","2020-10-25T00:00:00","2020-10-26T00:00:00","2020-10-27T00:00:00","2020-10-28T00:00:00","2020-10-29T00:00:00","2020-10-30T00:00:00","2020-10-31T00:00:00","2020-11-01T00:00:00","2020-11-02T00:00:00","2020-11-03T00:00:00","2020-11-04T00:00:00","2020-11-05T00:00:00","2020-11-06T00:00:00","2020-11-07T00:00:00","2020-11-08T00:00:00","2020-11-09T00:00:00","2020-11-10T00:00:00","2020-11-11T00:00:00","2020-11-12T00:00:00","2020-11-13T00:00:00","2020-11-14T00:00:00","2020-11-15T00:00:00","2020-11-16T00:00:00","2020-11-17T00:00:00","2020-11-18T00:00:00","2020-11-19T00:00:00","2020-11-20T00:00:00","2020-11-21T00:00:00","2020-11-22T00:00:00","2020-11-23T00:00:00","2020-11-24T00:00:00","2020-11-25T00:00:00","2020-11-26T00:00:00","2020-11-27T00:00:00","2020-11-28T00:00:00","2020-11-29T00:00:00","2020-11-30T00:00:00","2020-12-01T00:00:00","2020-12-02T00:00:00","2020-12-03T00:00:00","2020-12-04T00:00:00","2020-12-05T00:00:00","2020-12-06T00:00:00","2020-12-07T00:00:00","2020-12-08T00:00:00","2020-12-09T00:00:00","2020-12-10T00:00:00","2020-12-11T00:00:00","2020-12-12T00:00:00","2020-12-13T00:00:00","2020-12-14T00:00:00","2020-12-15T00:00:00","2020-12-16T00:00:00","2020-12-17T00:00:00","2020-12-18T00:00:00","2020-12-19T00:00:00","2020-12-20T00:00:00","2020-12-21T00:00:00","2020-12-22T00:00:00","2020-12-23T00:00:00","2020-12-24T00:00:00","2020-12-25T00:00:00","2020-12-26T00:00:00","2020-12-27T00:00:00","2020-12-28T00:00:00","2020-12-29T00:00:00","2020-12-30T00:00:00","2020-12-31T00:00:00","2021-01-01T00:00:00","2021-01-02T00:00:00","2021-01-03T00:00:00","2021-01-04T00:00:00","2021-01-05T00:00:00","2021-01-06T00:00:00","2021-01-07T00:00:00","2021-01-08T00:00:00","2021-01-09T00:00:00","2021-01-10T00:00:00","2021-01-11T00:00:00","2021-01-12T00:00:00","2021-01-13T00:00:00","2021-01-14T00:00:00","2021-01-15T00:00:00","2021-01-16T00:00:00","2021-01-17T00:00:00","2021-01-18T00:00:00","2021-01-19T00:00:00","2021-01-20T00:00:00","2021-01-21T00:00:00","2021-01-22T00:00:00","2021-01-23T00:00:00","2021-01-24T00:00:00","2021-01-25T00:00:00","2021-01-26T00:00:00","2021-01-27T00:00:00","2021-01-28T00:00:00","2021-01-29T00:00:00","2021-01-30T00:00:00","2021-01-31T00:00:00","2021-02-01T00:00:00","2021-02-02T00:00:00","2021-02-03T00:00:00","2021-02-04T00:00:00","2021-02-05T00:00:00","2021-02-06T00:00:00","2021-02-07T00:00:00","2021-02-08T00:00:00","2021-02-09T00:00:00","2021-02-10T00:00:00","2021-02-11T00:00:00","2021-02-12T00:00:00","2021-02-13T00:00:00","2021-02-14T00:00:00","2021-02-15T00:00:00","2021-02-16T00:00:00","2021-02-17T00:00:00","2021-02-18T00:00:00","2021-02-19T00:00:00","2021-02-20T00:00:00","2021-02-21T00:00:00","2021-02-22T00:00:00","2021-02-23T00:00:00","2021-02-24T00:00:00","2021-02-25T00:00:00","2021-02-26T00:00:00","2021-02-27T00:00:00","2021-02-28T00:00:00","2021-03-01T00:00:00","2021-03-02T00:00:00","2021-03-03T00:00:00","2021-03-04T00:00:00","2021-03-05T00:00:00","2021-03-06T00:00:00","2021-03-07T00:00:00","2021-03-08T00:00:00","2021-03-09T00:00:00","2021-03-10T00:00:00","2021-03-11T00:00:00","2021-03-12T00:00:00","2021-03-13T00:00:00","2021-03-14T00:00:00","2021-03-15T00:00:00","2021-03-16T00:00:00","2021-03-17T00:00:00","2021-03-18T00:00:00","2021-03-19T00:00:00","2021-03-20T00:00:00","2021-03-21T00:00:00","2021-03-22T00:00:00","2021-03-23T00:00:00","2021-03-24T00:00:00","2021-03-25T00:00:00","2021-03-26T00:00:00","2021-03-27T00:00:00","2021-03-28T00:00:00","2021-03-29T00:00:00","2021-03-30T00:00:00","2021-03-31T00:00:00","2021-04-01T00:00:00","2021-04-02T00:00:00","2021-04-03T00:00:00","2021-04-04T00:00:00","2021-04-05T00:00:00","2021-04-06T00:00:00","2021-04-07T00:00:00","2021-04-08T00:00:00","2021-04-09T00:00:00","2021-04-10T00:00:00","2021-04-11T00:00:00","2021-04-12T00:00:00","2021-04-13T00:00:00","2021-04-14T00:00:00","2021-04-15T00:00:00","2021-04-16T00:00:00","2021-04-17T00:00:00","2021-04-18T00:00:00","2021-04-19T00:00:00","2021-04-20T00:00:00","2021-04-21T00:00:00","2021-04-22T00:00:00","2021-04-23T00:00:00","2021-04-24T00:00:00","2021-04-25T00:00:00","2021-04-26T00:00:00","2021-04-27T00:00:00","2021-04-28T00:00:00","2021-04-29T00:00:00","2021-04-30T00:00:00","2021-05-01T00:00:00","2021-05-02T00:00:00","2021-05-03T00:00:00","2021-05-04T00:00:00","2021-05-05T00:00:00","2021-05-06T00:00:00","2021-05-07T00:00:00","2021-05-08T00:00:00","2021-05-09T00:00:00","2021-05-10T00:00:00","2021-05-11T00:00:00","2021-05-12T00:00:00","2021-05-13T00:00:00","2021-05-14T00:00:00","2021-05-15T00:00:00","2021-05-16T00:00:00","2021-05-17T00:00:00","2021-05-18T00:00:00","2021-05-19T00:00:00","2021-05-20T00:00:00","2021-05-21T00:00:00","2021-05-22T00:00:00","2021-05-23T00:00:00","2021-05-24T00:00:00","2021-05-25T00:00:00","2021-05-26T00:00:00","2021-05-27T00:00:00","2021-05-28T00:00:00","2021-05-29T00:00:00","2021-05-30T00:00:00","2021-05-31T00:00:00","2021-06-01T00:00:00","2021-06-02T00:00:00","2021-06-03T00:00:00","2021-06-04T00:00:00","2021-06-05T00:00:00","2021-06-06T00:00:00","2021-06-07T00:00:00","2021-06-08T00:00:00","2021-06-09T00:00:00","2021-06-10T00:00:00","2021-06-11T00:00:00","2021-06-12T00:00:00","2021-06-13T00:00:00","2021-06-14T00:00:00","2021-06-15T00:00:00","2021-06-16T00:00:00","2021-06-17T00:00:00","2021-06-18T00:00:00","2021-06-19T00:00:00","2021-06-20T00:00:00","2021-06-21T00:00:00","2021-06-22T00:00:00","2021-06-23T00:00:00","2021-06-24T00:00:00","2021-06-25T00:00:00","2021-06-26T00:00:00","2021-06-27T00:00:00","2021-06-28T00:00:00","2021-06-29T00:00:00","2021-06-30T00:00:00","2021-07-01T00:00:00","2021-07-02T00:00:00","2021-07-03T00:00:00","2021-07-04T00:00:00","2021-07-05T00:00:00","2021-07-06T00:00:00","2021-07-07T00:00:00","2021-07-08T00:00:00","2021-07-09T00:00:00","2021-07-10T00:00:00","2021-07-11T00:00:00","2021-07-12T00:00:00","2021-07-13T00:00:00","2021-07-14T00:00:00","2021-07-15T00:00:00","2021-07-16T00:00:00","2021-07-17T00:00:00","2021-07-18T00:00:00","2021-07-19T00:00:00","2021-07-20T00:00:00","2021-07-21T00:00:00","2021-07-22T00:00:00","2021-07-23T00:00:00","2021-07-24T00:00:00","2021-07-25T00:00:00","2021-07-26T00:00:00","2021-07-27T00:00:00","2021-07-28T00:00:00","2021-07-29T00:00:00","2021-07-30T00:00:00","2021-07-31T00:00:00","2021-08-01T00:00:00","2021-08-02T00:00:00","2021-08-03T00:00:00","2021-08-04T00:00:00","2021-08-05T00:00:00","2021-08-06T00:00:00","2021-08-07T00:00:00","2021-08-08T00:00:00","2021-08-09T00:00:00","2021-08-10T00:00:00","2021-08-11T00:00:00","2021-08-12T00:00:00","2021-08-13T00:00:00","2021-08-14T00:00:00","2021-08-15T00:00:00","2021-08-16T00:00:00","2021-08-17T00:00:00","2021-08-18T00:00:00","2021-08-19T00:00:00","2021-08-20T00:00:00","2021-08-21T00:00:00","2021-08-22T00:00:00","2021-08-23T00:00:00","2021-08-24T00:00:00","2021-08-25T00:00:00","2021-08-26T00:00:00","2021-08-27T00:00:00","2021-08-28T00:00:00","2021-08-29T00:00:00","2021-08-30T00:00:00","2021-08-31T00:00:00","2021-09-01T00:00:00","2021-09-02T00:00:00","2021-09-03T00:00:00","2021-09-04T00:00:00","2021-09-05T00:00:00","2021-09-06T00:00:00","2021-09-07T00:00:00","2021-09-08T00:00:00","2021-09-09T00:00:00","2021-09-10T00:00:00","2021-09-11T00:00:00","2021-09-12T00:00:00","2021-09-13T00:00:00","2021-09-14T00:00:00","2021-09-15T00:00:00","2021-09-16T00:00:00","2021-09-17T00:00:00","2021-09-18T00:00:00","2021-09-19T00:00:00","2021-09-20T00:00:00","2021-09-21T00:00:00","2021-09-22T00:00:00","2021-09-23T00:00:00","2021-09-24T00:00:00","2021-09-25T00:00:00","2021-09-26T00:00:00","2021-09-27T00:00:00","2021-09-28T00:00:00","2021-09-29T00:00:00","2021-09-30T00:00:00","2021-10-01T00:00:00","2021-10-02T00:00:00","2021-10-03T00:00:00","2021-10-04T00:00:00","2021-10-05T00:00:00","2021-10-06T00:00:00","2021-10-07T00:00:00","2021-10-08T00:00:00","2021-10-09T00:00:00","2021-10-10T00:00:00","2021-10-11T00:00:00","2021-10-12T00:00:00","2021-10-13T00:00:00","2021-10-14T00:00:00","2021-10-15T00:00:00","2021-10-16T00:00:00","2021-10-17T00:00:00","2021-10-18T00:00:00","2021-10-19T00:00:00","2021-10-20T00:00:00","2021-10-21T00:00:00","2021-10-22T00:00:00","2021-10-23T00:00:00","2021-10-24T00:00:00","2021-10-25T00:00:00","2021-10-26T00:00:00","2021-10-27T00:00:00","2021-10-28T00:00:00","2021-10-29T00:00:00","2021-10-30T00:00:00","2021-10-31T00:00:00","2021-11-01T00:00:00","2021-11-02T00:00:00","2021-11-03T00:00:00","2021-11-04T00:00:00","2021-11-05T00:00:00","2021-11-06T00:00:00","2021-11-07T00:00:00","2021-11-08T00:00:00","2021-11-09T00:00:00","2021-11-10T00:00:00","2021-11-11T00:00:00","2021-11-12T00:00:00","2021-11-13T00:00:00","2021-11-14T00:00:00","2021-11-15T00:00:00","2021-11-16T00:00:00","2021-11-17T00:00:00","2021-11-18T00:00:00","2021-11-19T00:00:00","2021-11-20T00:00:00","2021-11-21T00:00:00","2021-11-22T00:00:00","2021-11-23T00:00:00","2021-11-24T00:00:00","2021-11-25T00:00:00","2021-11-26T00:00:00","2021-11-27T00:00:00","2021-11-28T00:00:00","2021-11-29T00:00:00","2021-11-30T00:00:00","2021-12-01T00:00:00","2021-12-02T00:00:00","2021-12-03T00:00:00","2021-12-04T00:00:00","2021-12-05T00:00:00","2021-12-06T00:00:00","2021-12-07T00:00:00","2021-12-08T00:00:00","2021-12-09T00:00:00","2021-12-10T00:00:00","2021-12-11T00:00:00","2021-12-12T00:00:00","2021-12-13T00:00:00","2021-12-14T00:00:00","2021-12-15T00:00:00","2021-12-16T00:00:00","2021-12-17T00:00:00","2021-12-18T00:00:00","2021-12-19T00:00:00","2021-12-20T00:00:00","2021-12-21T00:00:00","2021-12-22T00:00:00","2021-12-23T00:00:00","2021-12-24T00:00:00","2021-12-25T00:00:00","2021-12-26T00:00:00","2021-12-27T00:00:00","2021-12-28T00:00:00","2021-12-29T00:00:00","2021-12-30T00:00:00","2021-12-31T00:00:00","2022-01-01T00:00:00","2022-01-02T00:00:00","2022-01-03T00:00:00","2022-01-04T00:00:00","2022-01-05T00:00:00","2022-01-06T00:00:00","2022-01-07T00:00:00","2022-01-08T00:00:00","2022-01-09T00:00:00","2022-01-10T00:00:00","2022-01-11T00:00:00","2022-01-12T00:00:00","2022-01-13T00:00:00","2022-01-14T00:00:00","2022-01-15T00:00:00","2022-01-16T00:00:00","2022-01-17T00:00:00","2022-01-18T00:00:00","2022-01-19T00:00:00","2022-01-20T00:00:00","2022-01-21T00:00:00","2022-01-22T00:00:00","2022-01-23T00:00:00","2022-01-24T00:00:00","2022-01-25T00:00:00","2022-01-26T00:00:00","2022-01-27T00:00:00","2022-01-28T00:00:00","2022-01-29T00:00:00","2022-01-30T00:00:00","2022-01-31T00:00:00","2022-02-01T00:00:00","2022-02-02T00:00:00","2022-02-03T00:00:00","2022-02-04T00:00:00","2022-02-05T00:00:00","2022-02-06T00:00:00","2022-02-07T00:00:00","2022-02-08T00:00:00","2022-02-09T00:00:00","2022-02-10T00:00:00","2022-02-11T00:00:00","2022-02-12T00:00:00","2022-02-13T00:00:00","2022-02-14T00:00:00","2022-02-15T00:00:00","2022-02-16T00:00:00","2022-02-17T00:00:00","2022-02-18T00:00:00","2022-02-19T00:00:00","2022-02-20T00:00:00","2022-02-21T00:00:00","2022-02-22T00:00:00","2022-02-23T00:00:00","2022-02-24T00:00:00","2022-02-25T00:00:00","2022-02-26T00:00:00","2022-02-27T00:00:00","2022-02-28T00:00:00","2022-03-01T00:00:00","2022-03-02T00:00:00","2022-03-03T00:00:00","2022-03-04T00:00:00","2022-03-05T00:00:00","2022-03-06T00:00:00","2022-03-07T00:00:00","2022-03-08T00:00:00","2022-03-09T00:00:00","2022-03-10T00:00:00","2022-03-11T00:00:00","2022-03-12T00:00:00","2022-03-13T00:00:00","2022-03-14T00:00:00","2022-03-15T00:00:00","2022-03-16T00:00:00","2022-03-17T00:00:00","2022-03-18T00:00:00","2022-03-19T00:00:00","2022-03-20T00:00:00","2022-03-21T00:00:00","2022-03-22T00:00:00","2022-03-23T00:00:00","2022-03-24T00:00:00","2022-03-25T00:00:00","2022-03-26T00:00:00","2022-03-27T00:00:00","2022-03-28T00:00:00","2022-03-29T00:00:00","2022-03-30T00:00:00","2022-03-31T00:00:00","2022-04-01T00:00:00","2022-04-02T00:00:00","2022-04-03T00:00:00","2022-04-04T00:00:00","2022-04-05T00:00:00","2022-04-06T00:00:00","2022-04-07T00:00:00","2022-04-08T00:00:00","2022-04-09T00:00:00","2022-04-10T00:00:00","2022-04-11T00:00:00","2022-04-12T00:00:00","2022-04-13T00:00:00","2022-04-14T00:00:00","2022-04-15T00:00:00","2022-04-16T00:00:00","2022-04-17T00:00:00","2022-04-18T00:00:00","2022-04-19T00:00:00","2022-04-20T00:00:00","2022-04-21T00:00:00","2022-04-22T00:00:00","2022-04-23T00:00:00","2022-04-24T00:00:00","2022-04-25T00:00:00","2022-04-26T00:00:00","2022-04-27T00:00:00","2022-04-28T00:00:00","2022-04-29T00:00:00","2022-04-30T00:00:00","2022-05-01T00:00:00","2022-05-02T00:00:00","2022-05-03T00:00:00","2022-05-04T00:00:00","2022-05-05T00:00:00","2022-05-06T00:00:00","2022-05-07T00:00:00","2022-05-08T00:00:00","2022-05-09T00:00:00","2022-05-10T00:00:00","2022-05-11T00:00:00","2022-05-12T00:00:00","2022-05-13T00:00:00","2022-05-14T00:00:00","2022-05-15T00:00:00","2022-05-16T00:00:00","2022-05-17T00:00:00","2022-05-18T00:00:00","2022-05-19T00:00:00","2022-05-20T00:00:00","2022-05-21T00:00:00","2022-05-22T00:00:00","2022-05-23T00:00:00","2022-05-24T00:00:00","2022-05-25T00:00:00","2022-05-26T00:00:00","2022-05-27T00:00:00","2022-05-28T00:00:00","2022-05-29T00:00:00","2022-05-30T00:00:00","2022-05-31T00:00:00","2022-06-01T00:00:00","2022-06-02T00:00:00","2022-06-03T00:00:00","2022-06-04T00:00:00","2022-06-05T00:00:00","2022-06-06T00:00:00","2022-06-07T00:00:00","2022-06-08T00:00:00","2022-06-09T00:00:00","2022-06-10T00:00:00","2022-06-11T00:00:00","2022-06-12T00:00:00","2022-06-13T00:00:00","2022-06-14T00:00:00","2022-06-15T00:00:00","2022-06-16T00:00:00","2022-06-17T00:00:00","2022-06-18T00:00:00","2022-06-19T00:00:00","2022-06-20T00:00:00","2022-06-21T00:00:00","2022-06-22T00:00:00","2022-06-23T00:00:00","2022-06-24T00:00:00","2022-06-25T00:00:00","2022-06-26T00:00:00","2022-06-27T00:00:00","2022-06-28T00:00:00","2022-06-29T00:00:00","2022-06-30T00:00:00","2022-07-01T00:00:00","2022-07-02T00:00:00","2022-07-03T00:00:00","2022-07-04T00:00:00","2022-07-05T00:00:00","2022-07-06T00:00:00","2022-07-07T00:00:00","2022-07-08T00:00:00","2022-07-09T00:00:00","2022-07-10T00:00:00","2022-07-11T00:00:00","2022-07-12T00:00:00","2022-07-13T00:00:00","2022-07-14T00:00:00","2022-07-15T00:00:00","2022-07-16T00:00:00","2022-07-17T00:00:00","2022-07-18T00:00:00","2022-07-19T00:00:00","2022-07-20T00:00:00","2022-07-21T00:00:00","2022-07-22T00:00:00","2022-07-23T00:00:00","2022-07-24T00:00:00","2022-07-25T00:00:00","2022-07-26T00:00:00","2022-07-27T00:00:00","2022-07-28T00:00:00","2022-07-29T00:00:00","2022-07-30T00:00:00","2022-07-31T00:00:00","2022-08-01T00:00:00","2022-08-02T00:00:00","2022-08-03T00:00:00","2022-08-04T00:00:00","2022-08-05T00:00:00","2022-08-06T00:00:00","2022-08-07T00:00:00","2022-08-08T00:00:00","2022-08-09T00:00:00","2022-08-10T00:00:00","2022-08-11T00:00:00","2022-08-12T00:00:00","2022-08-13T00:00:00","2022-08-14T00:00:00","2022-08-15T00:00:00","2022-08-16T00:00:00","2022-08-17T00:00:00","2022-08-18T00:00:00","2022-08-19T00:00:00","2022-08-20T00:00:00","2022-08-21T00:00:00","2022-08-22T00:00:00","2022-08-23T00:00:00","2022-08-24T00:00:00","2022-08-25T00:00:00","2022-08-26T00:00:00","2022-08-27T00:00:00","2022-08-28T00:00:00","2022-08-29T00:00:00","2022-08-30T00:00:00","2022-08-31T00:00:00","2022-09-01T00:00:00","2022-09-02T00:00:00","2022-09-03T00:00:00","2022-09-04T00:00:00","2022-09-05T00:00:00","2022-09-06T00:00:00","2022-09-07T00:00:00","2022-09-08T00:00:00","2022-09-09T00:00:00","2022-09-10T00:00:00","2022-09-11T00:00:00","2022-09-12T00:00:00","2022-09-13T00:00:00","2022-09-14T00:00:00","2022-09-15T00:00:00","2022-09-16T00:00:00","2022-09-17T00:00:00","2022-09-18T00:00:00","2022-09-19T00:00:00","2022-09-20T00:00:00","2022-09-21T00:00:00","2022-09-22T00:00:00","2022-09-23T00:00:00","2022-09-24T00:00:00","2022-09-25T00:00:00","2022-09-26T00:00:00","2022-09-27T00:00:00","2022-09-28T00:00:00","2022-09-29T00:00:00","2022-09-30T00:00:00","2022-10-01T00:00:00","2022-10-02T00:00:00","2022-10-03T00:00:00","2022-10-04T00:00:00","2022-10-05T00:00:00","2022-10-06T00:00:00","2022-10-07T00:00:00","2022-10-08T00:00:00","2022-10-09T00:00:00","2022-10-10T00:00:00","2022-10-11T00:00:00","2022-10-12T00:00:00","2022-10-13T00:00:00","2022-10-14T00:00:00","2022-10-15T00:00:00","2022-10-16T00:00:00","2022-10-17T00:00:00","2022-10-18T00:00:00","2022-10-19T00:00:00","2022-10-20T00:00:00","2022-10-21T00:00:00","2022-10-22T00:00:00","2022-10-23T00:00:00","2022-10-24T00:00:00","2022-10-25T00:00:00","2022-10-26T00:00:00","2022-10-27T00:00:00","2022-10-28T00:00:00","2022-10-29T00:00:00","2022-10-30T00:00:00","2022-10-31T00:00:00","2022-11-01T00:00:00","2022-11-02T00:00:00","2022-11-03T00:00:00","2022-11-04T00:00:00","2022-11-05T00:00:00","2022-11-06T00:00:00","2022-11-07T00:00:00","2022-11-08T00:00:00","2022-11-09T00:00:00","2022-11-10T00:00:00","2022-11-11T00:00:00","2022-11-12T00:00:00","2022-11-13T00:00:00","2022-11-14T00:00:00","2022-11-15T00:00:00","2022-11-16T00:00:00","2022-11-17T00:00:00","2022-11-18T00:00:00","2022-11-19T00:00:00","2022-11-20T00:00:00","2022-11-21T00:00:00","2022-11-22T00:00:00","2022-11-23T00:00:00","2022-11-24T00:00:00","2022-11-25T00:00:00","2022-11-26T00:00:00","2022-11-27T00:00:00","2022-11-28T00:00:00","2022-11-29T00:00:00","2022-11-30T00:00:00","2022-12-01T00:00:00","2022-12-02T00:00:00","2022-12-03T00:00:00","2022-12-04T00:00:00","2022-12-05T00:00:00","2022-12-06T00:00:00","2022-12-07T00:00:00","2022-12-08T00:00:00","2022-12-09T00:00:00","2022-12-10T00:00:00","2022-12-11T00:00:00","2022-12-12T00:00:00","2022-12-13T00:00:00"],"xaxis":"x","y":[0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,70.72,70.72,70.72,70.72,70.72,70.72,70.72,70.72,70.72,70.72,70.72,70.72,70.72,70.72,70.72,70.72,70.72,70.72,70.72,70.72,70.72,70.72,70.72,70.72,70.72,70.72,70.72,70.72,70.72,70.72,70.72,70.72,70.72,70.72,70.72,70.72,70.72,70.72,70.72,70.72,70.72,134.94,134.94,134.94,134.94,134.94,134.94,134.94,134.94,134.94,134.94,134.94,220.14,220.14,220.14,220.14,220.14,220.14,220.14,220.14,220.14,220.14,220.14,220.14,220.14,220.14,220.14,220.14,267.52,267.52,267.52,267.52,267.52,267.52,267.52,267.52,267.52,267.52,267.52,267.52,267.52,267.52,267.52,267.52,267.52,267.52,267.52,267.52,267.52,267.52,267.52,267.52,267.52,267.52,267.52,267.52,267.52,267.52,336.7,336.7,336.7,336.7,336.7,336.7,336.7,336.7,336.7,336.7,336.7,336.7,336.7,336.7,336.7,399.53,425.81,511.71,511.71,511.71,511.71,511.71,511.71,511.71,511.71,511.71,511.71,511.71,511.71,511.71,511.71,511.71,511.71,511.71,511.71,511.71,511.71,511.71,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,591.93,650.89,650.89,650.89,650.89,650.89,650.89,650.89,650.89,650.89,650.89,650.89,650.89,650.89,650.89,650.89,693.42,693.42,693.42,693.42,693.42,693.42,693.42,693.42,693.42,693.42,707.15,707.15,707.15,707.15,707.15,707.15,707.15,707.15,707.15,707.15,707.15,707.15,707.15,707.15,707.15,707.15,707.15,707.15,707.15,707.15,707.15,707.15,707.15,707.15,707.15,707.15,707.15,707.15,707.15,707.15,707.15,707.15,707.15,733.1,733.1,733.1,733.1,733.1,733.1,733.1,733.1,733.1,733.1,733.1,733.1,733.1,733.1,758.94,758.94,758.94,758.94,758.94,758.94,758.94,758.94,758.94,758.94,758.94,758.94,758.94,758.94,758.94,758.94,758.94,758.94,758.94,758.94,758.94,758.94,758.94,758.94,758.94,758.94,758.94,758.94,758.94,758.94,758.94,794.01,794.01,794.01,794.01,794.01,794.01,794.01,794.01,794.01,794.01,794.01,794.01,794.01,794.01,794.01,794.01,794.01,840.03,840.03,840.03,840.03,840.03,840.03,840.03,840.03,840.03,840.03,840.03,840.03,840.03,840.03,840.03,840.03,840.03,901.42,901.42,901.42,901.42,901.42,901.42,901.42,901.42,901.42,901.42,901.42,901.42,901.42,901.42,907.14,907.14,907.14,907.14,907.14,907.14,907.14,961.67,961.67,961.67,961.67,961.67,961.67,961.67,961.67,961.67,961.67,961.67,961.67,961.67,961.67,961.67,961.67,961.67,961.67,961.67,961.67,961.67,961.67,961.67,961.67,961.67,961.67,976.15,976.15,976.15,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1040.91,1077.14,1077.14,1077.14,1077.14,1077.14,1077.14,1077.14,1077.14,1077.14,1077.14,1077.14,1077.14,1077.14,1077.14,1077.14,1077.14,1077.14,1077.14,1077.14,1077.14,1077.14,1077.14,1077.14,1077.14,1077.14,1077.14,1077.14,1077.14,1077.14,1077.14,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1112.8,1199.05,1199.05,1199.05,1199.05,1199.05,1199.05,1199.05,1199.05,1317.2,1317.2,1317.2,1317.2,1317.2,1317.2,1317.2,1317.2,1317.2,1317.2,1317.2,1317.2,1317.2,1317.2,1317.2,1382.47,1382.47,1382.47,1382.47,1416.92,1416.92,1416.92,1416.92,1416.92,1416.92,1416.92,1416.92,1416.92,1416.92,1416.92,1416.92,1416.92,1416.92,1416.92,1416.92,1416.92,1416.92,1416.92,1416.92,1416.92,1416.92,1416.92,1416.92,1416.92,1465.42,1465.42,1465.42,1465.42,1465.42,1465.42,1465.42,1465.42,1465.42,1465.42,1465.42,1465.42,1465.42,1465.42,1465.42,1465.42,1465.42,1465.42,1465.42,1465.42,1465.42,1465.42,1465.42,1465.42,1465.42,1465.42,1465.42,1465.42,1465.42,1465.42,1465.42,1465.42,1465.42,1465.42,1465.42,1465.42,1465.42,1465.42,1510.35,1510.35,1510.35,1510.35,1510.35,1510.35,1516.62,1516.62,1516.62,1516.62,1516.62,1516.62,1516.62,1516.62,1516.62,1516.62,1516.62,1516.62,1516.62,1516.62,1516.62,1516.62,1516.62,1516.62,1516.62,1516.62,1516.62,1516.62,1516.62,1516.62,1516.62,1516.62,1597.59,1597.59,1597.59,1597.59,1669.27,1669.27,1669.27,1669.27,1669.27,1669.27,1669.27,1669.27,1716.73,1716.73,1716.73,1716.73,1716.73,1716.73,1716.73,1716.73,1716.73,1716.73,1716.73,1716.73,1716.73,1751.54,1751.54,1751.54,1751.54,1751.54,1751.54,1751.54,1751.54,1751.54,1751.54,1751.54,1751.54,1751.54,1751.54,1751.54,1751.54,1751.54,1751.54,1751.54,1751.54,1751.54,1751.54,1751.54,1751.54,1751.54,1751.54,1751.54,1751.54,1751.54,1751.54,1862.15,1862.15,1862.15,1862.15,1862.15,1923.67,1923.67,1923.67,1923.67,1923.67,1923.67,1923.67,1923.67,1923.67,1923.67,1923.67,1923.67,1923.67,1923.67,1923.67,1923.67,1923.67,1923.67,1923.67,1923.67,1923.67,1923.67,1923.67,1923.67,1923.67,1923.67,1923.67,1923.67,1923.67,1923.67,1923.67,1923.67,1923.67,1923.67,2005.91,2005.91,2005.91,2005.91,2005.91,2005.91,2005.91,2094.78,2094.78,2094.78,2094.78,2094.78,2094.78,2143.35,2143.35,2198.9,2198.9,2198.9,2198.9,2198.9,2198.9,2198.9,2198.9,2198.9,2198.9,2198.9,2198.9,2198.9,2198.9,2198.9,2198.9,2198.9,2198.9,2198.9,2233.51,2233.51,2233.51,2233.51,2233.51,2233.51,2233.51,2233.51,2233.51,2233.51,2233.51,2233.51,2233.51,2233.51,2233.51,2233.51,2307.44,2307.44,2307.44,2369.09,2369.09,2369.09,2369.09,2369.09,2369.09,2369.09,2369.09,2369.09,2369.09,2369.09,2369.09,2369.09,2369.09,2369.09,2369.09,2369.09,2369.09,2369.09,2369.09,2369.09,2369.09,2369.09,2369.09,2369.09,2369.09,2369.09,2369.09,2369.09,2369.09,2369.09,2369.09,2369.09,2408.14,2408.14,2408.14,2408.14,2408.14,2408.14,2408.14,2408.14,2408.14,2408.14,2408.14,2465.99,2465.99,2465.99,2529.26,2529.26,2529.26,2529.26,2529.26,2529.26,2529.26,2529.26,2529.26,2529.26,2529.26,2529.26,2529.26,2529.26,2529.26,2529.26,2529.26,2529.26,2529.26,2529.26,2529.26,2529.26,2529.26,2529.26,2529.26,2529.26,2576.07,2576.07,2576.07,2576.07,2576.07,2576.07,2576.07,2576.07,2576.07,2576.07,2576.07,2576.07,2576.07,2576.07,2576.07,2576.07,2576.07,2576.07,2576.07,2576.07,2576.07,2576.07,2670.9,2670.9,2670.9,2670.9,2670.9,2670.9,2670.9,2670.9,2670.9,2670.9,2670.9,2670.9,2670.9,2754.61,2754.61,2754.61,2754.61,2754.61,2754.61,2754.61,2757.19,2757.19,2757.19,2757.19,2757.19,2757.19,2757.19,2757.19,2757.19,2757.19,2757.19,2757.19,2757.19,2757.19,2757.19,2757.19,2757.19,2757.19,2757.19,2757.19,2757.19,2757.19,2757.19,2757.19,2757.19,2757.19,2757.19,2757.19,2757.19,2757.19,2757.19,2757.19,2757.19,2757.19,2757.19,2757.19,2757.19,2757.19,2757.19,2773.36,2773.36,2773.36,2773.36,2773.36,2773.36,2773.36,2802.28,2802.28,2802.28,2802.28,2802.28,2802.28,2802.28,2802.28,2802.28,2802.28,2802.28,2802.28,2802.28,2860.3,2860.3,2860.3,2860.3,2860.3,2860.3,2860.3,2860.3,2860.3,2860.3,2860.3,2860.3,2860.3,2860.3,2860.3,2860.3,2860.3,2860.3,2860.3,2860.3,2860.3,2860.3,2860.3,2888.26,2888.26,2888.26,2888.26,2888.26,2888.26,2888.26,2888.26,2888.26,2888.26,2888.26,2890.73,2890.73,2890.73,2890.73,2890.73,2890.73,2890.73,2890.73,2890.73,2948.75,2948.75,2948.75,2948.75,2948.75,2948.75,2948.75,2948.75,2948.75,2948.75,2948.75,2948.75,2948.75,2948.75,2948.75,2948.75,2948.75,2948.75,2948.75,2948.75,2948.75,2948.75,2948.75,2956.94,2956.94,2956.94,2956.94,3019.81,3019.81,3019.81,3019.81],"yaxis":"y","type":"scattergl"},{"hovertemplate":"purchased_by=Chuck<br>purchased_date=%{x}<br>Cumulative Dollars Spent=%{y}<extra></extra>","legendgroup":"Chuck","line":{"color":"#00cc96","dash":"solid"},"marker":{"symbol":"circle"},"mode":"lines","name":"Chuck","showlegend":true,"x":["2020-01-01T00:00:00","2020-01-02T00:00:00","2020-01-03T00:00:00","2020-01-04T00:00:00","2020-01-05T00:00:00","2020-01-06T00:00:00","2020-01-07T00:00:00","2020-01-08T00:00:00","2020-01-09T00:00:00","2020-01-10T00:00:00","2020-01-11T00:00:00","2020-01-12T00:00:00","2020-01-13T00:00:00","2020-01-14T00:00:00","2020-01-15T00:00:00","2020-01-16T00:00:00","2020-01-17T00:00:00","2020-01-18T00:00:00","2020-01-19T00:00:00","2020-01-20T00:00:00","2020-01-21T00:00:00","2020-01-22T00:00:00","2020-01-23T00:00:00","2020-01-24T00:00:00","2020-01-25T00:00:00","2020-01-26T00:00:00","2020-01-27T00:00:00","2020-01-28T00:00:00","2020-01-29T00:00:00","2020-01-30T00:00:00","2020-01-31T00:00:00","2020-02-01T00:00:00","2020-02-02T00:00:00","2020-02-03T00:00:00","2020-02-04T00:00:00","2020-02-05T00:00:00","2020-02-06T00:00:00","2020-02-07T00:00:00","2020-02-08T00:00:00","2020-02-09T00:00:00","2020-02-10T00:00:00","2020-02-11T00:00:00","2020-02-12T00:00:00","2020-02-13T00:00:00","2020-02-14T00:00:00","2020-02-15T00:00:00","2020-02-16T00:00:00","2020-02-17T00:00:00","2020-02-18T00:00:00","2020-02-19T00:00:00","2020-02-20T00:00:00","2020-02-21T00:00:00","2020-02-22T00:00:00","2020-02-23T00:00:00","2020-02-24T00:00:00","2020-02-25T00:00:00","2020-02-26T00:00:00","2020-02-27T00:00:00","2020-02-28T00:00:00","2020-02-29T00:00:00","2020-03-01T00:00:00","2020-03-02T00:00:00","2020-03-03T00:00:00","2020-03-04T00:00:00","2020-03-05T00:00:00","2020-03-06T00:00:00","2020-03-07T00:00:00","2020-03-08T00:00:00","2020-03-09T00:00:00","2020-03-10T00:00:00","2020-03-11T00:00:00","2020-03-12T00:00:00","2020-03-13T00:00:00","2020-03-14T00:00:00","2020-03-15T00:00:00","2020-03-16T00:00:00","2020-03-17T00:00:00","2020-03-18T00:00:00","2020-03-19T00:00:00","2020-03-20T00:00:00","2020-03-21T00:00:00","2020-03-22T00:00:00","2020-03-23T00:00:00","2020-03-24T00:00:00","2020-03-25T00:00:00","2020-03-26T00:00:00","2020-03-27T00:00:00","2020-03-28T00:00:00","2020-03-29T00:00:00","2020-03-30T00:00:00","2020-03-31T00:00:00","2020-04-01T00:00:00","2020-04-02T00:00:00","2020-04-03T00:00:00","2020-04-04T00:00:00","2020-04-05T00:00:00","2020-04-06T00:00:00","2020-04-07T00:00:00","2020-04-08T00:00:00","2020-04-09T00:00:00","2020-04-10T00:00:00","2020-04-11T00:00:00","2020-04-12T00:00:00","2020-04-13T00:00:00","2020-04-14T00:00:00","2020-04-15T00:00:00","2020-04-16T00:00:00","2020-04-17T00:00:00","2020-04-18T00:00:00","2020-04-19T00:00:00","2020-04-20T00:00:00","2020-04-21T00:00:00","2020-04-22T00:00:00","2020-04-23T00:00:00","2020-04-24T00:00:00","2020-04-25T00:00:00","2020-04-26T00:00:00","2020-04-27T00:00:00","2020-04-28T00:00:00","2020-04-29T00:00:00","2020-04-30T00:00:00","2020-05-01T00:00:00","2020-05-02T00:00:00","2020-05-03T00:00:00","2020-05-04T00:00:00","2020-05-05T00:00:00","2020-05-06T00:00:00","2020-05-07T00:00:00","2020-05-08T00:00:00","2020-05-09T00:00:00","2020-05-10T00:00:00","2020-05-11T00:00:00","2020-05-12T00:00:00","2020-05-13T00:00:00","2020-05-14T00:00:00","2020-05-15T00:00:00","2020-05-16T00:00:00","2020-05-17T00:00:00","2020-05-18T00:00:00","2020-05-19T00:00:00","2020-05-20T00:00:00","2020-05-21T00:00:00","2020-05-22T00:00:00","2020-05-23T00:00:00","2020-05-24T00:00:00","2020-05-25T00:00:00","2020-05-26T00:00:00","2020-05-27T00:00:00","2020-05-28T00:00:00","2020-05-29T00:00:00","2020-05-30T00:00:00","2020-05-31T00:00:00","2020-06-01T00:00:00","2020-06-02T00:00:00","2020-06-03T00:00:00","2020-06-04T00:00:00","2020-06-05T00:00:00","2020-06-06T00:00:00","2020-06-07T00:00:00","2020-06-08T00:00:00","2020-06-09T00:00:00","2020-06-10T00:00:00","2020-06-11T00:00:00","2020-06-12T00:00:00","2020-06-13T00:00:00","2020-06-14T00:00:00","2020-06-15T00:00:00","2020-06-16T00:00:00","2020-06-17T00:00:00","2020-06-18T00:00:00","2020-06-19T00:00:00","2020-06-20T00:00:00","2020-06-21T00:00:00","2020-06-22T00:00:00","2020-06-23T00:00:00","2020-06-24T00:00:00","2020-06-25T00:00:00","2020-06-26T00:00:00","2020-06-27T00:00:00","2020-06-28T00:00:00","2020-06-29T00:00:00","2020-06-30T00:00:00","2020-07-01T00:00:00","2020-07-02T00:00:00","2020-07-03T00:00:00","2020-07-04T00:00:00","2020-07-05T00:00:00","2020-07-06T00:00:00","2020-07-07T00:00:00","2020-07-08T00:00:00","2020-07-09T00:00:00","2020-07-10T00:00:00","2020-07-11T00:00:00","2020-07-12T00:00:00","2020-07-13T00:00:00","2020-07-14T00:00:00","2020-07-15T00:00:00","2020-07-16T00:00:00","2020-07-17T00:00:00","2020-07-18T00:00:00","2020-07-19T00:00:00","2020-07-20T00:00:00","2020-07-21T00:00:00","2020-07-22T00:00:00","2020-07-23T00:00:00","2020-07-24T00:00:00","2020-07-25T00:00:00","2020-07-26T00:00:00","2020-07-27T00:00:00","2020-07-28T00:00:00","2020-07-29T00:00:00","2020-07-30T00:00:00","2020-07-31T00:00:00","2020-08-01T00:00:00","2020-08-02T00:00:00","2020-08-03T00:00:00","2020-08-04T00:00:00","2020-08-05T00:00:00","2020-08-06T00:00:00","2020-08-07T00:00:00","2020-08-08T00:00:00","2020-08-09T00:00:00","2020-08-10T00:00:00","2020-08-11T00:00:00","2020-08-12T00:00:00","2020-08-13T00:00:00","2020-08-14T00:00:00","2020-08-15T00:00:00","2020-08-16T00:00:00","2020-08-17T00:00:00","2020-08-18T00:00:00","2020-08-19T00:00:00","2020-08-20T00:00:00","2020-08-21T00:00:00","2020-08-22T00:00:00","2020-08-23T00:00:00","2020-08-24T00:00:00","2020-08-25T00:00:00","2020-08-26T00:00:00","2020-08-27T00:00:00","2020-08-28T00:00:00","2020-08-29T00:00:00","2020-08-30T00:00:00","2020-08-31T00:00:00","2020-09-01T00:00:00","2020-09-02T00:00:00","2020-09-03T00:00:00","2020-09-04T00:00:00","2020-09-05T00:00:00","2020-09-06T00:00:00","2020-09-07T00:00:00","2020-09-08T00:00:00","2020-09-09T00:00:00","2020-09-10T00:00:00","2020-09-11T00:00:00","2020-09-12T00:00:00","2020-09-13T00:00:00","2020-09-14T00:00:00","2020-09-15T00:00:00","2020-09-16T00:00:00","2020-09-17T00:00:00","2020-09-18T00:00:00","2020-09-19T00:00:00","2020-09-20T00:00:00","2020-09-21T00:00:00","2020-09-22T00:00:00","2020-09-23T00:00:00","2020-09-24T00:00:00","2020-09-25T00:00:00","2020-09-26T00:00:00","2020-09-27T00:00:00","2020-09-28T00:00:00","2020-09-29T00:00:00","2020-09-30T00:00:00","2020-10-01T00:00:00","2020-10-02T00:00:00","2020-10-03T00:00:00","2020-10-04T00:00:00","2020-10-05T00:00:00","2020-10-06T00:00:00","2020-10-07T00:00:00","2020-10-08T00:00:00","2020-10-09T00:00:00","2020-10-10T00:00:00","2020-10-11T00:00:00","2020-10-12T00:00:00","2020-10-13T00:00:00","2020-10-14T00:00:00","2020-10-15T00:00:00","2020-10-16T00:00:00","2020-10-17T00:00:00","2020-10-18T00:00:00","2020-10-19T00:00:00","2020-10-20T00:00:00","2020-10-21T00:00:00","2020-10-22T00:00:00","2020-10-23T00:00:00","2020-10-24T00:00:00","2020-10-25T00:00:00","2020-10-26T00:00:00","2020-10-27T00:00:00","2020-10-28T00:00:00","2020-10-29T00:00:00","2020-10-30T00:00:00","2020-10-31T00:00:00","2020-11-01T00:00:00","2020-11-02T00:00:00","2020-11-03T00:00:00","2020-11-04T00:00:00","2020-11-05T00:00:00","2020-11-06T00:00:00","2020-11-07T00:00:00","2020-11-08T00:00:00","2020-11-09T00:00:00","2020-11-10T00:00:00","2020-11-11T00:00:00","2020-11-12T00:00:00","2020-11-13T00:00:00","2020-11-14T00:00:00","2020-11-15T00:00:00","2020-11-16T00:00:00","2020-11-17T00:00:00","2020-11-18T00:00:00","2020-11-19T00:00:00","2020-11-20T00:00:00","2020-11-21T00:00:00","2020-11-22T00:00:00","2020-11-23T00:00:00","2020-11-24T00:00:00","2020-11-25T00:00:00","2020-11-26T00:00:00","2020-11-27T00:00:00","2020-11-28T00:00:00","2020-11-29T00:00:00","2020-11-30T00:00:00","2020-12-01T00:00:00","2020-12-02T00:00:00","2020-12-03T00:00:00","2020-12-04T00:00:00","2020-12-05T00:00:00","2020-12-06T00:00:00","2020-12-07T00:00:00","2020-12-08T00:00:00","2020-12-09T00:00:00","2020-12-10T00:00:00","2020-12-11T00:00:00","2020-12-12T00:00:00","2020-12-13T00:00:00","2020-12-14T00:00:00","2020-12-15T00:00:00","2020-12-16T00:00:00","2020-12-17T00:00:00","2020-12-18T00:00:00","2020-12-19T00:00:00","2020-12-20T00:00:00","2020-12-21T00:00:00","2020-12-22T00:00:00","2020-12-23T00:00:00","2020-12-24T00:00:00","2020-12-25T00:00:00","2020-12-26T00:00:00","2020-12-27T00:00:00","2020-12-28T00:00:00","2020-12-29T00:00:00","2020-12-30T00:00:00","2020-12-31T00:00:00","2021-01-01T00:00:00","2021-01-02T00:00:00","2021-01-03T00:00:00","2021-01-04T00:00:00","2021-01-05T00:00:00","2021-01-06T00:00:00","2021-01-07T00:00:00","2021-01-08T00:00:00","2021-01-09T00:00:00","2021-01-10T00:00:00","2021-01-11T00:00:00","2021-01-12T00:00:00","2021-01-13T00:00:00","2021-01-14T00:00:00","2021-01-15T00:00:00","2021-01-16T00:00:00","2021-01-17T00:00:00","2021-01-18T00:00:00","2021-01-19T00:00:00","2021-01-20T00:00:00","2021-01-21T00:00:00","2021-01-22T00:00:00","2021-01-23T00:00:00","2021-01-24T00:00:00","2021-01-25T00:00:00","2021-01-26T00:00:00","2021-01-27T00:00:00","2021-01-28T00:00:00","2021-01-29T00:00:00","2021-01-30T00:00:00","2021-01-31T00:00:00","2021-02-01T00:00:00","2021-02-02T00:00:00","2021-02-03T00:00:00","2021-02-04T00:00:00","2021-02-05T00:00:00","2021-02-06T00:00:00","2021-02-07T00:00:00","2021-02-08T00:00:00","2021-02-09T00:00:00","2021-02-10T00:00:00","2021-02-11T00:00:00","2021-02-12T00:00:00","2021-02-13T00:00:00","2021-02-14T00:00:00","2021-02-15T00:00:00","2021-02-16T00:00:00","2021-02-17T00:00:00","2021-02-18T00:00:00","2021-02-19T00:00:00","2021-02-20T00:00:00","2021-02-21T00:00:00","2021-02-22T00:00:00","2021-02-23T00:00:00","2021-02-24T00:00:00","2021-02-25T00:00:00","2021-02-26T00:00:00","2021-02-27T00:00:00","2021-02-28T00:00:00","2021-03-01T00:00:00","2021-03-02T00:00:00","2021-03-03T00:00:00","2021-03-04T00:00:00","2021-03-05T00:00:00","2021-03-06T00:00:00","2021-03-07T00:00:00","2021-03-08T00:00:00","2021-03-09T00:00:00","2021-03-10T00:00:00","2021-03-11T00:00:00","2021-03-12T00:00:00","2021-03-13T00:00:00","2021-03-14T00:00:00","2021-03-15T00:00:00","2021-03-16T00:00:00","2021-03-17T00:00:00","2021-03-18T00:00:00","2021-03-19T00:00:00","2021-03-20T00:00:00","2021-03-21T00:00:00","2021-03-22T00:00:00","2021-03-23T00:00:00","2021-03-24T00:00:00","2021-03-25T00:00:00","2021-03-26T00:00:00","2021-03-27T00:00:00","2021-03-28T00:00:00","2021-03-29T00:00:00","2021-03-30T00:00:00","2021-03-31T00:00:00","2021-04-01T00:00:00","2021-04-02T00:00:00","2021-04-03T00:00:00","2021-04-04T00:00:00","2021-04-05T00:00:00","2021-04-06T00:00:00","2021-04-07T00:00:00","2021-04-08T00:00:00","2021-04-09T00:00:00","2021-04-10T00:00:00","2021-04-11T00:00:00","2021-04-12T00:00:00","2021-04-13T00:00:00","2021-04-14T00:00:00","2021-04-15T00:00:00","2021-04-16T00:00:00","2021-04-17T00:00:00","2021-04-18T00:00:00","2021-04-19T00:00:00","2021-04-20T00:00:00","2021-04-21T00:00:00","2021-04-22T00:00:00","2021-04-23T00:00:00","2021-04-24T00:00:00","2021-04-25T00:00:00","2021-04-26T00:00:00","2021-04-27T00:00:00","2021-04-28T00:00:00","2021-04-29T00:00:00","2021-04-30T00:00:00","2021-05-01T00:00:00","2021-05-02T00:00:00","2021-05-03T00:00:00","2021-05-04T00:00:00","2021-05-05T00:00:00","2021-05-06T00:00:00","2021-05-07T00:00:00","2021-05-08T00:00:00","2021-05-09T00:00:00","2021-05-10T00:00:00","2021-05-11T00:00:00","2021-05-12T00:00:00","2021-05-13T00:00:00","2021-05-14T00:00:00","2021-05-15T00:00:00","2021-05-16T00:00:00","2021-05-17T00:00:00","2021-05-18T00:00:00","2021-05-19T00:00:00","2021-05-20T00:00:00","2021-05-21T00:00:00","2021-05-22T00:00:00","2021-05-23T00:00:00","2021-05-24T00:00:00","2021-05-25T00:00:00","2021-05-26T00:00:00","2021-05-27T00:00:00","2021-05-28T00:00:00","2021-05-29T00:00:00","2021-05-30T00:00:00","2021-05-31T00:00:00","2021-06-01T00:00:00","2021-06-02T00:00:00","2021-06-03T00:00:00","2021-06-04T00:00:00","2021-06-05T00:00:00","2021-06-06T00:00:00","2021-06-07T00:00:00","2021-06-08T00:00:00","2021-06-09T00:00:00","2021-06-10T00:00:00","2021-06-11T00:00:00","2021-06-12T00:00:00","2021-06-13T00:00:00","2021-06-14T00:00:00","2021-06-15T00:00:00","2021-06-16T00:00:00","2021-06-17T00:00:00","2021-06-18T00:00:00","2021-06-19T00:00:00","2021-06-20T00:00:00","2021-06-21T00:00:00","2021-06-22T00:00:00","2021-06-23T00:00:00","2021-06-24T00:00:00","2021-06-25T00:00:00","2021-06-26T00:00:00","2021-06-27T00:00:00","2021-06-28T00:00:00","2021-06-29T00:00:00","2021-06-30T00:00:00","2021-07-01T00:00:00","2021-07-02T00:00:00","2021-07-03T00:00:00","2021-07-04T00:00:00","2021-07-05T00:00:00","2021-07-06T00:00:00","2021-07-07T00:00:00","2021-07-08T00:00:00","2021-07-09T00:00:00","2021-07-10T00:00:00","2021-07-11T00:00:00","2021-07-12T00:00:00","2021-07-13T00:00:00","2021-07-14T00:00:00","2021-07-15T00:00:00","2021-07-16T00:00:00","2021-07-17T00:00:00","2021-07-18T00:00:00","2021-07-19T00:00:00","2021-07-20T00:00:00","2021-07-21T00:00:00","2021-07-22T00:00:00","2021-07-23T00:00:00","2021-07-24T00:00:00","2021-07-25T00:00:00","2021-07-26T00:00:00","2021-07-27T00:00:00","2021-07-28T00:00:00","2021-07-29T00:00:00","2021-07-30T00:00:00","2021-07-31T00:00:00","2021-08-01T00:00:00","2021-08-02T00:00:00","2021-08-03T00:00:00","2021-08-04T00:00:00","2021-08-05T00:00:00","2021-08-06T00:00:00","2021-08-07T00:00:00","2021-08-08T00:00:00","2021-08-09T00:00:00","2021-08-10T00:00:00","2021-08-11T00:00:00","2021-08-12T00:00:00","2021-08-13T00:00:00","2021-08-14T00:00:00","2021-08-15T00:00:00","2021-08-16T00:00:00","2021-08-17T00:00:00","2021-08-18T00:00:00","2021-08-19T00:00:00","2021-08-20T00:00:00","2021-08-21T00:00:00","2021-08-22T00:00:00","2021-08-23T00:00:00","2021-08-24T00:00:00","2021-08-25T00:00:00","2021-08-26T00:00:00","2021-08-27T00:00:00","2021-08-28T00:00:00","2021-08-29T00:00:00","2021-08-30T00:00:00","2021-08-31T00:00:00","2021-09-01T00:00:00","2021-09-02T00:00:00","2021-09-03T00:00:00","2021-09-04T00:00:00","2021-09-05T00:00:00","2021-09-06T00:00:00","2021-09-07T00:00:00","2021-09-08T00:00:00","2021-09-09T00:00:00","2021-09-10T00:00:00","2021-09-11T00:00:00","2021-09-12T00:00:00","2021-09-13T00:00:00","2021-09-14T00:00:00","2021-09-15T00:00:00","2021-09-16T00:00:00","2021-09-17T00:00:00","2021-09-18T00:00:00","2021-09-19T00:00:00","2021-09-20T00:00:00","2021-09-21T00:00:00","2021-09-22T00:00:00","2021-09-23T00:00:00","2021-09-24T00:00:00","2021-09-25T00:00:00","2021-09-26T00:00:00","2021-09-27T00:00:00","2021-09-28T00:00:00","2021-09-29T00:00:00","2021-09-30T00:00:00","2021-10-01T00:00:00","2021-10-02T00:00:00","2021-10-03T00:00:00","2021-10-04T00:00:00","2021-10-05T00:00:00","2021-10-06T00:00:00","2021-10-07T00:00:00","2021-10-08T00:00:00","2021-10-09T00:00:00","2021-10-10T00:00:00","2021-10-11T00:00:00","2021-10-12T00:00:00","2021-10-13T00:00:00","2021-10-14T00:00:00","2021-10-15T00:00:00","2021-10-16T00:00:00","2021-10-17T00:00:00","2021-10-18T00:00:00","2021-10-19T00:00:00","2021-10-20T00:00:00","2021-10-21T00:00:00","2021-10-22T00:00:00","2021-10-23T00:00:00","2021-10-24T00:00:00","2021-10-25T00:00:00","2021-10-26T00:00:00","2021-10-27T00:00:00","2021-10-28T00:00:00","2021-10-29T00:00:00","2021-10-30T00:00:00","2021-10-31T00:00:00","2021-11-01T00:00:00","2021-11-02T00:00:00","2021-11-03T00:00:00","2021-11-04T00:00:00","2021-11-05T00:00:00","2021-11-06T00:00:00","2021-11-07T00:00:00","2021-11-08T00:00:00","2021-11-09T00:00:00","2021-11-10T00:00:00","2021-11-11T00:00:00","2021-11-12T00:00:00","2021-11-13T00:00:00","2021-11-14T00:00:00","2021-11-15T00:00:00","2021-11-16T00:00:00","2021-11-17T00:00:00","2021-11-18T00:00:00","2021-11-19T00:00:00","2021-11-20T00:00:00","2021-11-21T00:00:00","2021-11-22T00:00:00","2021-11-23T00:00:00","2021-11-24T00:00:00","2021-11-25T00:00:00","2021-11-26T00:00:00","2021-11-27T00:00:00","2021-11-28T00:00:00","2021-11-29T00:00:00","2021-11-30T00:00:00","2021-12-01T00:00:00","2021-12-02T00:00:00","2021-12-03T00:00:00","2021-12-04T00:00:00","2021-12-05T00:00:00","2021-12-06T00:00:00","2021-12-07T00:00:00","2021-12-08T00:00:00","2021-12-09T00:00:00","2021-12-10T00:00:00","2021-12-11T00:00:00","2021-12-12T00:00:00","2021-12-13T00:00:00","2021-12-14T00:00:00","2021-12-15T00:00:00","2021-12-16T00:00:00","2021-12-17T00:00:00","2021-12-18T00:00:00","2021-12-19T00:00:00","2021-12-20T00:00:00","2021-12-21T00:00:00","2021-12-22T00:00:00","2021-12-23T00:00:00","2021-12-24T00:00:00","2021-12-25T00:00:00","2021-12-26T00:00:00","2021-12-27T00:00:00","2021-12-28T00:00:00","2021-12-29T00:00:00","2021-12-30T00:00:00","2021-12-31T00:00:00","2022-01-01T00:00:00","2022-01-02T00:00:00","2022-01-03T00:00:00","2022-01-04T00:00:00","2022-01-05T00:00:00","2022-01-06T00:00:00","2022-01-07T00:00:00","2022-01-08T00:00:00","2022-01-09T00:00:00","2022-01-10T00:00:00","2022-01-11T00:00:00","2022-01-12T00:00:00","2022-01-13T00:00:00","2022-01-14T00:00:00","2022-01-15T00:00:00","2022-01-16T00:00:00","2022-01-17T00:00:00","2022-01-18T00:00:00","2022-01-19T00:00:00","2022-01-20T00:00:00","2022-01-21T00:00:00","2022-01-22T00:00:00","2022-01-23T00:00:00","2022-01-24T00:00:00","2022-01-25T00:00:00","2022-01-26T00:00:00","2022-01-27T00:00:00","2022-01-28T00:00:00","2022-01-29T00:00:00","2022-01-30T00:00:00","2022-01-31T00:00:00","2022-02-01T00:00:00","2022-02-02T00:00:00","2022-02-03T00:00:00","2022-02-04T00:00:00","2022-02-05T00:00:00","2022-02-06T00:00:00","2022-02-07T00:00:00","2022-02-08T00:00:00","2022-02-09T00:00:00","2022-02-10T00:00:00","2022-02-11T00:00:00","2022-02-12T00:00:00","2022-02-13T00:00:00","2022-02-14T00:00:00","2022-02-15T00:00:00","2022-02-16T00:00:00","2022-02-17T00:00:00","2022-02-18T00:00:00","2022-02-19T00:00:00","2022-02-20T00:00:00","2022-02-21T00:00:00","2022-02-22T00:00:00","2022-02-23T00:00:00","2022-02-24T00:00:00","2022-02-25T00:00:00","2022-02-26T00:00:00","2022-02-27T00:00:00","2022-02-28T00:00:00","2022-03-01T00:00:00","2022-03-02T00:00:00","2022-03-03T00:00:00","2022-03-04T00:00:00","2022-03-05T00:00:00","2022-03-06T00:00:00","2022-03-07T00:00:00","2022-03-08T00:00:00","2022-03-09T00:00:00","2022-03-10T00:00:00","2022-03-11T00:00:00","2022-03-12T00:00:00","2022-03-13T00:00:00","2022-03-14T00:00:00","2022-03-15T00:00:00","2022-03-16T00:00:00","2022-03-17T00:00:00","2022-03-18T00:00:00","2022-03-19T00:00:00","2022-03-20T00:00:00","2022-03-21T00:00:00","2022-03-22T00:00:00","2022-03-23T00:00:00","2022-03-24T00:00:00","2022-03-25T00:00:00","2022-03-26T00:00:00","2022-03-27T00:00:00","2022-03-28T00:00:00","2022-03-29T00:00:00","2022-03-30T00:00:00","2022-03-31T00:00:00","2022-04-01T00:00:00","2022-04-02T00:00:00","2022-04-03T00:00:00","2022-04-04T00:00:00","2022-04-05T00:00:00","2022-04-06T00:00:00","2022-04-07T00:00:00","2022-04-08T00:00:00","2022-04-09T00:00:00","2022-04-10T00:00:00","2022-04-11T00:00:00","2022-04-12T00:00:00","2022-04-13T00:00:00","2022-04-14T00:00:00","2022-04-15T00:00:00","2022-04-16T00:00:00","2022-04-17T00:00:00","2022-04-18T00:00:00","2022-04-19T00:00:00","2022-04-20T00:00:00","2022-04-21T00:00:00","2022-04-22T00:00:00","2022-04-23T00:00:00","2022-04-24T00:00:00","2022-04-25T00:00:00","2022-04-26T00:00:00","2022-04-27T00:00:00","2022-04-28T00:00:00","2022-04-29T00:00:00","2022-04-30T00:00:00","2022-05-01T00:00:00","2022-05-02T00:00:00","2022-05-03T00:00:00","2022-05-04T00:00:00","2022-05-05T00:00:00","2022-05-06T00:00:00","2022-05-07T00:00:00","2022-05-08T00:00:00","2022-05-09T00:00:00","2022-05-10T00:00:00","2022-05-11T00:00:00","2022-05-12T00:00:00","2022-05-13T00:00:00","2022-05-14T00:00:00","2022-05-15T00:00:00","2022-05-16T00:00:00","2022-05-17T00:00:00","2022-05-18T00:00:00","2022-05-19T00:00:00","2022-05-20T00:00:00","2022-05-21T00:00:00","2022-05-22T00:00:00","2022-05-23T00:00:00","2022-05-24T00:00:00","2022-05-25T00:00:00","2022-05-26T00:00:00","2022-05-27T00:00:00","2022-05-28T00:00:00","2022-05-29T00:00:00","2022-05-30T00:00:00","2022-05-31T00:00:00","2022-06-01T00:00:00","2022-06-02T00:00:00","2022-06-03T00:00:00","2022-06-04T00:00:00","2022-06-05T00:00:00","2022-06-06T00:00:00","2022-06-07T00:00:00","2022-06-08T00:00:00","2022-06-09T00:00:00","2022-06-10T00:00:00","2022-06-11T00:00:00","2022-06-12T00:00:00","2022-06-13T00:00:00","2022-06-14T00:00:00","2022-06-15T00:00:00","2022-06-16T00:00:00","2022-06-17T00:00:00","2022-06-18T00:00:00","2022-06-19T00:00:00","2022-06-20T00:00:00","2022-06-21T00:00:00","2022-06-22T00:00:00","2022-06-23T00:00:00","2022-06-24T00:00:00","2022-06-25T00:00:00","2022-06-26T00:00:00","2022-06-27T00:00:00","2022-06-28T00:00:00","2022-06-29T00:00:00","2022-06-30T00:00:00","2022-07-01T00:00:00","2022-07-02T00:00:00","2022-07-03T00:00:00","2022-07-04T00:00:00","2022-07-05T00:00:00","2022-07-06T00:00:00","2022-07-07T00:00:00","2022-07-08T00:00:00","2022-07-09T00:00:00","2022-07-10T00:00:00","2022-07-11T00:00:00","2022-07-12T00:00:00","2022-07-13T00:00:00","2022-07-14T00:00:00","2022-07-15T00:00:00","2022-07-16T00:00:00","2022-07-17T00:00:00","2022-07-18T00:00:00","2022-07-19T00:00:00","2022-07-20T00:00:00","2022-07-21T00:00:00","2022-07-22T00:00:00","2022-07-23T00:00:00","2022-07-24T00:00:00","2022-07-25T00:00:00","2022-07-26T00:00:00","2022-07-27T00:00:00","2022-07-28T00:00:00","2022-07-29T00:00:00","2022-07-30T00:00:00","2022-07-31T00:00:00","2022-08-01T00:00:00","2022-08-02T00:00:00","2022-08-03T00:00:00","2022-08-04T00:00:00","2022-08-05T00:00:00","2022-08-06T00:00:00","2022-08-07T00:00:00","2022-08-08T00:00:00","2022-08-09T00:00:00","2022-08-10T00:00:00","2022-08-11T00:00:00","2022-08-12T00:00:00","2022-08-13T00:00:00","2022-08-14T00:00:00","2022-08-15T00:00:00","2022-08-16T00:00:00","2022-08-17T00:00:00","2022-08-18T00:00:00","2022-08-19T00:00:00","2022-08-20T00:00:00","2022-08-21T00:00:00","2022-08-22T00:00:00","2022-08-23T00:00:00","2022-08-24T00:00:00","2022-08-25T00:00:00","2022-08-26T00:00:00","2022-08-27T00:00:00","2022-08-28T00:00:00","2022-08-29T00:00:00","2022-08-30T00:00:00","2022-08-31T00:00:00","2022-09-01T00:00:00","2022-09-02T00:00:00","2022-09-03T00:00:00","2022-09-04T00:00:00","2022-09-05T00:00:00","2022-09-06T00:00:00","2022-09-07T00:00:00","2022-09-08T00:00:00","2022-09-09T00:00:00","2022-09-10T00:00:00","2022-09-11T00:00:00","2022-09-12T00:00:00","2022-09-13T00:00:00","2022-09-14T00:00:00","2022-09-15T00:00:00","2022-09-16T00:00:00","2022-09-17T00:00:00","2022-09-18T00:00:00","2022-09-19T00:00:00","2022-09-20T00:00:00","2022-09-21T00:00:00","2022-09-22T00:00:00","2022-09-23T00:00:00","2022-09-24T00:00:00","2022-09-25T00:00:00","2022-09-26T00:00:00","2022-09-27T00:00:00","2022-09-28T00:00:00","2022-09-29T00:00:00","2022-09-30T00:00:00","2022-10-01T00:00:00","2022-10-02T00:00:00","2022-10-03T00:00:00","2022-10-04T00:00:00","2022-10-05T00:00:00","2022-10-06T00:00:00","2022-10-07T00:00:00","2022-10-08T00:00:00","2022-10-09T00:00:00","2022-10-10T00:00:00","2022-10-11T00:00:00","2022-10-12T00:00:00","2022-10-13T00:00:00","2022-10-14T00:00:00","2022-10-15T00:00:00","2022-10-16T00:00:00","2022-10-17T00:00:00","2022-10-18T00:00:00","2022-10-19T00:00:00","2022-10-20T00:00:00","2022-10-21T00:00:00","2022-10-22T00:00:00","2022-10-23T00:00:00","2022-10-24T00:00:00","2022-10-25T00:00:00","2022-10-26T00:00:00","2022-10-27T00:00:00","2022-10-28T00:00:00","2022-10-29T00:00:00","2022-10-30T00:00:00","2022-10-31T00:00:00","2022-11-01T00:00:00","2022-11-02T00:00:00","2022-11-03T00:00:00","2022-11-04T00:00:00","2022-11-05T00:00:00","2022-11-06T00:00:00","2022-11-07T00:00:00","2022-11-08T00:00:00","2022-11-09T00:00:00","2022-11-10T00:00:00","2022-11-11T00:00:00","2022-11-12T00:00:00","2022-11-13T00:00:00","2022-11-14T00:00:00","2022-11-15T00:00:00","2022-11-16T00:00:00","2022-11-17T00:00:00","2022-11-18T00:00:00","2022-11-19T00:00:00","2022-11-20T00:00:00","2022-11-21T00:00:00","2022-11-22T00:00:00","2022-11-23T00:00:00","2022-11-24T00:00:00","2022-11-25T00:00:00","2022-11-26T00:00:00","2022-11-27T00:00:00","2022-11-28T00:00:00","2022-11-29T00:00:00","2022-11-30T00:00:00","2022-12-01T00:00:00","2022-12-02T00:00:00","2022-12-03T00:00:00","2022-12-04T00:00:00","2022-12-05T00:00:00","2022-12-06T00:00:00","2022-12-07T00:00:00","2022-12-08T00:00:00","2022-12-09T00:00:00","2022-12-10T00:00:00","2022-12-11T00:00:00","2022-12-12T00:00:00","2022-12-13T00:00:00"],"xaxis":"x","y":[15.66,15.66,15.66,15.66,15.66,15.66,15.66,15.66,15.66,15.66,15.66,15.66,15.66,15.66,15.66,15.66,15.66,15.66,15.66,15.66,15.66,15.66,15.66,15.66,15.66,115.48,115.48,115.48,115.48,115.48,115.48,141.79,141.79,141.79,185.53,185.53,185.53,185.53,185.53,185.53,185.53,185.53,222.14,222.14,301.18,301.18,301.18,301.18,301.18,301.18,301.18,301.18,301.18,301.18,301.18,301.18,301.18,301.18,301.18,301.18,301.18,301.18,302.57,302.57,302.57,302.57,302.57,302.57,302.57,302.57,302.57,302.57,302.57,302.57,302.57,302.57,302.57,302.57,302.57,396.55,396.55,396.55,396.55,396.55,396.55,396.55,396.55,396.55,396.55,396.55,396.55,396.55,396.55,396.55,495.41,495.41,495.41,495.41,495.41,495.41,495.41,495.41,509.21,509.21,538.56,538.56,538.56,538.56,538.56,538.56,538.56,538.56,538.56,538.56,538.56,538.56,538.56,538.56,538.56,538.56,538.56,538.56,538.56,538.56,538.56,538.56,538.56,538.56,538.56,538.56,538.56,538.56,538.56,538.56,538.56,538.56,538.56,538.56,538.56,538.56,538.56,538.56,538.56,538.56,538.56,538.56,538.56,538.56,538.56,538.56,538.56,538.56,538.56,538.56,538.56,538.56,538.56,538.56,538.56,625.17,625.17,625.17,625.17,625.17,625.17,625.17,625.17,625.17,625.17,625.17,625.17,625.17,625.17,625.17,625.17,625.17,625.17,625.17,625.17,684.23,684.23,684.23,730.04,730.04,730.04,730.04,730.04,730.04,730.04,730.04,730.04,730.04,730.04,730.04,730.04,730.04,730.04,730.04,730.04,730.04,730.04,730.04,730.04,730.04,730.04,730.04,730.04,730.04,730.04,730.04,730.04,730.04,730.04,730.04,730.04,730.04,730.04,730.04,730.04,730.04,730.04,730.04,730.04,730.04,730.04,730.04,730.04,730.04,730.04,730.04,730.04,730.04,730.04,828.33,828.33,828.33,828.33,870.05,870.05,870.05,870.05,870.05,870.05,870.05,870.05,870.05,870.05,870.05,870.05,870.05,870.05,870.05,870.05,870.05,870.05,900.89,983.47,983.47,983.47,983.47,983.47,983.47,983.47,983.47,983.47,983.47,1072.8,1154.55,1154.55,1154.55,1154.55,1154.55,1154.55,1154.55,1154.55,1184.15,1184.15,1184.15,1184.15,1184.15,1184.15,1184.15,1184.15,1184.15,1184.15,1184.15,1184.15,1198.93,1198.93,1198.93,1198.93,1198.93,1198.93,1198.93,1198.93,1198.93,1198.93,1198.93,1198.93,1302.76,1302.76,1302.76,1302.76,1302.76,1302.76,1302.76,1302.76,1302.76,1302.76,1302.76,1302.76,1302.76,1302.76,1377.75,1377.75,1377.75,1377.75,1377.75,1377.75,1377.75,1377.75,1377.75,1377.75,1377.75,1377.75,1377.75,1377.75,1377.75,1377.75,1377.75,1377.75,1377.75,1377.75,1377.75,1377.75,1377.75,1377.75,1452.35,1452.35,1452.35,1452.35,1452.35,1452.35,1452.35,1452.35,1452.35,1452.35,1452.35,1452.35,1452.35,1452.35,1452.35,1452.35,1452.35,1508.79,1508.79,1508.79,1508.79,1508.79,1508.79,1508.79,1508.79,1508.79,1508.79,1508.79,1508.79,1508.79,1508.79,1508.79,1508.79,1508.79,1508.79,1508.79,1508.79,1508.79,1508.79,1508.79,1508.79,1508.79,1508.79,1508.79,1508.79,1508.79,1508.79,1508.79,1508.79,1508.79,1508.79,1508.79,1508.79,1517.06,1584.01,1584.01,1584.01,1584.01,1584.01,1584.01,1584.01,1584.01,1584.01,1584.01,1584.01,1584.01,1584.01,1584.01,1584.01,1584.01,1584.01,1584.01,1584.01,1584.01,1584.01,1584.01,1584.01,1584.01,1584.01,1584.01,1584.01,1584.01,1584.01,1584.01,1584.01,1584.01,1584.01,1584.01,1584.01,1584.01,1584.01,1674.78,1674.78,1674.78,1674.78,1674.78,1674.78,1674.78,1674.78,1674.78,1674.78,1674.78,1674.78,1674.78,1674.78,1674.78,1674.78,1674.78,1674.78,1674.78,1674.78,1674.78,1674.78,1674.78,1674.78,1674.78,1674.78,1674.78,1674.78,1674.78,1674.78,1674.78,1674.78,1674.78,1674.78,1674.78,1674.78,1674.78,1674.78,1674.78,1674.78,1674.78,1674.78,1674.78,1674.78,1674.78,1674.78,1682.54,1682.54,1682.54,1682.54,1682.54,1682.54,1682.54,1682.54,1682.54,1682.54,1682.54,1682.54,1682.54,1769.82,1769.82,1769.82,1769.82,1769.82,1769.82,1769.82,1769.82,1769.82,1769.82,1815.21,1815.21,1815.21,1815.21,1815.21,1912.83,1912.83,1912.83,1912.83,1912.83,1912.83,1912.83,2011.04,2011.04,2011.04,2011.04,2011.04,2011.04,2011.04,2011.04,2011.04,2011.04,2011.04,2054.92,2054.92,2054.92,2054.92,2054.92,2073.38,2154.96,2154.96,2154.96,2154.96,2154.96,2154.96,2154.96,2154.96,2154.96,2154.96,2154.96,2154.96,2165.45,2165.45,2165.45,2165.45,2217.09,2217.09,2217.09,2217.09,2217.09,2217.09,2217.09,2217.09,2217.09,2217.09,2217.09,2217.09,2217.09,2218.87,2218.87,2218.87,2218.87,2218.87,2218.87,2218.87,2218.87,2218.87,2218.87,2218.87,2218.87,2218.87,2218.87,2218.87,2218.87,2218.87,2218.87,2218.87,2218.87,2218.87,2218.87,2218.87,2304.62,2304.62,2373.54,2373.54,2452.49,2452.49,2452.49,2452.49,2452.49,2452.49,2452.49,2479.76,2479.76,2479.76,2479.76,2479.76,2479.76,2479.76,2479.76,2479.76,2479.76,2479.76,2479.76,2479.76,2479.76,2479.76,2479.76,2479.76,2479.76,2479.76,2479.76,2479.76,2479.76,2479.76,2479.76,2479.76,2479.76,2479.76,2479.76,2479.76,2479.76,2479.76,2479.76,2479.76,2566.32,2566.32,2652.97,2652.97,2709.77,2709.77,2709.77,2709.77,2709.77,2709.77,2709.77,2709.77,2709.77,2709.77,2709.77,2709.77,2709.77,2709.77,2709.77,2709.77,2709.77,2709.77,2709.77,2787.09,2787.09,2787.09,2787.09,2787.09,2787.09,2787.09,2853.95,2853.95,2853.95,2853.95,2853.95,2860.06,2860.06,2860.06,2860.06,2860.06,2860.06,2860.06,2860.06,2860.06,2860.06,2860.06,2860.06,2860.06,2860.06,2860.06,2860.06,2860.06,2860.06,2860.06,2860.06,2860.06,2860.06,2860.06,2860.06,2860.06,2860.06,2860.06,2868.18,2868.18,2868.18,2868.18,2868.18,2868.18,2868.18,2868.18,2868.18,2868.18,2868.18,2868.18,2868.18,2868.18,2868.18,2868.18,2868.18,2868.18,2868.18,2868.18,2868.18,2868.18,2868.18,2868.18,2868.18,2868.18,2868.18,2868.18,2868.18,2868.18,2868.18,2868.18,2959.09,2959.09,2959.09,2959.09,2959.09,2959.09,2959.09,2959.09,2959.09,2959.09,2959.09,2959.09,2959.09,2959.09,2959.09,2979.36,2979.36,2979.36,2979.36,2979.36,2979.36,3034.3,3034.3,3034.3,3034.3,3034.3,3058.22,3058.22,3058.22,3058.22,3058.22,3058.22,3058.22,3058.22,3058.22,3058.22,3058.22,3058.22,3058.22,3058.22,3141.37,3141.37,3141.37,3141.37,3141.37,3141.37,3141.37,3141.37,3141.37,3141.37,3141.37,3141.37,3141.37,3141.37,3141.37,3141.37,3141.37,3141.37,3158.6,3158.6,3158.6,3158.6,3158.6,3158.6,3158.6,3158.6,3158.6,3158.6,3158.6,3158.6,3158.6,3158.6,3158.6,3158.6,3158.6,3158.6,3158.6,3158.6,3158.6,3158.6,3158.6,3158.6,3158.6,3158.6,3158.6,3158.6,3158.6,3158.6,3158.6,3158.6,3158.6,3158.6,3237.47,3237.47,3237.47,3237.47,3237.47,3237.47,3237.47,3237.47,3237.47,3237.47,3237.47,3237.47,3237.47,3237.47,3237.47,3237.47,3237.47,3237.47,3237.47,3237.47,3237.47,3237.47,3237.47,3237.47,3237.47,3237.47,3237.47,3237.47,3237.47,3237.47,3237.47,3237.47,3237.47,3237.47,3237.47,3288.7,3306.18,3306.18,3306.18,3306.18,3306.18,3306.18,3306.18,3306.18,3306.18,3306.18,3306.18,3306.18,3306.18,3306.18,3306.18,3306.18,3306.18,3306.18,3306.18,3342.87,3342.87,3342.87,3342.87,3342.87,3342.87,3342.87,3342.87,3342.87,3342.87,3342.87,3342.87,3342.87,3342.87,3380.07,3380.07,3380.07,3380.07,3380.07,3380.07,3380.07,3380.07,3380.07,3380.07,3380.07,3380.07,3380.07,3380.07,3380.07,3406.67,3406.67,3406.67,3406.67,3406.67,3406.67,3406.67,3406.67,3406.67,3406.67,3406.67,3406.67,3406.67,3406.67,3406.67,3406.67,3406.67,3406.67,3406.67,3406.67,3406.67,3406.67,3406.67,3406.67,3406.67,3406.67,3406.67,3406.67,3406.67,3406.67,3438.27,3438.27,3438.27,3438.27,3438.27,3438.27,3438.27,3438.27,3438.27,3438.27,3438.27,3438.27,3438.27,3438.27,3438.27,3438.27,3438.27,3438.27,3438.27,3438.27,3438.27,3438.27,3438.27,3438.27,3438.27,3438.27,3438.27,3438.27,3438.27,3438.27,3438.27,3438.27,3438.27,3438.27,3438.27,3438.27,3438.27,3438.27,3438.27,3438.27,3438.27,3438.27,3438.27,3438.27,3438.27,3438.27,3438.27,3438.27,3438.27,3438.27,3438.27,3438.27,3438.27,3441.32,3441.32,3441.32,3441.32,3441.32,3441.32,3441.32,3441.32,3480.53,3480.53,3480.53,3480.53,3480.53,3480.53,3480.53,3480.53,3480.53,3480.53,3480.53,3480.53,3574.99,3574.99,3574.99,3574.99,3574.99,3574.99,3574.99,3574.99,3574.99,3574.99,3574.99,3574.99,3574.99,3574.99,3574.99,3574.99,3574.99,3574.99,3574.99,3574.99,3574.99,3574.99,3574.99,3574.99,3574.99,3574.99,3574.99,3574.99,3574.99,3574.99,3574.99,3586.35,3586.35,3586.35,3586.35,3586.35,3638.23,3638.23,3638.23,3638.23,3638.23,3638.23,3638.23,3638.23,3638.23,3638.23,3638.23,3638.23,3638.23,3638.23,3726.33,3726.33,3726.33,3726.33,3726.33,3726.33,3765.36,3765.36,3765.36,3765.36,3826.65,3826.65,3826.65,3826.65,3826.65,3826.65,3826.65,3826.65,3826.65,3826.65,3826.65,3826.65,3826.65,3826.65,3826.65,3826.65,3826.65,3826.65,3826.65,3826.65,3826.65,3826.65,3826.65],"yaxis":"y","type":"scattergl"},{"hovertemplate":"purchased_by=All<br>purchased_date=%{x}<br>Cumulative Dollars Spent=%{y}<extra></extra>","legendgroup":"All","line":{"color":"#ab63fa","dash":"solid"},"marker":{"symbol":"circle"},"mode":"lines","name":"All","showlegend":true,"x":["2020-01-01T00:00:00","2020-01-02T00:00:00","2020-01-03T00:00:00","2020-01-04T00:00:00","2020-01-05T00:00:00","2020-01-06T00:00:00","2020-01-07T00:00:00","2020-01-08T00:00:00","2020-01-09T00:00:00","2020-01-10T00:00:00","2020-01-11T00:00:00","2020-01-12T00:00:00","2020-01-13T00:00:00","2020-01-14T00:00:00","2020-01-15T00:00:00","2020-01-16T00:00:00","2020-01-17T00:00:00","2020-01-18T00:00:00","2020-01-19T00:00:00","2020-01-20T00:00:00","2020-01-21T00:00:00","2020-01-22T00:00:00","2020-01-23T00:00:00","2020-01-24T00:00:00","2020-01-25T00:00:00","2020-01-26T00:00:00","2020-01-27T00:00:00","2020-01-28T00:00:00","2020-01-29T00:00:00","2020-01-30T00:00:00","2020-01-31T00:00:00","2020-02-01T00:00:00","2020-02-02T00:00:00","2020-02-03T00:00:00","2020-02-04T00:00:00","2020-02-05T00:00:00","2020-02-06T00:00:00","2020-02-07T00:00:00","2020-02-08T00:00:00","2020-02-09T00:00:00","2020-02-10T00:00:00","2020-02-11T00:00:00","2020-02-12T00:00:00","2020-02-13T00:00:00","2020-02-14T00:00:00","2020-02-15T00:00:00","2020-02-16T00:00:00","2020-02-17T00:00:00","2020-02-18T00:00:00","2020-02-19T00:00:00","2020-02-20T00:00:00","2020-02-21T00:00:00","2020-02-22T00:00:00","2020-02-23T00:00:00","2020-02-24T00:00:00","2020-02-25T00:00:00","2020-02-26T00:00:00","2020-02-27T00:00:00","2020-02-28T00:00:00","2020-02-29T00:00:00","2020-03-01T00:00:00","2020-03-02T00:00:00","2020-03-03T00:00:00","2020-03-04T00:00:00","2020-03-05T00:00:00","2020-03-06T00:00:00","2020-03-07T00:00:00","2020-03-08T00:00:00","2020-03-09T00:00:00","2020-03-10T00:00:00","2020-03-11T00:00:00","2020-03-12T00:00:00","2020-03-13T00:00:00","2020-03-14T00:00:00","2020-03-15T00:00:00","2020-03-16T00:00:00","2020-03-17T00:00:00","2020-03-18T00:00:00","2020-03-19T00:00:00","2020-03-20T00:00:00","2020-03-21T00:00:00","2020-03-22T00:00:00","2020-03-23T00:00:00","2020-03-24T00:00:00","2020-03-25T00:00:00","2020-03-26T00:00:00","2020-03-27T00:00:00","2020-03-28T00:00:00","2020-03-29T00:00:00","2020-03-30T00:00:00","2020-03-31T00:00:00","2020-04-01T00:00:00","2020-04-02T00:00:00","2020-04-03T00:00:00","2020-04-04T00:00:00","2020-04-05T00:00:00","2020-04-06T00:00:00","2020-04-07T00:00:00","2020-04-08T00:00:00","2020-04-09T00:00:00","2020-04-10T00:00:00","2020-04-11T00:00:00","2020-04-12T00:00:00","2020-04-13T00:00:00","2020-04-14T00:00:00","2020-04-15T00:00:00","2020-04-16T00:00:00","2020-04-17T00:00:00","2020-04-18T00:00:00","2020-04-19T00:00:00","2020-04-20T00:00:00","2020-04-21T00:00:00","2020-04-22T00:00:00","2020-04-23T00:00:00","2020-04-24T00:00:00","2020-04-25T00:00:00","2020-04-26T00:00:00","2020-04-27T00:00:00","2020-04-28T00:00:00","2020-04-29T00:00:00","2020-04-30T00:00:00","2020-05-01T00:00:00","2020-05-02T00:00:00","2020-05-03T00:00:00","2020-05-04T00:00:00","2020-05-05T00:00:00","2020-05-06T00:00:00","2020-05-07T00:00:00","2020-05-08T00:00:00","2020-05-09T00:00:00","2020-05-10T00:00:00","2020-05-11T00:00:00","2020-05-12T00:00:00","2020-05-13T00:00:00","2020-05-14T00:00:00","2020-05-15T00:00:00","2020-05-16T00:00:00","2020-05-17T00:00:00","2020-05-18T00:00:00","2020-05-19T00:00:00","2020-05-20T00:00:00","2020-05-21T00:00:00","2020-05-22T00:00:00","2020-05-23T00:00:00","2020-05-24T00:00:00","2020-05-25T00:00:00","2020-05-26T00:00:00","2020-05-27T00:00:00","2020-05-28T00:00:00","2020-05-29T00:00:00","2020-05-30T00:00:00","2020-05-31T00:00:00","2020-06-01T00:00:00","2020-06-02T00:00:00","2020-06-03T00:00:00","2020-06-04T00:00:00","2020-06-05T00:00:00","2020-06-06T00:00:00","2020-06-07T00:00:00","2020-06-08T00:00:00","2020-06-09T00:00:00","2020-06-10T00:00:00","2020-06-11T00:00:00","2020-06-12T00:00:00","2020-06-13T00:00:00","2020-06-14T00:00:00","2020-06-15T00:00:00","2020-06-16T00:00:00","2020-06-17T00:00:00","2020-06-18T00:00:00","2020-06-19T00:00:00","2020-06-20T00:00:00","2020-06-21T00:00:00","2020-06-22T00:00:00","2020-06-23T00:00:00","2020-06-24T00:00:00","2020-06-25T00:00:00","2020-06-26T00:00:00","2020-06-27T00:00:00","2020-06-28T00:00:00","2020-06-29T00:00:00","2020-06-30T00:00:00","2020-07-01T00:00:00","2020-07-02T00:00:00","2020-07-03T00:00:00","2020-07-04T00:00:00","2020-07-05T00:00:00","2020-07-06T00:00:00","2020-07-07T00:00:00","2020-07-08T00:00:00","2020-07-09T00:00:00","2020-07-10T00:00:00","2020-07-11T00:00:00","2020-07-12T00:00:00","2020-07-13T00:00:00","2020-07-14T00:00:00","2020-07-15T00:00:00","2020-07-16T00:00:00","2020-07-17T00:00:00","2020-07-18T00:00:00","2020-07-19T00:00:00","2020-07-20T00:00:00","2020-07-21T00:00:00","2020-07-22T00:00:00","2020-07-23T00:00:00","2020-07-24T00:00:00","2020-07-25T00:00:00","2020-07-26T00:00:00","2020-07-27T00:00:00","2020-07-28T00:00:00","2020-07-29T00:00:00","2020-07-30T00:00:00","2020-07-31T00:00:00","2020-08-01T00:00:00","2020-08-02T00:00:00","2020-08-03T00:00:00","2020-08-04T00:00:00","2020-08-05T00:00:00","2020-08-06T00:00:00","2020-08-07T00:00:00","2020-08-08T00:00:00","2020-08-09T00:00:00","2020-08-10T00:00:00","2020-08-11T00:00:00","2020-08-12T00:00:00","2020-08-13T00:00:00","2020-08-14T00:00:00","2020-08-15T00:00:00","2020-08-16T00:00:00","2020-08-17T00:00:00","2020-08-18T00:00:00","2020-08-19T00:00:00","2020-08-20T00:00:00","2020-08-21T00:00:00","2020-08-22T00:00:00","2020-08-23T00:00:00","2020-08-24T00:00:00","2020-08-25T00:00:00","2020-08-26T00:00:00","2020-08-27T00:00:00","2020-08-28T00:00:00","2020-08-29T00:00:00","2020-08-30T00:00:00","2020-08-31T00:00:00","2020-09-01T00:00:00","2020-09-02T00:00:00","2020-09-03T00:00:00","2020-09-04T00:00:00","2020-09-05T00:00:00","2020-09-06T00:00:00","2020-09-07T00:00:00","2020-09-08T00:00:00","2020-09-09T00:00:00","2020-09-10T00:00:00","2020-09-11T00:00:00","2020-09-12T00:00:00","2020-09-13T00:00:00","2020-09-14T00:00:00","2020-09-15T00:00:00","2020-09-16T00:00:00","2020-09-17T00:00:00","2020-09-18T00:00:00","2020-09-19T00:00:00","2020-09-20T00:00:00","2020-09-21T00:00:00","2020-09-22T00:00:00","2020-09-23T00:00:00","2020-09-24T00:00:00","2020-09-25T00:00:00","2020-09-26T00:00:00","2020-09-27T00:00:00","2020-09-28T00:00:00","2020-09-29T00:00:00","2020-09-30T00:00:00","2020-10-01T00:00:00","2020-10-02T00:00:00","2020-10-03T00:00:00","2020-10-04T00:00:00","2020-10-05T00:00:00","2020-10-06T00:00:00","2020-10-07T00:00:00","2020-10-08T00:00:00","2020-10-09T00:00:00","2020-10-10T00:00:00","2020-10-11T00:00:00","2020-10-12T00:00:00","2020-10-13T00:00:00","2020-10-14T00:00:00","2020-10-15T00:00:00","2020-10-16T00:00:00","2020-10-17T00:00:00","2020-10-18T00:00:00","2020-10-19T00:00:00","2020-10-20T00:00:00","2020-10-21T00:00:00","2020-10-22T00:00:00","2020-10-23T00:00:00","2020-10-24T00:00:00","2020-10-25T00:00:00","2020-10-26T00:00:00","2020-10-27T00:00:00","2020-10-28T00:00:00","2020-10-29T00:00:00","2020-10-30T00:00:00","2020-10-31T00:00:00","2020-11-01T00:00:00","2020-11-02T00:00:00","2020-11-03T00:00:00","2020-11-04T00:00:00","2020-11-05T00:00:00","2020-11-06T00:00:00","2020-11-07T00:00:00","2020-11-08T00:00:00","2020-11-09T00:00:00","2020-11-10T00:00:00","2020-11-11T00:00:00","2020-11-12T00:00:00","2020-11-13T00:00:00","2020-11-14T00:00:00","2020-11-15T00:00:00","2020-11-16T00:00:00","2020-11-17T00:00:00","2020-11-18T00:00:00","2020-11-19T00:00:00","2020-11-20T00:00:00","2020-11-21T00:00:00","2020-11-22T00:00:00","2020-11-23T00:00:00","2020-11-24T00:00:00","2020-11-25T00:00:00","2020-11-26T00:00:00","2020-11-27T00:00:00","2020-11-28T00:00:00","2020-11-29T00:00:00","2020-11-30T00:00:00","2020-12-01T00:00:00","2020-12-02T00:00:00","2020-12-03T00:00:00","2020-12-04T00:00:00","2020-12-05T00:00:00","2020-12-06T00:00:00","2020-12-07T00:00:00","2020-12-08T00:00:00","2020-12-09T00:00:00","2020-12-10T00:00:00","2020-12-11T00:00:00","2020-12-12T00:00:00","2020-12-13T00:00:00","2020-12-14T00:00:00","2020-12-15T00:00:00","2020-12-16T00:00:00","2020-12-17T00:00:00","2020-12-18T00:00:00","2020-12-19T00:00:00","2020-12-20T00:00:00","2020-12-21T00:00:00","2020-12-22T00:00:00","2020-12-23T00:00:00","2020-12-24T00:00:00","2020-12-25T00:00:00","2020-12-26T00:00:00","2020-12-27T00:00:00","2020-12-28T00:00:00","2020-12-29T00:00:00","2020-12-30T00:00:00","2020-12-31T00:00:00","2021-01-01T00:00:00","2021-01-02T00:00:00","2021-01-03T00:00:00","2021-01-04T00:00:00","2021-01-05T00:00:00","2021-01-06T00:00:00","2021-01-07T00:00:00","2021-01-08T00:00:00","2021-01-09T00:00:00","2021-01-10T00:00:00","2021-01-11T00:00:00","2021-01-12T00:00:00","2021-01-13T00:00:00","2021-01-14T00:00:00","2021-01-15T00:00:00","2021-01-16T00:00:00","2021-01-17T00:00:00","2021-01-18T00:00:00","2021-01-19T00:00:00","2021-01-20T00:00:00","2021-01-21T00:00:00","2021-01-22T00:00:00","2021-01-23T00:00:00","2021-01-24T00:00:00","2021-01-25T00:00:00","2021-01-26T00:00:00","2021-01-27T00:00:00","2021-01-28T00:00:00","2021-01-29T00:00:00","2021-01-30T00:00:00","2021-01-31T00:00:00","2021-02-01T00:00:00","2021-02-02T00:00:00","2021-02-03T00:00:00","2021-02-04T00:00:00","2021-02-05T00:00:00","2021-02-06T00:00:00","2021-02-07T00:00:00","2021-02-08T00:00:00","2021-02-09T00:00:00","2021-02-10T00:00:00","2021-02-11T00:00:00","2021-02-12T00:00:00","2021-02-13T00:00:00","2021-02-14T00:00:00","2021-02-15T00:00:00","2021-02-16T00:00:00","2021-02-17T00:00:00","2021-02-18T00:00:00","2021-02-19T00:00:00","2021-02-20T00:00:00","2021-02-21T00:00:00","2021-02-22T00:00:00","2021-02-23T00:00:00","2021-02-24T00:00:00","2021-02-25T00:00:00","2021-02-26T00:00:00","2021-02-27T00:00:00","2021-02-28T00:00:00","2021-03-01T00:00:00","2021-03-02T00:00:00","2021-03-03T00:00:00","2021-03-04T00:00:00","2021-03-05T00:00:00","2021-03-06T00:00:00","2021-03-07T00:00:00","2021-03-08T00:00:00","2021-03-09T00:00:00","2021-03-10T00:00:00","2021-03-11T00:00:00","2021-03-12T00:00:00","2021-03-13T00:00:00","2021-03-14T00:00:00","2021-03-15T00:00:00","2021-03-16T00:00:00","2021-03-17T00:00:00","2021-03-18T00:00:00","2021-03-19T00:00:00","2021-03-20T00:00:00","2021-03-21T00:00:00","2021-03-22T00:00:00","2021-03-23T00:00:00","2021-03-24T00:00:00","2021-03-25T00:00:00","2021-03-26T00:00:00","2021-03-27T00:00:00","2021-03-28T00:00:00","2021-03-29T00:00:00","2021-03-30T00:00:00","2021-03-31T00:00:00","2021-04-01T00:00:00","2021-04-02T00:00:00","2021-04-03T00:00:00","2021-04-04T00:00:00","2021-04-05T00:00:00","2021-04-06T00:00:00","2021-04-07T00:00:00","2021-04-08T00:00:00","2021-04-09T00:00:00","2021-04-10T00:00:00","2021-04-11T00:00:00","2021-04-12T00:00:00","2021-04-13T00:00:00","2021-04-14T00:00:00","2021-04-15T00:00:00","2021-04-16T00:00:00","2021-04-17T00:00:00","2021-04-18T00:00:00","2021-04-19T00:00:00","2021-04-20T00:00:00","2021-04-21T00:00:00","2021-04-22T00:00:00","2021-04-23T00:00:00","2021-04-24T00:00:00","2021-04-25T00:00:00","2021-04-26T00:00:00","2021-04-27T00:00:00","2021-04-28T00:00:00","2021-04-29T00:00:00","2021-04-30T00:00:00","2021-05-01T00:00:00","2021-05-02T00:00:00","2021-05-03T00:00:00","2021-05-04T00:00:00","2021-05-05T00:00:00","2021-05-06T00:00:00","2021-05-07T00:00:00","2021-05-08T00:00:00","2021-05-09T00:00:00","2021-05-10T00:00:00","2021-05-11T00:00:00","2021-05-12T00:00:00","2021-05-13T00:00:00","2021-05-14T00:00:00","2021-05-15T00:00:00","2021-05-16T00:00:00","2021-05-17T00:00:00","2021-05-18T00:00:00","2021-05-19T00:00:00","2021-05-20T00:00:00","2021-05-21T00:00:00","2021-05-22T00:00:00","2021-05-23T00:00:00","2021-05-24T00:00:00","2021-05-25T00:00:00","2021-05-26T00:00:00","2021-05-27T00:00:00","2021-05-28T00:00:00","2021-05-29T00:00:00","2021-05-30T00:00:00","2021-05-31T00:00:00","2021-06-01T00:00:00","2021-06-02T00:00:00","2021-06-03T00:00:00","2021-06-04T00:00:00","2021-06-05T00:00:00","2021-06-06T00:00:00","2021-06-07T00:00:00","2021-06-08T00:00:00","2021-06-09T00:00:00","2021-06-10T00:00:00","2021-06-11T00:00:00","2021-06-12T00:00:00","2021-06-13T00:00:00","2021-06-14T00:00:00","2021-06-15T00:00:00","2021-06-16T00:00:00","2021-06-17T00:00:00","2021-06-18T00:00:00","2021-06-19T00:00:00","2021-06-20T00:00:00","2021-06-21T00:00:00","2021-06-22T00:00:00","2021-06-23T00:00:00","2021-06-24T00:00:00","2021-06-25T00:00:00","2021-06-26T00:00:00","2021-06-27T00:00:00","2021-06-28T00:00:00","2021-06-29T00:00:00","2021-06-30T00:00:00","2021-07-01T00:00:00","2021-07-02T00:00:00","2021-07-03T00:00:00","2021-07-04T00:00:00","2021-07-05T00:00:00","2021-07-06T00:00:00","2021-07-07T00:00:00","2021-07-08T00:00:00","2021-07-09T00:00:00","2021-07-10T00:00:00","2021-07-11T00:00:00","2021-07-12T00:00:00","2021-07-13T00:00:00","2021-07-14T00:00:00","2021-07-15T00:00:00","2021-07-16T00:00:00","2021-07-17T00:00:00","2021-07-18T00:00:00","2021-07-19T00:00:00","2021-07-20T00:00:00","2021-07-21T00:00:00","2021-07-22T00:00:00","2021-07-23T00:00:00","2021-07-24T00:00:00","2021-07-25T00:00:00","2021-07-26T00:00:00","2021-07-27T00:00:00","2021-07-28T00:00:00","2021-07-29T00:00:00","2021-07-30T00:00:00","2021-07-31T00:00:00","2021-08-01T00:00:00","2021-08-02T00:00:00","2021-08-03T00:00:00","2021-08-04T00:00:00","2021-08-05T00:00:00","2021-08-06T00:00:00","2021-08-07T00:00:00","2021-08-08T00:00:00","2021-08-09T00:00:00","2021-08-10T00:00:00","2021-08-11T00:00:00","2021-08-12T00:00:00","2021-08-13T00:00:00","2021-08-14T00:00:00","2021-08-15T00:00:00","2021-08-16T00:00:00","2021-08-17T00:00:00","2021-08-18T00:00:00","2021-08-19T00:00:00","2021-08-20T00:00:00","2021-08-21T00:00:00","2021-08-22T00:00:00","2021-08-23T00:00:00","2021-08-24T00:00:00","2021-08-25T00:00:00","2021-08-26T00:00:00","2021-08-27T00:00:00","2021-08-28T00:00:00","2021-08-29T00:00:00","2021-08-30T00:00:00","2021-08-31T00:00:00","2021-09-01T00:00:00","2021-09-02T00:00:00","2021-09-03T00:00:00","2021-09-04T00:00:00","2021-09-05T00:00:00","2021-09-06T00:00:00","2021-09-07T00:00:00","2021-09-08T00:00:00","2021-09-09T00:00:00","2021-09-10T00:00:00","2021-09-11T00:00:00","2021-09-12T00:00:00","2021-09-13T00:00:00","2021-09-14T00:00:00","2021-09-15T00:00:00","2021-09-16T00:00:00","2021-09-17T00:00:00","2021-09-18T00:00:00","2021-09-19T00:00:00","2021-09-20T00:00:00","2021-09-21T00:00:00","2021-09-22T00:00:00","2021-09-23T00:00:00","2021-09-24T00:00:00","2021-09-25T00:00:00","2021-09-26T00:00:00","2021-09-27T00:00:00","2021-09-28T00:00:00","2021-09-29T00:00:00","2021-09-30T00:00:00","2021-10-01T00:00:00","2021-10-02T00:00:00","2021-10-03T00:00:00","2021-10-04T00:00:00","2021-10-05T00:00:00","2021-10-06T00:00:00","2021-10-07T00:00:00","2021-10-08T00:00:00","2021-10-09T00:00:00","2021-10-10T00:00:00","2021-10-11T00:00:00","2021-10-12T00:00:00","2021-10-13T00:00:00","2021-10-14T00:00:00","2021-10-15T00:00:00","2021-10-16T00:00:00","2021-10-17T00:00:00","2021-10-18T00:00:00","2021-10-19T00:00:00","2021-10-20T00:00:00","2021-10-21T00:00:00","2021-10-22T00:00:00","2021-10-23T00:00:00","2021-10-24T00:00:00","2021-10-25T00:00:00","2021-10-26T00:00:00","2021-10-27T00:00:00","2021-10-28T00:00:00","2021-10-29T00:00:00","2021-10-30T00:00:00","2021-10-31T00:00:00","2021-11-01T00:00:00","2021-11-02T00:00:00","2021-11-03T00:00:00","2021-11-04T00:00:00","2021-11-05T00:00:00","2021-11-06T00:00:00","2021-11-07T00:00:00","2021-11-08T00:00:00","2021-11-09T00:00:00","2021-11-10T00:00:00","2021-11-11T00:00:00","2021-11-12T00:00:00","2021-11-13T00:00:00","2021-11-14T00:00:00","2021-11-15T00:00:00","2021-11-16T00:00:00","2021-11-17T00:00:00","2021-11-18T00:00:00","2021-11-19T00:00:00","2021-11-20T00:00:00","2021-11-21T00:00:00","2021-11-22T00:00:00","2021-11-23T00:00:00","2021-11-24T00:00:00","2021-11-25T00:00:00","2021-11-26T00:00:00","2021-11-27T00:00:00","2021-11-28T00:00:00","2021-11-29T00:00:00","2021-11-30T00:00:00","2021-12-01T00:00:00","2021-12-02T00:00:00","2021-12-03T00:00:00","2021-12-04T00:00:00","2021-12-05T00:00:00","2021-12-06T00:00:00","2021-12-07T00:00:00","2021-12-08T00:00:00","2021-12-09T00:00:00","2021-12-10T00:00:00","2021-12-11T00:00:00","2021-12-12T00:00:00","2021-12-13T00:00:00","2021-12-14T00:00:00","2021-12-15T00:00:00","2021-12-16T00:00:00","2021-12-17T00:00:00","2021-12-18T00:00:00","2021-12-19T00:00:00","2021-12-20T00:00:00","2021-12-21T00:00:00","2021-12-22T00:00:00","2021-12-23T00:00:00","2021-12-24T00:00:00","2021-12-25T00:00:00","2021-12-26T00:00:00","2021-12-27T00:00:00","2021-12-28T00:00:00","2021-12-29T00:00:00","2021-12-30T00:00:00","2021-12-31T00:00:00","2022-01-01T00:00:00","2022-01-02T00:00:00","2022-01-03T00:00:00","2022-01-04T00:00:00","2022-01-05T00:00:00","2022-01-06T00:00:00","2022-01-07T00:00:00","2022-01-08T00:00:00","2022-01-09T00:00:00","2022-01-10T00:00:00","2022-01-11T00:00:00","2022-01-12T00:00:00","2022-01-13T00:00:00","2022-01-14T00:00:00","2022-01-15T00:00:00","2022-01-16T00:00:00","2022-01-17T00:00:00","2022-01-18T00:00:00","2022-01-19T00:00:00","2022-01-20T00:00:00","2022-01-21T00:00:00","2022-01-22T00:00:00","2022-01-23T00:00:00","2022-01-24T00:00:00","2022-01-25T00:00:00","2022-01-26T00:00:00","2022-01-27T00:00:00","2022-01-28T00:00:00","2022-01-29T00:00:00","2022-01-30T00:00:00","2022-01-31T00:00:00","2022-02-01T00:00:00","2022-02-02T00:00:00","2022-02-03T00:00:00","2022-02-04T00:00:00","2022-02-05T00:00:00","2022-02-06T00:00:00","2022-02-07T00:00:00","2022-02-08T00:00:00","2022-02-09T00:00:00","2022-02-10T00:00:00","2022-02-11T00:00:00","2022-02-12T00:00:00","2022-02-13T00:00:00","2022-02-14T00:00:00","2022-02-15T00:00:00","2022-02-16T00:00:00","2022-02-17T00:00:00","2022-02-18T00:00:00","2022-02-19T00:00:00","2022-02-20T00:00:00","2022-02-21T00:00:00","2022-02-22T00:00:00","2022-02-23T00:00:00","2022-02-24T00:00:00","2022-02-25T00:00:00","2022-02-26T00:00:00","2022-02-27T00:00:00","2022-02-28T00:00:00","2022-03-01T00:00:00","2022-03-02T00:00:00","2022-03-03T00:00:00","2022-03-04T00:00:00","2022-03-05T00:00:00","2022-03-06T00:00:00","2022-03-07T00:00:00","2022-03-08T00:00:00","2022-03-09T00:00:00","2022-03-10T00:00:00","2022-03-11T00:00:00","2022-03-12T00:00:00","2022-03-13T00:00:00","2022-03-14T00:00:00","2022-03-15T00:00:00","2022-03-16T00:00:00","2022-03-17T00:00:00","2022-03-18T00:00:00","2022-03-19T00:00:00","2022-03-20T00:00:00","2022-03-21T00:00:00","2022-03-22T00:00:00","2022-03-23T00:00:00","2022-03-24T00:00:00","2022-03-25T00:00:00","2022-03-26T00:00:00","2022-03-27T00:00:00","2022-03-28T00:00:00","2022-03-29T00:00:00","2022-03-30T00:00:00","2022-03-31T00:00:00","2022-04-01T00:00:00","2022-04-02T00:00:00","2022-04-03T00:00:00","2022-04-04T00:00:00","2022-04-05T00:00:00","2022-04-06T00:00:00","2022-04-07T00:00:00","2022-04-08T00:00:00","2022-04-09T00:00:00","2022-04-10T00:00:00","2022-04-11T00:00:00","2022-04-12T00:00:00","2022-04-13T00:00:00","2022-04-14T00:00:00","2022-04-15T00:00:00","2022-04-16T00:00:00","2022-04-17T00:00:00","2022-04-18T00:00:00","2022-04-19T00:00:00","2022-04-20T00:00:00","2022-04-21T00:00:00","2022-04-22T00:00:00","2022-04-23T00:00:00","2022-04-24T00:00:00","2022-04-25T00:00:00","2022-04-26T00:00:00","2022-04-27T00:00:00","2022-04-28T00:00:00","2022-04-29T00:00:00","2022-04-30T00:00:00","2022-05-01T00:00:00","2022-05-02T00:00:00","2022-05-03T00:00:00","2022-05-04T00:00:00","2022-05-05T00:00:00","2022-05-06T00:00:00","2022-05-07T00:00:00","2022-05-08T00:00:00","2022-05-09T00:00:00","2022-05-10T00:00:00","2022-05-11T00:00:00","2022-05-12T00:00:00","2022-05-13T00:00:00","2022-05-14T00:00:00","2022-05-15T00:00:00","2022-05-16T00:00:00","2022-05-17T00:00:00","2022-05-18T00:00:00","2022-05-19T00:00:00","2022-05-20T00:00:00","2022-05-21T00:00:00","2022-05-22T00:00:00","2022-05-23T00:00:00","2022-05-24T00:00:00","2022-05-25T00:00:00","2022-05-26T00:00:00","2022-05-27T00:00:00","2022-05-28T00:00:00","2022-05-29T00:00:00","2022-05-30T00:00:00","2022-05-31T00:00:00","2022-06-01T00:00:00","2022-06-02T00:00:00","2022-06-03T00:00:00","2022-06-04T00:00:00","2022-06-05T00:00:00","2022-06-06T00:00:00","2022-06-07T00:00:00","2022-06-08T00:00:00","2022-06-09T00:00:00","2022-06-10T00:00:00","2022-06-11T00:00:00","2022-06-12T00:00:00","2022-06-13T00:00:00","2022-06-14T00:00:00","2022-06-15T00:00:00","2022-06-16T00:00:00","2022-06-17T00:00:00","2022-06-18T00:00:00","2022-06-19T00:00:00","2022-06-20T00:00:00","2022-06-21T00:00:00","2022-06-22T00:00:00","2022-06-23T00:00:00","2022-06-24T00:00:00","2022-06-25T00:00:00","2022-06-26T00:00:00","2022-06-27T00:00:00","2022-06-28T00:00:00","2022-06-29T00:00:00","2022-06-30T00:00:00","2022-07-01T00:00:00","2022-07-02T00:00:00","2022-07-03T00:00:00","2022-07-04T00:00:00","2022-07-05T00:00:00","2022-07-06T00:00:00","2022-07-07T00:00:00","2022-07-08T00:00:00","2022-07-09T00:00:00","2022-07-10T00:00:00","2022-07-11T00:00:00","2022-07-12T00:00:00","2022-07-13T00:00:00","2022-07-14T00:00:00","2022-07-15T00:00:00","2022-07-16T00:00:00","2022-07-17T00:00:00","2022-07-18T00:00:00","2022-07-19T00:00:00","2022-07-20T00:00:00","2022-07-21T00:00:00","2022-07-22T00:00:00","2022-07-23T00:00:00","2022-07-24T00:00:00","2022-07-25T00:00:00","2022-07-26T00:00:00","2022-07-27T00:00:00","2022-07-28T00:00:00","2022-07-29T00:00:00","2022-07-30T00:00:00","2022-07-31T00:00:00","2022-08-01T00:00:00","2022-08-02T00:00:00","2022-08-03T00:00:00","2022-08-04T00:00:00","2022-08-05T00:00:00","2022-08-06T00:00:00","2022-08-07T00:00:00","2022-08-08T00:00:00","2022-08-09T00:00:00","2022-08-10T00:00:00","2022-08-11T00:00:00","2022-08-12T00:00:00","2022-08-13T00:00:00","2022-08-14T00:00:00","2022-08-15T00:00:00","2022-08-16T00:00:00","2022-08-17T00:00:00","2022-08-18T00:00:00","2022-08-19T00:00:00","2022-08-20T00:00:00","2022-08-21T00:00:00","2022-08-22T00:00:00","2022-08-23T00:00:00","2022-08-24T00:00:00","2022-08-25T00:00:00","2022-08-26T00:00:00","2022-08-27T00:00:00","2022-08-28T00:00:00","2022-08-29T00:00:00","2022-08-30T00:00:00","2022-08-31T00:00:00","2022-09-01T00:00:00","2022-09-02T00:00:00","2022-09-03T00:00:00","2022-09-04T00:00:00","2022-09-05T00:00:00","2022-09-06T00:00:00","2022-09-07T00:00:00","2022-09-08T00:00:00","2022-09-09T00:00:00","2022-09-10T00:00:00","2022-09-11T00:00:00","2022-09-12T00:00:00","2022-09-13T00:00:00","2022-09-14T00:00:00","2022-09-15T00:00:00","2022-09-16T00:00:00","2022-09-17T00:00:00","2022-09-18T00:00:00","2022-09-19T00:00:00","2022-09-20T00:00:00","2022-09-21T00:00:00","2022-09-22T00:00:00","2022-09-23T00:00:00","2022-09-24T00:00:00","2022-09-25T00:00:00","2022-09-26T00:00:00","2022-09-27T00:00:00","2022-09-28T00:00:00","2022-09-29T00:00:00","2022-09-30T00:00:00","2022-10-01T00:00:00","2022-10-02T00:00:00","2022-10-03T00:00:00","2022-10-04T00:00:00","2022-10-05T00:00:00","2022-10-06T00:00:00","2022-10-07T00:00:00","2022-10-08T00:00:00","2022-10-09T00:00:00","2022-10-10T00:00:00","2022-10-11T00:00:00","2022-10-12T00:00:00","2022-10-13T00:00:00","2022-10-14T00:00:00","2022-10-15T00:00:00","2022-10-16T00:00:00","2022-10-17T00:00:00","2022-10-18T00:00:00","2022-10-19T00:00:00","2022-10-20T00:00:00","2022-10-21T00:00:00","2022-10-22T00:00:00","2022-10-23T00:00:00","2022-10-24T00:00:00","2022-10-25T00:00:00","2022-10-26T00:00:00","2022-10-27T00:00:00","2022-10-28T00:00:00","2022-10-29T00:00:00","2022-10-30T00:00:00","2022-10-31T00:00:00","2022-11-01T00:00:00","2022-11-02T00:00:00","2022-11-03T00:00:00","2022-11-04T00:00:00","2022-11-05T00:00:00","2022-11-06T00:00:00","2022-11-07T00:00:00","2022-11-08T00:00:00","2022-11-09T00:00:00","2022-11-10T00:00:00","2022-11-11T00:00:00","2022-11-12T00:00:00","2022-11-13T00:00:00","2022-11-14T00:00:00","2022-11-15T00:00:00","2022-11-16T00:00:00","2022-11-17T00:00:00","2022-11-18T00:00:00","2022-11-19T00:00:00","2022-11-20T00:00:00","2022-11-21T00:00:00","2022-11-22T00:00:00","2022-11-23T00:00:00","2022-11-24T00:00:00","2022-11-25T00:00:00","2022-11-26T00:00:00","2022-11-27T00:00:00","2022-11-28T00:00:00","2022-11-29T00:00:00","2022-11-30T00:00:00","2022-12-01T00:00:00","2022-12-02T00:00:00","2022-12-03T00:00:00","2022-12-04T00:00:00","2022-12-05T00:00:00","2022-12-06T00:00:00","2022-12-07T00:00:00","2022-12-08T00:00:00","2022-12-09T00:00:00","2022-12-10T00:00:00","2022-12-11T00:00:00","2022-12-12T00:00:00","2022-12-13T00:00:00"],"xaxis":"x","y":[15.66,15.66,15.66,15.66,15.66,15.66,15.66,15.66,15.66,15.66,15.66,15.66,15.66,15.66,15.66,15.66,15.66,15.66,15.66,86.38,86.38,86.38,86.38,86.38,86.38,186.2,186.2,186.2,186.2,186.2,186.2,212.51,212.51,212.51,256.25,256.25,256.25,256.25,256.25,256.25,256.25,256.25,292.86,292.86,371.9,371.9,371.9,371.9,371.9,371.9,371.9,371.9,371.9,371.9,371.9,371.9,371.9,371.9,371.9,371.9,436.12,436.12,484.91,484.91,484.91,484.91,484.91,484.91,484.91,484.91,484.91,570.11,570.11,570.11,570.11,570.11,570.11,570.11,570.11,664.09,664.09,664.09,664.09,664.09,664.09,664.09,664.09,711.47,711.47,711.47,711.47,711.47,711.47,711.47,810.33,810.33,810.33,810.33,810.33,810.33,810.33,810.33,824.13,824.13,853.48,853.48,853.48,853.48,853.48,853.48,853.48,853.48,853.48,853.48,853.48,853.48,853.48,922.66,922.66,922.66,922.66,922.66,922.66,922.66,922.66,922.66,922.66,922.66,922.66,922.66,922.66,922.66,985.49,1011.77,1097.67,1097.67,1097.67,1097.67,1097.67,1097.67,1097.67,1097.67,1097.67,1097.67,1097.67,1097.67,1097.67,1144.51,1238.52,1238.52,1238.52,1238.52,1238.52,1238.52,1238.52,1318.74,1318.74,1318.74,1318.74,1405.35,1405.35,1405.35,1405.35,1405.35,1405.35,1405.35,1405.35,1405.35,1405.35,1405.35,1405.35,1405.35,1405.35,1405.35,1405.35,1405.35,1493.97,1493.97,1493.97,1553.03,1553.03,1553.03,1662.78,1662.78,1662.78,1662.78,1662.78,1662.78,1662.78,1711.64,1711.64,1711.64,1711.64,1711.64,1711.64,1711.64,1711.64,1711.64,1732.49,1732.49,1732.49,1732.49,1732.49,1732.49,1732.49,1732.49,1732.49,1732.49,1732.49,1732.49,1732.49,1732.49,1732.49,1732.49,1732.49,1732.49,1732.49,1732.49,1732.49,1732.49,1732.49,1732.49,1743.87,1743.87,1839.99,1839.99,1839.99,1839.99,1839.99,1839.99,1839.99,1839.99,1839.99,1938.28,1938.28,1938.28,1938.28,1980.0,1980.0,2022.53,2022.53,2022.53,2022.53,2022.53,2022.53,2022.53,2022.53,2022.53,2022.53,2036.26,2092.82,2092.82,2092.82,2178.86,2178.86,2209.7,2292.28,2292.28,2292.28,2292.28,2292.28,2292.28,2292.28,2292.28,2292.28,2376.16,2465.49,2547.24,2547.24,2547.24,2547.24,2547.24,2547.24,2547.24,2596.49,2626.09,2626.09,2626.09,2626.09,2626.09,2626.09,2626.09,2700.85,2700.85,2700.85,2700.85,2700.85,2805.99,2805.99,2805.99,2805.99,2805.99,2805.99,2818.02,2818.02,2818.02,2843.86,2843.86,2843.86,2947.69,2947.69,2947.69,2947.69,2947.69,2947.69,2947.69,2947.69,2947.69,2947.69,2947.69,3010.82,3010.82,3010.82,3085.81,3085.81,3085.81,3085.81,3085.81,3085.81,3085.81,3085.81,3085.81,3085.81,3085.81,3085.81,3085.81,3085.81,3120.88,3120.88,3120.88,3120.88,3120.88,3120.88,3120.88,3120.88,3120.88,3199.14,3273.74,3273.74,3273.74,3273.74,3273.74,3273.74,3273.74,3319.76,3319.76,3319.76,3319.76,3319.76,3319.76,3319.76,3319.76,3319.76,3319.76,3376.2,3377.8,3377.8,3421.4,3421.4,3421.4,3421.4,3482.79,3482.79,3482.79,3482.79,3482.79,3482.79,3482.79,3482.79,3482.79,3482.79,3482.79,3482.79,3482.79,3482.79,3488.51,3488.51,3488.51,3488.51,3488.51,3488.51,3488.51,3543.04,3543.04,3543.04,3543.04,3569.12,3569.12,3569.12,3569.12,3577.39,3644.34,3644.34,3644.34,3644.34,3644.34,3644.34,3644.34,3644.34,3644.34,3644.34,3644.34,3644.34,3644.34,3644.34,3644.34,3644.34,3644.34,3658.82,3658.82,3658.82,3723.58,3723.58,3723.58,3723.58,3723.58,3723.58,3723.58,3723.58,3723.58,3723.58,3723.58,3723.58,3723.58,3808.26,3808.26,3808.26,3808.26,3899.03,3899.03,3899.03,3899.03,3914.64,3914.64,3914.64,3914.64,4012.5,4012.5,4012.5,4012.5,4012.5,4012.5,4012.5,4012.5,4012.5,4018.17,4018.17,4018.17,4018.17,4018.17,4061.53,4061.53,4061.53,4061.53,4061.53,4061.53,4061.53,4061.53,4061.53,4061.53,4061.53,4061.53,4061.53,4061.53,4061.53,4061.53,4137.41,4137.41,4137.41,4137.41,4137.41,4137.41,4206.46,4206.46,4214.22,4214.22,4214.22,4214.22,4214.22,4214.22,4214.22,4214.22,4214.22,4214.22,4214.22,4214.22,4214.22,4301.5,4301.5,4335.02,4335.02,4335.02,4335.02,4335.02,4335.02,4335.02,4370.68,4416.07,4416.07,4416.07,4416.07,4416.07,4513.69,4513.69,4513.69,4513.69,4513.69,4513.69,4520.8,4619.01,4619.01,4619.01,4619.01,4619.01,4619.01,4619.01,4619.01,4619.01,4619.01,4619.01,4662.89,4727.07,4727.07,4727.07,4727.07,4745.53,4827.11,4827.11,4827.11,4827.11,4906.42,4906.42,4906.42,4906.42,4906.42,4906.42,4906.42,4906.42,4916.91,4916.91,4916.91,4916.91,4968.55,4968.55,4968.55,4968.55,4968.55,4968.55,4968.55,4968.55,5078.65,5078.65,5078.65,5078.65,5078.65,5080.43,5080.43,5080.43,5080.43,5080.43,5080.43,5166.68,5166.68,5166.68,5166.68,5166.68,5166.68,5166.68,5166.68,5284.83,5284.83,5284.83,5284.83,5284.83,5284.83,5284.83,5284.83,5284.83,5370.58,5370.58,5439.5,5439.5,5518.45,5518.45,5583.72,5583.72,5583.72,5583.72,5618.17,5645.44,5645.44,5645.44,5645.44,5645.44,5645.44,5645.44,5645.44,5645.44,5645.44,5709.13,5709.13,5709.13,5709.13,5709.13,5709.13,5709.13,5709.13,5709.13,5709.13,5793.25,5793.25,5793.25,5793.25,5841.75,5841.75,5841.75,5841.75,5841.75,5881.84,5881.84,5881.84,5881.84,5968.4,6107.93,6194.58,6194.58,6331.42,6331.42,6331.42,6331.42,6331.42,6331.42,6331.42,6331.42,6331.42,6331.42,6331.42,6331.42,6331.42,6331.42,6331.42,6331.42,6332.37,6332.37,6332.37,6409.69,6409.69,6409.69,6409.69,6409.69,6409.69,6454.62,6521.48,6521.48,6521.48,6521.48,6521.48,6567.18,6567.18,6567.18,6567.18,6567.18,6567.18,6567.18,6567.18,6567.18,6567.18,6567.18,6567.18,6567.18,6567.18,6567.18,6567.18,6567.18,6567.18,6567.18,6567.18,6567.18,6567.18,6567.18,6567.18,6567.18,6567.18,6648.15,6656.27,6656.27,6656.27,6727.95,6799.8,6799.8,6799.8,6799.8,6799.8,6799.8,6799.8,6847.26,6847.26,6847.26,6847.26,6847.26,6847.26,6847.26,6847.26,6847.26,6847.26,6926.16,6926.16,6926.16,6960.97,6960.97,6960.97,6960.97,6960.97,6960.97,6960.97,6960.97,7051.88,7051.88,7051.88,7051.88,7051.88,7051.88,7051.88,7106.65,7106.65,7106.65,7106.65,7106.65,7106.65,7106.65,7106.65,7126.92,7126.92,7126.92,7126.92,7126.92,7126.92,7181.86,7342.68,7342.68,7342.68,7342.68,7366.6,7428.12,7474.27,7474.27,7474.27,7474.27,7474.27,7474.27,7474.27,7474.27,7474.27,7474.27,7474.27,7474.27,7557.42,7557.42,7557.42,7557.42,7557.42,7557.42,7557.42,7557.42,7557.42,7557.42,7557.42,7557.42,7557.42,7557.42,7557.42,7557.42,7557.42,7557.42,7574.65,7574.65,7574.65,7656.89,7656.89,7656.89,7656.89,7656.89,7656.89,7656.89,7745.76,7745.76,7745.76,7745.76,7745.76,7745.76,7863.28,7863.28,7918.83,7918.83,7918.83,7918.83,7918.83,7918.83,7918.83,7918.83,7918.83,7918.83,7918.83,7918.83,7918.83,7918.83,7918.83,7918.83,7997.7,7997.7,8066.87,8101.48,8101.48,8101.48,8101.48,8101.48,8101.48,8113.39,8113.39,8113.39,8113.39,8113.39,8113.39,8113.39,8113.39,8113.39,8113.39,8187.32,8187.32,8187.32,8248.97,8248.97,8248.97,8248.97,8264.11,8264.11,8264.11,8264.11,8264.11,8264.11,8264.11,8264.11,8264.11,8371.26,8388.74,8388.74,8388.74,8388.74,8388.74,8388.74,8388.74,8388.74,8388.74,8388.74,8388.74,8388.74,8388.74,8388.74,8388.74,8388.74,8388.74,8388.74,8388.74,8464.48,8464.48,8464.48,8464.48,8464.48,8464.48,8464.48,8464.48,8464.48,8464.48,8464.48,8522.33,8522.33,8522.33,8622.8,8622.8,8622.8,8622.8,8622.8,8622.8,8622.8,8622.8,8622.8,8622.8,8622.8,8622.8,8622.8,8622.8,8622.8,8649.4,8649.4,8649.4,8649.4,8649.4,8649.4,8649.4,8649.4,8649.4,8649.4,8649.4,8696.21,8696.21,8696.21,8696.21,8696.21,8696.21,8696.21,8696.21,8696.21,8696.21,8696.21,8696.21,8696.21,8696.21,8696.21,8696.21,8696.21,8696.21,8696.21,8727.81,8727.81,8850.24,8945.07,8945.07,8945.07,8945.07,8992.78,8992.78,8992.78,9015.91,9015.91,9015.91,9015.91,9015.91,9015.91,9099.62,9099.62,9099.62,9099.62,9099.62,9099.62,9099.62,9188.62,9188.62,9188.62,9188.62,9188.62,9188.62,9265.19,9265.19,9265.19,9265.19,9265.19,9265.19,9265.19,9265.19,9265.19,9265.19,9265.19,9265.19,9265.19,9265.19,9265.19,9265.19,9265.19,9265.19,9265.19,9265.19,9265.19,9265.19,9265.19,9265.19,9268.24,9268.24,9268.24,9268.24,9268.24,9268.24,9268.24,9290.75,9329.96,9393.64,9455.12,9455.12,9455.12,9455.12,9455.12,9455.12,9484.04,9484.04,9484.04,9484.04,9578.5,9578.5,9578.5,9578.5,9578.5,9578.5,9578.5,9578.5,9578.5,9636.52,9636.52,9636.52,9636.52,9636.52,9636.52,9636.52,9636.52,9636.52,9636.52,9636.52,9636.52,9636.52,9636.52,9636.52,9636.52,9636.52,9636.52,9636.52,9636.52,9636.52,9636.52,9647.88,9675.84,9675.84,9768.79,9768.79,9820.67,9820.67,9820.67,9820.67,9820.67,9820.67,9820.67,9823.14,9823.14,9823.14,9823.14,9823.14,9823.14,9823.14,9911.24,9911.24,9969.26,9969.26,9969.26,9969.26,10008.29,10008.29,10008.29,10067.22,10128.51,10128.51,10128.51,10128.51,10128.51,10128.51,10128.51,10128.51,10128.51,10128.51,10128.51,10128.51,10128.51,10128.51,10128.51,10136.7,10152.88,10152.88,10152.88,10215.75,10215.75,10315.0,10411.62],"yaxis":"y","type":"scattergl"}],                        {"template":{"data":{"bar":[{"error_x":{"color":"#2a3f5f"},"error_y":{"color":"#2a3f5f"},"marker":{"line":{"color":"#E5ECF6","width":0.5},"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"bar"}],"barpolar":[{"marker":{"line":{"color":"#E5ECF6","width":0.5},"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"barpolar"}],"carpet":[{"aaxis":{"endlinecolor":"#2a3f5f","gridcolor":"white","linecolor":"white","minorgridcolor":"white","startlinecolor":"#2a3f5f"},"baxis":{"endlinecolor":"#2a3f5f","gridcolor":"white","linecolor":"white","minorgridcolor":"white","startlinecolor":"#2a3f5f"},"type":"carpet"}],"choropleth":[{"colorbar":{"outlinewidth":0,"ticks":""},"type":"choropleth"}],"contour":[{"colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"type":"contour"}],"contourcarpet":[{"colorbar":{"outlinewidth":0,"ticks":""},"type":"contourcarpet"}],"heatmap":[{"colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"type":"heatmap"}],"heatmapgl":[{"colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"type":"heatmapgl"}],"histogram":[{"marker":{"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"histogram"}],"histogram2d":[{"colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"type":"histogram2d"}],"histogram2dcontour":[{"colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"type":"histogram2dcontour"}],"mesh3d":[{"colorbar":{"outlinewidth":0,"ticks":""},"type":"mesh3d"}],"parcoords":[{"line":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"parcoords"}],"pie":[{"automargin":true,"type":"pie"}],"scatter":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scatter"}],"scatter3d":[{"line":{"colorbar":{"outlinewidth":0,"ticks":""}},"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scatter3d"}],"scattercarpet":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scattercarpet"}],"scattergeo":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scattergeo"}],"scattergl":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scattergl"}],"scattermapbox":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scattermapbox"}],"scatterpolar":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scatterpolar"}],"scatterpolargl":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scatterpolargl"}],"scatterternary":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scatterternary"}],"surface":[{"colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"type":"surface"}],"table":[{"cells":{"fill":{"color":"#EBF0F8"},"line":{"color":"white"}},"header":{"fill":{"color":"#C8D4E3"},"line":{"color":"white"}},"type":"table"}]},"layout":{"annotationdefaults":{"arrowcolor":"#2a3f5f","arrowhead":0,"arrowwidth":1},"autotypenumbers":"strict","coloraxis":{"colorbar":{"outlinewidth":0,"ticks":""}},"colorscale":{"diverging":[[0,"#8e0152"],[0.1,"#c51b7d"],[0.2,"#de77ae"],[0.3,"#f1b6da"],[0.4,"#fde0ef"],[0.5,"#f7f7f7"],[0.6,"#e6f5d0"],[0.7,"#b8e186"],[0.8,"#7fbc41"],[0.9,"#4d9221"],[1,"#276419"]],"sequential":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"sequentialminus":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]},"colorway":["#636efa","#EF553B","#00cc96","#ab63fa","#FFA15A","#19d3f3","#FF6692","#B6E880","#FF97FF","#FECB52"],"font":{"color":"#2a3f5f"},"geo":{"bgcolor":"white","lakecolor":"white","landcolor":"#E5ECF6","showlakes":true,"showland":true,"subunitcolor":"white"},"hoverlabel":{"align":"left"},"hovermode":"closest","mapbox":{"style":"light"},"paper_bgcolor":"white","plot_bgcolor":"#E5ECF6","polar":{"angularaxis":{"gridcolor":"white","linecolor":"white","ticks":""},"bgcolor":"#E5ECF6","radialaxis":{"gridcolor":"white","linecolor":"white","ticks":""}},"scene":{"xaxis":{"backgroundcolor":"#E5ECF6","gridcolor":"white","gridwidth":2,"linecolor":"white","showbackground":true,"ticks":"","zerolinecolor":"white"},"yaxis":{"backgroundcolor":"#E5ECF6","gridcolor":"white","gridwidth":2,"linecolor":"white","showbackground":true,"ticks":"","zerolinecolor":"white"},"zaxis":{"backgroundcolor":"#E5ECF6","gridcolor":"white","gridwidth":2,"linecolor":"white","showbackground":true,"ticks":"","zerolinecolor":"white"}},"shapedefaults":{"line":{"color":"#2a3f5f"}},"ternary":{"aaxis":{"gridcolor":"white","linecolor":"white","ticks":""},"baxis":{"gridcolor":"white","linecolor":"white","ticks":""},"bgcolor":"#E5ECF6","caxis":{"gridcolor":"white","linecolor":"white","ticks":""}},"title":{"x":0.05},"xaxis":{"automargin":true,"gridcolor":"white","linecolor":"white","ticks":"","title":{"standoff":15},"zerolinecolor":"white","zerolinewidth":2},"yaxis":{"automargin":true,"gridcolor":"white","linecolor":"white","ticks":"","title":{"standoff":15},"zerolinecolor":"white","zerolinewidth":2}}},"xaxis":{"anchor":"y","domain":[0.0,1.0],"title":{"text":"purchased_date"}},"yaxis":{"anchor":"x","domain":[0.0,1.0],"title":{"text":"Cumulative Dollars Spent"}},"legend":{"title":{"text":"purchased_by"},"tracegroupgap":0},"margin":{"t":60}},                        {"responsive": true}                    )                };                            </script>        </div>
</body>
</html>



For more of the plotting and charting, check it out [live on streamlit!](https://share.streamlit.io/gerardrbentley/roommate-ledger/main/app.py)
