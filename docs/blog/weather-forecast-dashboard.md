---
title: Checking 48 Mountain Weather Locations at Once
description: Using Async Python to feed a Streamlit Dashboard
categories:
    - projects
tags:
    - streamlit
    - python
    - async
    - intermediate
date: 2022-02-05
---

# Checking 48 Mountain Weather Locations at Once


![Screenshot of weather app](/images/weather/weather.png)

## Peak Weather: Checking New Hampshire's 48 4,000 Footers

Check it out [live on streamlit cloud](https://share.streamlit.io/gerardrbentley/peak-weather/main/streamlit_app/streamlit_app.py)

Built to give you a dashboard view of the next few hours' forecast for New Hampshires 48 4,000 ft mountains.
Gonna rain on the Kinsmans?
Is it snowing on Washington?
Should I hike Owl's Head?

Powered by [Streamlit](https://docs.streamlit.io/) + [Open Weather API](https://openweathermap.org/api).
Specifically, Streamlit runs the web interactinos and OpenWeather provides the data.

This post will go over a few aspects of the app:

- Data scraping the mountain metadata
- Connecting to Weather API feed
- Making it reasonably fast 

## Data Scraping

I couldn't find an easy csv or api for the latitudes and longitudes of the 48 4,000 footers, so I turned to [Wikipedia](https://en.wikipedia.org/wiki/Four-thousand_footers) for the list.

### Try Pandas

The [`read_html()`](https://pandas.pydata.org/docs/reference/api/pandas.read_html.html) function in Pandas has been a sanity saver in my job for reading data from flat file specification documents.

Unfortunately the data I'm looking for in Wikipedia is in `<li>...</li>` tags, not a real html `<table>...</table>`

### Naive Copy+Paste

Next I tried just copying the list of names and heights to feed to a search API, yielding a csv like the following after some cleanup:

```txt
name,height_ft
Washington,6288
Adams,5774
Jefferson,5712
```

And this gives us csv access to the data like so:



```python
import pandas as pd
mountains = pd.read_csv('./data/mtns.txt')
mountains.head(3)
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
      <th>name</th>
      <th>height_ft</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>Washington</td>
      <td>6288</td>
    </tr>
    <tr>
      <th>1</th>
      <td>Adams</td>
      <td>5774</td>
    </tr>
    <tr>
      <th>2</th>
      <td>Jefferson</td>
      <td>5712</td>
    </tr>
  </tbody>
</table>
</div>



### A-Links to the Rescue

Now with the list of peaks, I needed the corresponding latitude and longitudes.

After searching for a straightforward source, I realized the Wikipedia pages linked from the main list page were the best...

I grabbed the portion of the html with the list to a file with dev tools (chrome f12), but could have been done with BeautifulSoup

#### Scrape Mountain Links



```python
from bs4 import BeautifulSoup
# Chunk from 4,000 footers page containing list of mountains
# https://en.wikipedia.org/wiki/Four-thousand_footers
soup = BeautifulSoup(open("./data/wiki.html"), "html.parser")

# Gather <a> tags, ignore citation
links = [x for x in soup.find_all("a") if x.get("title")]
links[:2]
```




    [<a class="mw-redirect" href="/wiki/Mount_Washington_(New_Hampshire)" title="Mount Washington (New Hampshire)">Washington</a>,
     <a href="/wiki/Mount_Adams_(New_Hampshire)" title="Mount Adams (New Hampshire)">Adams</a>]



#### Get Lat Lon For One Mountain

With access to the `href` attributes of the `<a>` tags, I could then fetch all of those pages and scrape out the Lat and Lon from each.

Most older guides will use Python's `requests` library for this kind of task, but that library does not have the ability to send asynchronous requests without multiprocessing (Translation: It's difficult to fetch a bunch of pages all at once).

I've found success with [`httpx`](https://www.python-httpx.org/) and [`aiohttp`](https://docs.aiohttp.org/en/stable/) for making asynchronous requests in one Python process.
So I went with `httpx` for fetching each page.

Lets demonstrate fetching one of those pages and scraping the Latitude and Longitude.
We won't worry too much about errors or missed data for this cleaning phase.


```python
import httpx
# English Wikipedia
BASE_URL = "https://en.wikipedia.org"

def convert(raw_tude: str) -> float:
    """Takes a wikipedia latitude or longitude string and converts it to float
    Math Source: https://stackoverflow.com/questions/21298772/how-to-convert-latitude-longitude-to-decimal-in-python

    Args:
        raw_tude (str): Lat or Lon in one of the following forms:
            degrees°minutes′seconds″N,
            degrees°minutes′N,
            degrees-minutes-secondsN,
            degrees-minutesN

    Returns:
        (float): Float converted lat or lon based on supplied DMS
    """
    tude = raw_tude.replace("°", "-").replace("′", "-").replace("″", "")
    if tude[-2] == "-":
        tude = tude[:-2] + tude[-1]
    multiplier = 1 if tude[-1] in ["N", "E"] else -1
    return multiplier * sum(
        float(x) / 60 ** n for n, x in enumerate(tude[:-1].split("-"))
    )

a_link = links[0]
a_link
```




    <a class="mw-redirect" href="/wiki/Mount_Washington_(New_Hampshire)" title="Mount Washington (New Hampshire)">Washington</a>




```python
# bs4 lets us "get" html tag attributes as in python dicts
name = a_link.get("title")
link = a_link.get("href")

# httpx lets us fetch the raw html page
raw_page = httpx.get(BASE_URL + link)
# Which bs4 will help parse
raw_soup = BeautifulSoup(raw_page, "html.parser")

# find returns first instance of a tag with this class
raw_lat = raw_soup.find(class_="latitude").text.strip()
lat = convert(raw_lat)
raw_lon = raw_soup.find(class_="longitude").text.strip()
lon = convert(raw_lon)

name, link, lat, lon
```




    ('Mount Washington (New Hampshire)',
     '/wiki/Mount_Washington_(New_Hampshire)',
     44.2705,
     -71.30324999999999)



#### Get Lat Lon For Many Mountains

Lets chuck the first 10 mountains into a for-loop and fetch the same pieces of data.

First we'll define a function to encapsulate the synchronous fetch logic

Then we'll see how long this takes with jupyter's `%%time` magic


```python
def sync_get_coords(a_link: BeautifulSoup) -> dict:
    name = a_link.get("title")
    link = a_link.get("href")
    raw_page = httpx.get(BASE_URL + link)
    raw_soup = BeautifulSoup(raw_page, "html.parser")
    raw_lat = raw_soup.find(class_="latitude").text.strip()
    lat = convert(raw_lat)
    raw_lon = raw_soup.find(class_="longitude").text.strip()
    lon = convert(raw_lon)
    return {"name": name, "link": link, "lat": lat, "lon": lon}
```


```python
%%time

for a_link in links[:10]:
    result = sync_get_coords(a_link)
    print(result)
```

    {'name': 'Mount Washington (New Hampshire)', 'link': '/wiki/Mount_Washington_(New_Hampshire)', 'lat': 44.2705, 'lon': -71.30324999999999}
    {'name': 'Mount Adams (New Hampshire)', 'link': '/wiki/Mount_Adams_(New_Hampshire)', 'lat': 44.32055555555556, 'lon': -71.29138888888889}
    {'name': 'Mount Jefferson (New Hampshire)', 'link': '/wiki/Mount_Jefferson_(New_Hampshire)', 'lat': 44.30416666666667, 'lon': -71.31694444444445}
    {'name': 'Mount Monroe (New Hampshire)', 'link': '/wiki/Mount_Monroe_(New_Hampshire)', 'lat': 44.25555555555555, 'lon': -71.32249999999999}
    {'name': 'Mount Madison', 'link': '/wiki/Mount_Madison', 'lat': 44.32833333333333, 'lon': -71.27777777777777}
    {'name': 'Mount Lafayette', 'link': '/wiki/Mount_Lafayette', 'lat': 44.16083333333333, 'lon': -71.64444444444445}
    {'name': 'Mount Lincoln (New Hampshire)', 'link': '/wiki/Mount_Lincoln_(New_Hampshire)', 'lat': 44.14888888888889, 'lon': -71.64444444444445}
    {'name': 'South Twin Mountain (New Hampshire)', 'link': '/wiki/South_Twin_Mountain_(New_Hampshire)', 'lat': 44.1875, 'lon': -71.55533333333334}
    {'name': 'Carter Dome', 'link': '/wiki/Carter_Dome', 'lat': 44.26722222222222, 'lon': -71.17888888888889}
    {'name': 'Mount Moosilauke', 'link': '/wiki/Mount_Moosilauke', 'lat': 44.02444444444444, 'lon': -71.83083333333333}
    CPU times: user 2.44 s, sys: 62.4 ms, total: 2.5 s
    Wall time: 3.9 s


Results will vary by machine, internet connection, Wikipedia server status, and [butterly wing flaps](https://xkcd.com/378/).

Mine were like this the first time around:

```txt
CPU times: user 2.25 s, sys: 65.1 ms, total: 2.31 s
Wall time: 5.47 s
```

#### Faster Fetching

We're not using the asynchronous capabilities of `httpx` yet, so each of the 10 requests to Wikipedia needs to go over the wire and back in order for the next request to start.

How about we speed things up a little (Jupyter `%%time` doesn't work on async cells):


```python
import asyncio
async def get_coords(client: httpx.AsyncClient, a_link: BeautifulSoup) -> dict:
    """Given http client and <a> link from wikipedia list,
    Fetches the place's html page,
    Attempts to parse and convert lat and lon to decimal from the page (first occurrence)
    Returns entry with keys: "name", "link", "lat", "lon"

    Args:
        client (httpx.AsyncClient): To make requests. See httpx docs
        a_link (BeautifulSoup): <a> ... </a> chunk

    Returns:
        dict: coordinate entry for this wikipedia place
    """    
    name = a_link.get("title")
    link = a_link.get("href")
    raw_page = await client.get(BASE_URL + link)
    raw_soup = BeautifulSoup(raw_page, "html.parser")
    raw_lat = raw_soup.find(class_="latitude").text.strip()
    lat = convert(raw_lat)

    raw_lon = raw_soup.find(class_="longitude").text.strip()
    lon = convert(raw_lon)

    return {"name": name, "link": link, "lat": lat, "lon": lon}


async def gather_coords(links: list) -> list:
    """Given List of a links, asynchronously fetch all of them and return results"""
    async with httpx.AsyncClient() as client:
        tasks = [asyncio.ensure_future(get_coords(client, link)) for link in links]
        coords = await asyncio.gather(*tasks)
        return coords
```


```python
from timeit import default_timer as timer
start = timer()
# Async get all lat lon as list of dictionaries
coords = await gather_coords(links[:10])
end = timer()
print(*coords[:10], f"{end - start :.2f} seconds", sep='\n')
```

    {'name': 'Mount Washington (New Hampshire)', 'link': '/wiki/Mount_Washington_(New_Hampshire)', 'lat': 44.2705, 'lon': -71.30324999999999}
    {'name': 'Mount Adams (New Hampshire)', 'link': '/wiki/Mount_Adams_(New_Hampshire)', 'lat': 44.32055555555556, 'lon': -71.29138888888889}
    {'name': 'Mount Jefferson (New Hampshire)', 'link': '/wiki/Mount_Jefferson_(New_Hampshire)', 'lat': 44.30416666666667, 'lon': -71.31694444444445}
    {'name': 'Mount Monroe (New Hampshire)', 'link': '/wiki/Mount_Monroe_(New_Hampshire)', 'lat': 44.25555555555555, 'lon': -71.32249999999999}
    {'name': 'Mount Madison', 'link': '/wiki/Mount_Madison', 'lat': 44.32833333333333, 'lon': -71.27777777777777}
    {'name': 'Mount Lafayette', 'link': '/wiki/Mount_Lafayette', 'lat': 44.16083333333333, 'lon': -71.64444444444445}
    {'name': 'Mount Lincoln (New Hampshire)', 'link': '/wiki/Mount_Lincoln_(New_Hampshire)', 'lat': 44.14888888888889, 'lon': -71.64444444444445}
    {'name': 'South Twin Mountain (New Hampshire)', 'link': '/wiki/South_Twin_Mountain_(New_Hampshire)', 'lat': 44.1875, 'lon': -71.55533333333334}
    {'name': 'Carter Dome', 'link': '/wiki/Carter_Dome', 'lat': 44.26722222222222, 'lon': -71.17888888888889}
    {'name': 'Mount Moosilauke', 'link': '/wiki/Mount_Moosilauke', 'lat': 44.02444444444444, 'lon': -71.83083333333333}
    2.01 seconds



```python
# Data from original run
2.16 / 5.47
```




    0.3948811700182816



40% of the time spent scraping data, sounds good to me!

#### Data Cleaning

If you thought the "finds first occurrence" strategy for scraping latitude and longitude was going to cause errors, cheers to you.

Turns out just a few mountains have multiple peaks that count as 4,000 footers, so these mountains have 2 sets of latitudes and longitudes.

I fetched these by hand and said LGTM with my csv of:
- Mountain Names
- Heights
- Latitudes
- Longitudes

## Weather Scraping

I figured there's probably a free open API for accessing weather data, and a quick google found two that caught my eye:

- [OpenWeatherMap](https://openweathermap.org/api)
- [Weather.gov](https://www.weather.gov/documentation/services-web-api)

It's a free API, but this was the selling point for OpenWeatherMap for this Proof-of-Concept project:

The [`One Call API`](https://openweathermap.org/api/one-call-api) provides the following weather data for any geographical coordinates:

- *Current weather*
- *Minute forecast* for 1 hour
- *Hourly forecast* for 48 hours
- *Daily forecast* for 7 days
- National weather *alerts*
- *Historical* weather data for the previous 5 days

### API Signup and Prep

Getting a free account and key was straightforward involving just an email address verification link.

Then off to the races with the following documentation (there's more on their site in better formatting):

```sh
# One Call URL
https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude={part}&appid={API key}
```

**Parameters**

`lat`, `lon`: *required* 
Geographical coordinates (latitude, longitude)

`appid`: *required* 
Your unique API key (you can always find it on your account page under the "API key" tab)


```python
from pydantic import BaseSettings


class Settings(BaseSettings):
    """Handles fetching configuration from environment variables and secrets.
    Type-hinting for config as a bonus"""

    open_weather_api_key: str


settings = Settings()


class WeatherUnit:
    STANDARD = "standard"
    KELVIN = "standard"
    METRIC = "metric"
    IMPERIAL = "imperial"


def get_one_call_endpoint(
    lat: float,
    lon: float,
    units: WeatherUnit = WeatherUnit.IMPERIAL,
    exclude="",
    lang="en",
):
    if exclude != "":
        exclude = f"&exclude={exclude}"
    return f"https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&units={units}{exclude}&lang={lang}&appid={settings.open_weather_api_key}"


def get_one_call_data(lat, lon):
    endpoint = get_one_call_endpoint(lat, lon)
    response = httpx.get(endpoint)
    return response.json()

```

### Test One Location

I included some of the API parameters as endpoint configuration options as I messed around with it.

For this use case these defaults are sensible to me:

- American users -> `units = Imperial`
- English speaking users -> `lang="en"`
- Exclude -> don't care too much about some extra data coming over to the server

Lets see what we get for a live mountain location!


```python
mount_washington = coords[0]
mount_washington
```




    {'name': 'Mount Washington (New Hampshire)',
     'link': '/wiki/Mount_Washington_(New_Hampshire)',
     'lat': 44.2705,
     'lon': -71.30324999999999}




```python
#collapse-output
get_one_call_data(mount_washington['lat'], mount_washington['lon'])
```




    {'lat': 44.2705,
     'lon': -71.3032,
     'timezone': 'America/New_York',
     'timezone_offset': -18000,
     'current': {'dt': 1644375343,
      'sunrise': 1644321288,
      'sunset': 1644357845,
      'temp': 11.35,
      'feels_like': -0.72,
      'pressure': 1011,
      'humidity': 84,
      'dew_point': 7.88,
      'uvi': 0,
      'clouds': 99,
      'visibility': 300,
      'wind_speed': 8.5,
      'wind_deg': 300,
      'wind_gust': 15.79,
      'weather': [{'id': 600,
        'main': 'Snow',
        'description': 'light snow',
        'icon': '13n'}],
      'snow': {'1h': 0.19}},
     'minutely': [{'dt': 1644375360, 'precipitation': 0},
      {'dt': 1644375420, 'precipitation': 0},
      {'dt': 1644375480, 'precipitation': 0},
      {'dt': 1644375540, 'precipitation': 0},
      {'dt': 1644375600, 'precipitation': 0},
      {'dt': 1644375660, 'precipitation': 0},
      {'dt': 1644375720, 'precipitation': 0},
      {'dt': 1644375780, 'precipitation': 0},
      {'dt': 1644375840, 'precipitation': 0},
      {'dt': 1644375900, 'precipitation': 0},
      {'dt': 1644375960, 'precipitation': 0},
      {'dt': 1644376020, 'precipitation': 0},
      {'dt': 1644376080, 'precipitation': 0},
      {'dt': 1644376140, 'precipitation': 0},
      {'dt': 1644376200, 'precipitation': 0},
      {'dt': 1644376260, 'precipitation': 0},
      {'dt': 1644376320, 'precipitation': 0},
      {'dt': 1644376380, 'precipitation': 0},
      {'dt': 1644376440, 'precipitation': 0},
      {'dt': 1644376500, 'precipitation': 0},
      {'dt': 1644376560, 'precipitation': 0},
      {'dt': 1644376620, 'precipitation': 0},
      {'dt': 1644376680, 'precipitation': 0},
      {'dt': 1644376740, 'precipitation': 0},
      {'dt': 1644376800, 'precipitation': 0},
      {'dt': 1644376860, 'precipitation': 0},
      {'dt': 1644376920, 'precipitation': 0},
      {'dt': 1644376980, 'precipitation': 0},
      {'dt': 1644377040, 'precipitation': 0},
      {'dt': 1644377100, 'precipitation': 0},
      {'dt': 1644377160, 'precipitation': 0},
      {'dt': 1644377220, 'precipitation': 0},
      {'dt': 1644377280, 'precipitation': 0},
      {'dt': 1644377340, 'precipitation': 0},
      {'dt': 1644377400, 'precipitation': 0},
      {'dt': 1644377460, 'precipitation': 0},
      {'dt': 1644377520, 'precipitation': 0},
      {'dt': 1644377580, 'precipitation': 0},
      {'dt': 1644377640, 'precipitation': 0},
      {'dt': 1644377700, 'precipitation': 0},
      {'dt': 1644377760, 'precipitation': 0},
      {'dt': 1644377820, 'precipitation': 0},
      {'dt': 1644377880, 'precipitation': 0},
      {'dt': 1644377940, 'precipitation': 0},
      {'dt': 1644378000, 'precipitation': 0},
      {'dt': 1644378060, 'precipitation': 0},
      {'dt': 1644378120, 'precipitation': 0},
      {'dt': 1644378180, 'precipitation': 0},
      {'dt': 1644378240, 'precipitation': 0},
      {'dt': 1644378300, 'precipitation': 0},
      {'dt': 1644378360, 'precipitation': 0},
      {'dt': 1644378420, 'precipitation': 0},
      {'dt': 1644378480, 'precipitation': 0},
      {'dt': 1644378540, 'precipitation': 0},
      {'dt': 1644378600, 'precipitation': 0},
      {'dt': 1644378660, 'precipitation': 0},
      {'dt': 1644378720, 'precipitation': 0},
      {'dt': 1644378780, 'precipitation': 0},
      {'dt': 1644378840, 'precipitation': 0},
      {'dt': 1644378900, 'precipitation': 0},
      {'dt': 1644378960, 'precipitation': 0}],
     'hourly': [{'dt': 1644372000,
       'temp': 10.76,
       'feels_like': -1.25,
       'pressure': 1011,
       'humidity': 87,
       'dew_point': 7.99,
       'uvi': 0,
       'clouds': 99,
       'visibility': 353,
       'wind_speed': 8.25,
       'wind_deg': 300,
       'wind_gust': 15.05,
       'weather': [{'id': 600,
         'main': 'Snow',
         'description': 'light snow',
         'icon': '13n'}],
       'pop': 0.33,
       'snow': {'1h': 0.22}},
      {'dt': 1644375600,
       'temp': 11.35,
       'feels_like': -0.72,
       'pressure': 1011,
       'humidity': 84,
       'dew_point': 7.88,
       'uvi': 0,
       'clouds': 99,
       'visibility': 300,
       'wind_speed': 8.5,
       'wind_deg': 300,
       'wind_gust': 15.79,
       'weather': [{'id': 600,
         'main': 'Snow',
         'description': 'light snow',
         'icon': '13n'}],
       'pop': 0.33,
       'snow': {'1h': 0.19}},
      {'dt': 1644379200,
       'temp': 10.33,
       'feels_like': -1.82,
       'pressure': 1011,
       'humidity': 86,
       'dew_point': 7.34,
       'uvi': 0,
       'clouds': 99,
       'visibility': 338,
       'wind_speed': 8.32,
       'wind_deg': 303,
       'wind_gust': 15.97,
       'weather': [{'id': 600,
         'main': 'Snow',
         'description': 'light snow',
         'icon': '13n'}],
       'pop': 0.33,
       'snow': {'1h': 0.24}},
      {'dt': 1644382800,
       'temp': 9.09,
       'feels_like': -3.19,
       'pressure': 1011,
       'humidity': 89,
       'dew_point': 6.78,
       'uvi': 0,
       'clouds': 99,
       'visibility': 302,
       'wind_speed': 8.14,
       'wind_deg': 300,
       'wind_gust': 15.41,
       'weather': [{'id': 600,
         'main': 'Snow',
         'description': 'light snow',
         'icon': '13n'}],
       'pop': 0.33,
       'snow': {'1h': 0.17}},
      {'dt': 1644386400,
       'temp': 7.93,
       'feels_like': -4.67,
       'pressure': 1012,
       'humidity': 90,
       'dew_point': 5.86,
       'uvi': 0,
       'clouds': 98,
       'visibility': 319,
       'wind_speed': 8.43,
       'wind_deg': 300,
       'wind_gust': 16.02,
       'weather': [{'id': 600,
         'main': 'Snow',
         'description': 'light snow',
         'icon': '13n'}],
       'pop': 0.33,
       'snow': {'1h': 0.18}},
      {'dt': 1644390000,
       'temp': 6.48,
       'feels_like': -6.12,
       'pressure': 1012,
       'humidity': 92,
       'dew_point': 4.84,
       'uvi': 0,
       'clouds': 96,
       'visibility': 417,
       'wind_speed': 8.43,
       'wind_deg': 303,
       'wind_gust': 15.66,
       'weather': [{'id': 600,
         'main': 'Snow',
         'description': 'light snow',
         'icon': '13n'}],
       'pop': 0.21,
       'snow': {'1h': 0.16}},
      {'dt': 1644393600,
       'temp': 4.3,
       'feels_like': -8.3,
       'pressure': 1013,
       'humidity': 95,
       'dew_point': 11.14,
       'uvi': 0,
       'clouds': 94,
       'visibility': 761,
       'wind_speed': 7.81,
       'wind_deg': 302,
       'wind_gust': 14.2,
       'weather': [{'id': 804,
         'main': 'Clouds',
         'description': 'overcast clouds',
         'icon': '04n'}],
       'pop': 0.09},
      {'dt': 1644397200,
       'temp': 4.03,
       'feels_like': -8.57,
       'pressure': 1013,
       'humidity': 94,
       'dew_point': 10.85,
       'uvi': 0,
       'clouds': 92,
       'visibility': 975,
       'wind_speed': 7.4,
       'wind_deg': 302,
       'wind_gust': 13.35,
       'weather': [{'id': 804,
         'main': 'Clouds',
         'description': 'overcast clouds',
         'icon': '04n'}],
       'pop': 0.09},
      {'dt': 1644400800,
       'temp': 3.79,
       'feels_like': -8.52,
       'pressure': 1014,
       'humidity': 95,
       'dew_point': 10.58,
       'uvi': 0,
       'clouds': 94,
       'visibility': 1495,
       'wind_speed': 7.02,
       'wind_deg': 296,
       'wind_gust': 11.65,
       'weather': [{'id': 804,
         'main': 'Clouds',
         'description': 'overcast clouds',
         'icon': '04n'}],
       'pop': 0.04},
      {'dt': 1644404400,
       'temp': 3.38,
       'feels_like': -8.12,
       'pressure': 1016,
       'humidity': 95,
       'dew_point': 10.27,
       'uvi': 0,
       'clouds': 95,
       'visibility': 1822,
       'wind_speed': 6.22,
       'wind_deg': 295,
       'wind_gust': 10.11,
       'weather': [{'id': 804,
         'main': 'Clouds',
         'description': 'overcast clouds',
         'icon': '04n'}],
       'pop': 0.04},
      {'dt': 1644408000,
       'temp': 2.26,
       'feels_like': -8.12,
       'pressure': 1017,
       'humidity': 96,
       'dew_point': 9.19,
       'uvi': 0,
       'clouds': 96,
       'visibility': 5758,
       'wind_speed': 5.19,
       'wind_deg': 298,
       'wind_gust': 7.99,
       'weather': [{'id': 804,
         'main': 'Clouds',
         'description': 'overcast clouds',
         'icon': '04d'}],
       'pop': 0.04},
      {'dt': 1644411600,
       'temp': 3.88,
       'feels_like': -5.91,
       'pressure': 1017,
       'humidity': 94,
       'dew_point': 10.62,
       'uvi': 0.35,
       'clouds': 89,
       'visibility': 10000,
       'wind_speed': 4.97,
       'wind_deg': 305,
       'wind_gust': 8.77,
       'weather': [{'id': 804,
         'main': 'Clouds',
         'description': 'overcast clouds',
         'icon': '04d'}],
       'pop': 0},
      {'dt': 1644415200,
       'temp': 7.86,
       'feels_like': -1.5,
       'pressure': 1017,
       'humidity': 84,
       'dew_point': 12.45,
       'uvi': 0.9,
       'clouds': 71,
       'visibility': 10000,
       'wind_speed': 5.17,
       'wind_deg': 301,
       'wind_gust': 7.63,
       'weather': [{'id': 803,
         'main': 'Clouds',
         'description': 'broken clouds',
         'icon': '04d'}],
       'pop': 0},
      {'dt': 1644418800,
       'temp': 11.75,
       'feels_like': 3.81,
       'pressure': 1016,
       'humidity': 76,
       'dew_point': 13.91,
       'uvi': 1.59,
       'clouds': 52,
       'visibility': 10000,
       'wind_speed': 4.61,
       'wind_deg': 311,
       'wind_gust': 6.82,
       'weather': [{'id': 803,
         'main': 'Clouds',
         'description': 'broken clouds',
         'icon': '04d'}],
       'pop': 0},
      {'dt': 1644422400,
       'temp': 14.92,
       'feels_like': 9.14,
       'pressure': 1016,
       'humidity': 71,
       'dew_point': 15.62,
       'uvi': 2.16,
       'clouds': 56,
       'visibility': 10000,
       'wind_speed': 3.49,
       'wind_deg': 304,
       'wind_gust': 4.79,
       'weather': [{'id': 803,
         'main': 'Clouds',
         'description': 'broken clouds',
         'icon': '04d'}],
       'pop': 0},
      {'dt': 1644426000,
       'temp': 17.1,
       'feels_like': 17.1,
       'pressure': 1015,
       'humidity': 70,
       'dew_point': 17.31,
       'uvi': 2.29,
       'clouds': 64,
       'visibility': 10000,
       'wind_speed': 2.44,
       'wind_deg': 283,
       'wind_gust': 3.87,
       'weather': [{'id': 803,
         'main': 'Clouds',
         'description': 'broken clouds',
         'icon': '04d'}],
       'pop': 0},
      {'dt': 1644429600,
       'temp': 18.88,
       'feels_like': 18.88,
       'pressure': 1014,
       'humidity': 68,
       'dew_point': 18.59,
       'uvi': 1.95,
       'clouds': 67,
       'visibility': 10000,
       'wind_speed': 2.1,
       'wind_deg': 270,
       'wind_gust': 3.51,
       'weather': [{'id': 803,
         'main': 'Clouds',
         'description': 'broken clouds',
         'icon': '04d'}],
       'pop': 0},
      {'dt': 1644433200,
       'temp': 19.72,
       'feels_like': 19.72,
       'pressure': 1014,
       'humidity': 68,
       'dew_point': 19.26,
       'uvi': 1.2,
       'clouds': 98,
       'visibility': 10000,
       'wind_speed': 2.01,
       'wind_deg': 226,
       'wind_gust': 3.6,
       'weather': [{'id': 804,
         'main': 'Clouds',
         'description': 'overcast clouds',
         'icon': '04d'}],
       'pop': 0},
      {'dt': 1644436800,
       'temp': 19.83,
       'feels_like': 19.83,
       'pressure': 1013,
       'humidity': 72,
       'dew_point': 20.84,
       'uvi': 0.58,
       'clouds': 95,
       'visibility': 10000,
       'wind_speed': 2.77,
       'wind_deg': 185,
       'wind_gust': 4.38,
       'weather': [{'id': 804,
         'main': 'Clouds',
         'description': 'overcast clouds',
         'icon': '04d'}],
       'pop': 0},
      {'dt': 1644440400,
       'temp': 18.39,
       'feels_like': 13.32,
       'pressure': 1013,
       'humidity': 84,
       'dew_point': 23.11,
       'uvi': 0.17,
       'clouds': 70,
       'visibility': 10000,
       'wind_speed': 3.36,
       'wind_deg': 185,
       'wind_gust': 5.3,
       'weather': [{'id': 803,
         'main': 'Clouds',
         'description': 'broken clouds',
         'icon': '04d'}],
       'pop': 0},
      {'dt': 1644444000,
       'temp': 11.05,
       'feels_like': 11.05,
       'pressure': 1014,
       'humidity': 95,
       'dew_point': 18.41,
       'uvi': 0,
       'clouds': 55,
       'visibility': 10000,
       'wind_speed': 2.82,
       'wind_deg': 191,
       'wind_gust': 2.77,
       'weather': [{'id': 803,
         'main': 'Clouds',
         'description': 'broken clouds',
         'icon': '04d'}],
       'pop': 0},
      {'dt': 1644447600,
       'temp': 8.55,
       'feels_like': 8.55,
       'pressure': 1015,
       'humidity': 96,
       'dew_point': 16.05,
       'uvi': 0,
       'clouds': 48,
       'visibility': 10000,
       'wind_speed': 2.89,
       'wind_deg': 185,
       'wind_gust': 3.04,
       'weather': [{'id': 802,
         'main': 'Clouds',
         'description': 'scattered clouds',
         'icon': '03n'}],
       'pop': 0},
      {'dt': 1644451200,
       'temp': 9.16,
       'feels_like': 1.51,
       'pressure': 1015,
       'humidity': 96,
       'dew_point': 16.72,
       'uvi': 0,
       'clouds': 56,
       'visibility': 10000,
       'wind_speed': 4.12,
       'wind_deg': 177,
       'wind_gust': 6.71,
       'weather': [{'id': 803,
         'main': 'Clouds',
         'description': 'broken clouds',
         'icon': '04n'}],
       'pop': 0},
      {'dt': 1644454800,
       'temp': 9.46,
       'feels_like': 1.56,
       'pressure': 1015,
       'humidity': 96,
       'dew_point': 16.95,
       'uvi': 0,
       'clouds': 100,
       'visibility': 9935,
       'wind_speed': 4.32,
       'wind_deg': 179,
       'wind_gust': 7.67,
       'weather': [{'id': 804,
         'main': 'Clouds',
         'description': 'overcast clouds',
         'icon': '04n'}],
       'pop': 0},
      {'dt': 1644458400,
       'temp': 9.12,
       'feels_like': 1.67,
       'pressure': 1015,
       'humidity': 94,
       'dew_point': 16.07,
       'uvi': 0,
       'clouds': 100,
       'visibility': 9789,
       'wind_speed': 3.98,
       'wind_deg': 182,
       'wind_gust': 6.71,
       'weather': [{'id': 804,
         'main': 'Clouds',
         'description': 'overcast clouds',
         'icon': '04n'}],
       'pop': 0},
      {'dt': 1644462000,
       'temp': 9.39,
       'feels_like': 2.62,
       'pressure': 1014,
       'humidity': 92,
       'dew_point': 16.05,
       'uvi': 0,
       'clouds': 100,
       'visibility': 10000,
       'wind_speed': 3.6,
       'wind_deg': 199,
       'wind_gust': 4.16,
       'weather': [{'id': 804,
         'main': 'Clouds',
         'description': 'overcast clouds',
         'icon': '04n'}],
       'pop': 0},
      {'dt': 1644465600,
       'temp': 10.08,
       'feels_like': 3.63,
       'pressure': 1013,
       'humidity': 92,
       'dew_point': 16.77,
       'uvi': 0,
       'clouds': 100,
       'visibility': 10000,
       'wind_speed': 3.47,
       'wind_deg': 209,
       'wind_gust': 4.21,
       'weather': [{'id': 804,
         'main': 'Clouds',
         'description': 'overcast clouds',
         'icon': '04n'}],
       'pop': 0},
      {'dt': 1644469200,
       'temp': 10.22,
       'feels_like': 3.69,
       'pressure': 1013,
       'humidity': 92,
       'dew_point': 16.92,
       'uvi': 0,
       'clouds': 99,
       'visibility': 10000,
       'wind_speed': 3.53,
       'wind_deg': 205,
       'wind_gust': 4.29,
       'weather': [{'id': 804,
         'main': 'Clouds',
         'description': 'overcast clouds',
         'icon': '04n'}],
       'pop': 0},
      {'dt': 1644472800,
       'temp': 9.5,
       'feels_like': 2.26,
       'pressure': 1012,
       'humidity': 92,
       'dew_point': 16.18,
       'uvi': 0,
       'clouds': 87,
       'visibility': 10000,
       'wind_speed': 3.89,
       'wind_deg': 213,
       'wind_gust': 3.74,
       'weather': [{'id': 804,
         'main': 'Clouds',
         'description': 'overcast clouds',
         'icon': '04n'}],
       'pop': 0},
      {'dt': 1644476400,
       'temp': 9.05,
       'feels_like': 2.03,
       'pressure': 1012,
       'humidity': 93,
       'dew_point': 15.87,
       'uvi': 0,
       'clouds': 22,
       'visibility': 10000,
       'wind_speed': 3.71,
       'wind_deg': 220,
       'wind_gust': 3.71,
       'weather': [{'id': 801,
         'main': 'Clouds',
         'description': 'few clouds',
         'icon': '02n'}],
       'pop': 0},
      {'dt': 1644480000,
       'temp': 8.8,
       'feels_like': 2.21,
       'pressure': 1011,
       'humidity': 92,
       'dew_point': 15.4,
       'uvi': 0,
       'clouds': 27,
       'visibility': 10000,
       'wind_speed': 3.44,
       'wind_deg': 230,
       'wind_gust': 3.56,
       'weather': [{'id': 802,
         'main': 'Clouds',
         'description': 'scattered clouds',
         'icon': '03n'}],
       'pop': 0},
      {'dt': 1644483600,
       'temp': 10.08,
       'feels_like': 3.76,
       'pressure': 1010,
       'humidity': 91,
       'dew_point': 16.47,
       'uvi': 0,
       'clouds': 51,
       'visibility': 10000,
       'wind_speed': 3.4,
       'wind_deg': 230,
       'wind_gust': 3.51,
       'weather': [{'id': 803,
         'main': 'Clouds',
         'description': 'broken clouds',
         'icon': '04n'}],
       'pop': 0},
      {'dt': 1644487200,
       'temp': 11.68,
       'feels_like': 5.83,
       'pressure': 1010,
       'humidity': 90,
       'dew_point': 17.89,
       'uvi': 0,
       'clouds': 64,
       'visibility': 10000,
       'wind_speed': 3.27,
       'wind_deg': 223,
       'wind_gust': 3.18,
       'weather': [{'id': 803,
         'main': 'Clouds',
         'description': 'broken clouds',
         'icon': '04n'}],
       'pop': 0},
      {'dt': 1644490800,
       'temp': 12.47,
       'feels_like': 6.19,
       'pressure': 1009,
       'humidity': 90,
       'dew_point': 18.73,
       'uvi': 0,
       'clouds': 71,
       'visibility': 10000,
       'wind_speed': 3.58,
       'wind_deg': 223,
       'wind_gust': 3.8,
       'weather': [{'id': 803,
         'main': 'Clouds',
         'description': 'broken clouds',
         'icon': '04n'}],
       'pop': 0},
      {'dt': 1644494400,
       'temp': 13.1,
       'feels_like': 7.18,
       'pressure': 1009,
       'humidity': 94,
       'dew_point': 20.43,
       'uvi': 0,
       'clouds': 76,
       'visibility': 856,
       'wind_speed': 3.42,
       'wind_deg': 224,
       'wind_gust': 3.69,
       'weather': [{'id': 803,
         'main': 'Clouds',
         'description': 'broken clouds',
         'icon': '04d'}],
       'pop': 0.09},
      {'dt': 1644498000,
       'temp': 16.45,
       'feels_like': 11.53,
       'pressure': 1008,
       'humidity': 96,
       'dew_point': 24.35,
       'uvi': 0.23,
       'clouds': 100,
       'visibility': 619,
       'wind_speed': 3.11,
       'wind_deg': 222,
       'wind_gust': 5.57,
       'weather': [{'id': 600,
         'main': 'Snow',
         'description': 'light snow',
         'icon': '13d'}],
       'pop': 0.55,
       'snow': {'1h': 0.17}},
      {'dt': 1644501600,
       'temp': 18.79,
       'feels_like': 13.89,
       'pressure': 1008,
       'humidity': 95,
       'dew_point': 26.6,
       'uvi': 0.58,
       'clouds': 100,
       'visibility': 6348,
       'wind_speed': 3.29,
       'wind_deg': 214,
       'wind_gust': 5.3,
       'weather': [{'id': 804,
         'main': 'Clouds',
         'description': 'overcast clouds',
         'icon': '04d'}],
       'pop': 0.42},
      {'dt': 1644505200,
       'temp': 20.39,
       'feels_like': 14.59,
       'pressure': 1007,
       'humidity': 95,
       'dew_point': 28.13,
       'uvi': 1.01,
       'clouds': 100,
       'visibility': 10000,
       'wind_speed': 4.05,
       'wind_deg': 199,
       'wind_gust': 6.71,
       'weather': [{'id': 804,
         'main': 'Clouds',
         'description': 'overcast clouds',
         'icon': '04d'}],
       'pop': 0.38},
      {'dt': 1644508800,
       'temp': 21.81,
       'feels_like': 15.03,
       'pressure': 1006,
       'humidity': 94,
       'dew_point': 29.3,
       'uvi': 1.04,
       'clouds': 94,
       'visibility': 4548,
       'wind_speed': 5.08,
       'wind_deg': 196,
       'wind_gust': 9.06,
       'weather': [{'id': 804,
         'main': 'Clouds',
         'description': 'overcast clouds',
         'icon': '04d'}],
       'pop': 0.25},
      {'dt': 1644512400,
       'temp': 22.01,
       'feels_like': 14.76,
       'pressure': 1005,
       'humidity': 92,
       'dew_point': 28.96,
       'uvi': 1.1,
       'clouds': 91,
       'visibility': 2107,
       'wind_speed': 5.57,
       'wind_deg': 197,
       'wind_gust': 12.86,
       'weather': [{'id': 804,
         'main': 'Clouds',
         'description': 'overcast clouds',
         'icon': '04d'}],
       'pop': 0.23},
      {'dt': 1644516000,
       'temp': 21.06,
       'feels_like': 13.69,
       'pressure': 1004,
       'humidity': 99,
       'dew_point': 29.71,
       'uvi': 0.94,
       'clouds': 93,
       'visibility': 53,
       'wind_speed': 5.5,
       'wind_deg': 194,
       'wind_gust': 10.96,
       'weather': [{'id': 600,
         'main': 'Snow',
         'description': 'light snow',
         'icon': '13d'}],
       'pop': 0.35,
       'snow': {'1h': 0.31}},
      {'dt': 1644519600,
       'temp': 20.07,
       'feels_like': 12.65,
       'pressure': 1004,
       'humidity': 99,
       'dew_point': 28.72,
       'uvi': 0.27,
       'clouds': 100,
       'visibility': 76,
       'wind_speed': 5.37,
       'wind_deg': 216,
       'wind_gust': 13.85,
       'weather': [{'id': 600,
         'main': 'Snow',
         'description': 'light snow',
         'icon': '13d'}],
       'pop': 0.68,
       'snow': {'1h': 0.36}},
      {'dt': 1644523200,
       'temp': 19.6,
       'feels_like': 12.4,
       'pressure': 1004,
       'humidity': 95,
       'dew_point': 27.32,
       'uvi': 0.14,
       'clouds': 100,
       'visibility': 255,
       'wind_speed': 5.1,
       'wind_deg': 240,
       'wind_gust': 14,
       'weather': [{'id': 600,
         'main': 'Snow',
         'description': 'light snow',
         'icon': '13d'}],
       'pop': 0.6,
       'snow': {'1h': 0.21}},
      {'dt': 1644526800,
       'temp': 18.72,
       'feels_like': 11.3,
       'pressure': 1005,
       'humidity': 94,
       'dew_point': 26.04,
       'uvi': 0.04,
       'clouds': 100,
       'visibility': 781,
       'wind_speed': 5.14,
       'wind_deg': 254,
       'wind_gust': 15.99,
       'weather': [{'id': 600,
         'main': 'Snow',
         'description': 'light snow',
         'icon': '13d'}],
       'pop': 0.7,
       'snow': {'1h': 0.14}},
      {'dt': 1644530400,
       'temp': 16.41,
       'feels_like': 9.25,
       'pressure': 1005,
       'humidity': 96,
       'dew_point': 24.3,
       'uvi': 0,
       'clouds': 100,
       'visibility': 645,
       'wind_speed': 4.61,
       'wind_deg': 261,
       'wind_gust': 9.51,
       'weather': [{'id': 600,
         'main': 'Snow',
         'description': 'light snow',
         'icon': '13d'}],
       'pop': 0.69,
       'snow': {'1h': 0.16}},
      {'dt': 1644534000,
       'temp': 14.34,
       'feels_like': 5.86,
       'pressure': 1007,
       'humidity': 95,
       'dew_point': 21.97,
       'uvi': 0,
       'clouds': 99,
       'visibility': 689,
       'wind_speed': 5.39,
       'wind_deg': 260,
       'wind_gust': 12.37,
       'weather': [{'id': 600,
         'main': 'Snow',
         'description': 'light snow',
         'icon': '13n'}],
       'pop': 0.66,
       'snow': {'1h': 0.11}},
      {'dt': 1644537600,
       'temp': 14.02,
       'feels_like': 4.87,
       'pressure': 1007,
       'humidity': 94,
       'dew_point': 21.47,
       'uvi': 0,
       'clouds': 99,
       'visibility': 282,
       'wind_speed': 5.95,
       'wind_deg': 257,
       'wind_gust': 16.06,
       'weather': [{'id': 600,
         'main': 'Snow',
         'description': 'light snow',
         'icon': '13n'}],
       'pop': 0.58,
       'snow': {'1h': 0.26}},
      {'dt': 1644541200,
       'temp': 13.08,
       'feels_like': 3.52,
       'pressure': 1008,
       'humidity': 94,
       'dew_point': 20.55,
       'uvi': 0,
       'clouds': 100,
       'visibility': 248,
       'wind_speed': 6.17,
       'wind_deg': 261,
       'wind_gust': 16.87,
       'weather': [{'id': 600,
         'main': 'Snow',
         'description': 'light snow',
         'icon': '13n'}],
       'pop': 0.42,
       'snow': {'1h': 0.28}}],
     'daily': [{'dt': 1644336000,
       'sunrise': 1644321288,
       'sunset': 1644357845,
       'moonrise': 1644334440,
       'moonset': 1644298020,
       'moon_phase': 0.25,
       'temp': {'day': 18.59,
        'min': 10.33,
        'max': 19.72,
        'night': 10.33,
        'eve': 15.06,
        'morn': 14.94},
       'feels_like': {'day': 12.94, 'night': -1.82, 'eve': 5.97, 'morn': 14.94},
       'pressure': 1010,
       'humidity': 97,
       'dew_point': 26.85,
       'wind_speed': 8.5,
       'wind_deg': 300,
       'wind_gust': 15.97,
       'weather': [{'id': 601,
         'main': 'Snow',
         'description': 'snow',
         'icon': '13d'}],
       'clouds': 100,
       'pop': 0.99,
       'snow': 10.77,
       'uvi': 1.2},
      {'dt': 1644422400,
       'sunrise': 1644407609,
       'sunset': 1644444329,
       'moonrise': 1644422460,
       'moonset': 1644388320,
       'moon_phase': 0.28,
       'temp': {'day': 14.92,
        'min': 2.26,
        'max': 19.83,
        'night': 10.08,
        'eve': 11.05,
        'morn': 3.79},
       'feels_like': {'day': 9.14, 'night': 3.63, 'eve': 11.05, 'morn': -8.52},
       'pressure': 1016,
       'humidity': 71,
       'dew_point': 15.62,
       'wind_speed': 8.43,
       'wind_deg': 300,
       'wind_gust': 16.02,
       'weather': [{'id': 600,
         'main': 'Snow',
         'description': 'light snow',
         'icon': '13d'}],
       'clouds': 56,
       'pop': 0.33,
       'snow': 0.51,
       'uvi': 2.29},
      {'dt': 1644508800,
       'sunrise': 1644493928,
       'sunset': 1644530813,
       'moonrise': 1644510840,
       'moonset': 1644478500,
       'moon_phase': 0.31,
       'temp': {'day': 21.81,
        'min': 8.8,
        'max': 22.01,
        'night': 9.46,
        'eve': 16.41,
        'morn': 11.68},
       'feels_like': {'day': 15.03, 'night': 0.05, 'eve': 9.25, 'morn': 5.83},
       'pressure': 1006,
       'humidity': 94,
       'dew_point': 29.3,
       'wind_speed': 6.2,
       'wind_deg': 272,
       'wind_gust': 17,
       'weather': [{'id': 600,
         'main': 'Snow',
         'description': 'light snow',
         'icon': '13d'}],
       'clouds': 94,
       'pop': 0.7,
       'snow': 2.27,
       'uvi': 1.1},
      {'dt': 1644595200,
       'sunrise': 1644580246,
       'sunset': 1644617298,
       'moonrise': 1644599520,
       'moonset': 1644568620,
       'moon_phase': 0.34,
       'temp': {'day': 15.17,
        'min': 2.52,
        'max': 16.65,
        'night': 11.16,
        'eve': 14.95,
        'morn': 5.09},
       'feels_like': {'day': 9.57, 'night': 2.14, 'eve': 7.18, 'morn': -3.42},
       'pressure': 1014,
       'humidity': 76,
       'dew_point': 17.38,
       'wind_speed': 5.55,
       'wind_deg': 191,
       'wind_gust': 11.25,
       'weather': [{'id': 802,
         'main': 'Clouds',
         'description': 'scattered clouds',
         'icon': '03d'}],
       'clouds': 47,
       'pop': 0.34,
       'uvi': 1.75},
      {'dt': 1644681600,
       'sunrise': 1644666563,
       'sunset': 1644703782,
       'moonrise': 1644688800,
       'moonset': 1644658320,
       'moon_phase': 0.37,
       'temp': {'day': 21.24,
        'min': -10.28,
        'max': 21.61,
        'night': -10.28,
        'eve': 7.41,
        'morn': 19.63},
       'feels_like': {'day': 12.07, 'night': -22.88, 'eve': -5.19, 'morn': 10.44},
       'pressure': 1010,
       'humidity': 98,
       'dew_point': 29.59,
       'wind_speed': 10.74,
       'wind_deg': 267,
       'wind_gust': 36.6,
       'weather': [{'id': 600,
         'main': 'Snow',
         'description': 'light snow',
         'icon': '13d'}],
       'clouds': 100,
       'pop': 0.66,
       'snow': 2.45,
       'uvi': 0.74},
      {'dt': 1644768000,
       'sunrise': 1644752878,
       'sunset': 1644790266,
       'moonrise': 1644778560,
       'moonset': 1644747720,
       'moon_phase': 0.4,
       'temp': {'day': -4.45,
        'min': -12.17,
        'max': 0.68,
        'night': -6.97,
        'eve': 0.23,
        'morn': -11.9},
       'feels_like': {'day': -4.45, 'night': -6.97, 'eve': 0.23, 'morn': -24.5},
       'pressure': 1029,
       'humidity': 65,
       'dew_point': -6.56,
       'wind_speed': 6.91,
       'wind_deg': 319,
       'wind_gust': 9.95,
       'weather': [{'id': 804,
         'main': 'Clouds',
         'description': 'overcast clouds',
         'icon': '04d'}],
       'clouds': 100,
       'pop': 0,
       'uvi': 1},
      {'dt': 1644854400,
       'sunrise': 1644839191,
       'sunset': 1644876749,
       'moonrise': 1644868680,
       'moonset': 1644836640,
       'moon_phase': 0.44,
       'temp': {'day': -5.12,
        'min': -13.97,
        'max': -2,
        'night': -9.49,
        'eve': -3.84,
        'morn': -10.5},
       'feels_like': {'day': -16.47,
        'night': -19.82,
        'eve': -16.44,
        'morn': -19.3},
       'pressure': 1020,
       'humidity': 69,
       'dew_point': -6.23,
       'wind_speed': 6.2,
       'wind_deg': 308,
       'wind_gust': 8.72,
       'weather': [{'id': 801,
         'main': 'Clouds',
         'description': 'few clouds',
         'icon': '02d'}],
       'clouds': 18,
       'pop': 0,
       'uvi': 1},
      {'dt': 1644940800,
       'sunrise': 1644925504,
       'sunset': 1644963233,
       'moonrise': 1644959040,
       'moonset': 1644925140,
       'moon_phase': 0.47,
       'temp': {'day': -2.83,
        'min': -8.66,
        'max': 1.02,
        'night': -2.72,
        'eve': 0.75,
        'morn': -5.62},
       'feels_like': {'day': -15.43,
        'night': -11.79,
        'eve': -7.58,
        'morn': -16.47},
       'pressure': 1030,
       'humidity': 79,
       'dew_point': -0.74,
       'wind_speed': 9.37,
       'wind_deg': 303,
       'wind_gust': 26.06,
       'weather': [{'id': 600,
         'main': 'Snow',
         'description': 'light snow',
         'icon': '13d'}],
       'clouds': 100,
       'pop': 0.26,
       'snow': 0.62,
       'uvi': 1}]}



### Fetch for Many Locations

Using the same scaffolding as the Wikipedia asynchronous scrape, the helper code for the main streamlit app also relies on `httpx` to fetch 48 responses quickly.


```python

async def async_get_one_call_data(client: httpx.AsyncClient, lat: float, lon: float) -> dict:
    """Given http client and valid lat lon, retrieves open weather "One call" API data

    Args:
        client (httpx.AsyncClient): To make requests. See httpx docs
        lat (float): lat of the desired location
        lon (float): lon of the desired location

    Returns:
        dict: json response from Open Weather One Call
    """
    endpoint = get_one_call_endpoint(lat, lon)
    response = await client.get(endpoint)
    return response.json()


async def gather_one_call_weather_data(lat_lon_pairs: list) -> list:
    """Given list of tuples of lat, lon pairs, will asynchronously fetch the one call open weather api data for those pairs

    Args:
        lat_lon_pairs (list): Destinations to get data for

    Returns:
        list: List of dictionaries which are json responses from open weather
    """
    async with httpx.AsyncClient() as client:
        tasks = [
            asyncio.ensure_future(async_get_one_call_data(client, lat, lon))
            for lat, lon in lat_lon_pairs
        ]
        one_call_weather_data = await asyncio.gather(*tasks)
        return one_call_weather_data
```

## Web App Component

Goals from the start:
- Usable UI for comparing / viewing weather on 48 locations (mobile-friendly for hikers)
- Not sluggish to load data or click through page after page to get different mountains / times
- Good uptime

Other technical considerations:
- Obeying API limits
    - API key security
- Streamlit resource limits
    - Cloud host or self host

### Caching Data

There are 2 main points of loading data in the app:

- Load the list of mountains, heights, lats, lons
- Fetch live data from OpenWeatherMap for all locations

With Streamlit, decorating a function with `@st.cache()` will save the computed result so that it can be loaded faster by the next user!

#### Caching Mountain Data

The first list is static, and purely for convenience of fetching columns I load it in with `pandas`. (In hindsight I could have at least reset the index after sorting).

Leaving the default arguments lets this dataset get cached indefinitely (until the app gets shut down / restarted)

*note:* `st.cache` decorators commented out in notebook


```python
import pandas as pd
# import streamlit as st

#@st.cache()
def load_metadata() -> pd.DataFrame:
    """Function to read mountain lat, lon, and other metadata and cache results

    Returns:
        pd.DataFrame: df containing information for 48 mountains
    """
    df = pd.read_csv("./data/mountains.csv")
    df = df.sort_values("name")
    return df

load_metadata().head()
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
      <th>name</th>
      <th>link</th>
      <th>lat</th>
      <th>lon</th>
      <th>height_ft</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>29</th>
      <td>Bondcliff</td>
      <td>https://en.wikipedia.org/wiki/Bondcliff</td>
      <td>44.153056</td>
      <td>-71.531111</td>
      <td>4265</td>
    </tr>
    <tr>
      <th>35</th>
      <td>Cannon Mountain</td>
      <td>https://en.wikipedia.org/wiki/Cannon_Mountain_...</td>
      <td>44.156389</td>
      <td>-71.698333</td>
      <td>4100</td>
    </tr>
    <tr>
      <th>8</th>
      <td>Carter Dome</td>
      <td>https://en.wikipedia.org/wiki/Carter_Dome</td>
      <td>44.267222</td>
      <td>-71.178889</td>
      <td>4832</td>
    </tr>
    <tr>
      <th>33</th>
      <td>East Peak Mount Osceola</td>
      <td>https://en.wikipedia.org/wiki/East_Peak_Mount_...</td>
      <td>44.006111</td>
      <td>-71.520556</td>
      <td>4340</td>
    </tr>
    <tr>
      <th>43</th>
      <td>Galehead Mountain</td>
      <td>https://en.wikipedia.org/wiki/Galehead_Mountain</td>
      <td>44.185278</td>
      <td>-71.573611</td>
      <td>4024</td>
    </tr>
  </tbody>
</table>
</div>



#### Caching Weather Data

With this dataset I don't want to cache things indefinitely.
In fact, we want it to update as often as the API limits will allow us to query it!

Setting a `ttl` or "Time To Live" value in `st.cache(ttl=...)` will cause the cache to bust if the precomputed result is longer than the provided time.

We'll set the `ttl` to 60 minutes to respect OpenWeatherMaps.

This means that if 100 users all open the app within 59 minutes of one another then only 1 request to `load_data()` would actually go to OpenWeatherMaps. The other 99 requests would use the cached result.

When any user opens it 61 minutes after the first user, the cache will be busted and another request to OpenWeatherMaps will refresh all of the 48 mountains' weather data in the app.


```python
pass
# @st.cache(ttl=60 * 60)
def load_data(lat_lon_pairs: list) -> list:
    """Function to fetch Open Weather data and cache results

    Args:
        lat_lon_pairs (list): Destinations to get data for

    Returns:
        list: List of dictionaries which are json responses from open weather
    """
    data = asyncio.run(gather_one_call_weather_data(lat_lon_pairs))
    return data
```

### Bonuses

#### Display future forecast

Hikers don't need to know just the weather right now.
They also need to know the next few hours' forecast.

The OpenWeatherMaps data provides temperature and weather event forecasts hourly.

So how about a row across the screen with 5 hours of data in 5 even columns.

Feels good on desktop, but a horrendous amount of scrolling past locations you don't care about on mobile.

`st.expander()` provides a way to tuck sections away in a drop down hide/expand section.

Then using `st.columns()` we can get an iterator over `x` amount of columns.
Zipping this with the hourly results starting from the next hour gives a nice way to match up layout to data.
It also gives some flexibility for how many columns to include.

```py
response = load_data()[0]
current_temperature = round(response["current"]["temp"], 1)

with st.expander("Expand for future forecast:"):
    for col, entry in zip(st.columns(5), response["hourly"][1:]):
        col.write(f"{clean_time(entry['dt'])}")
        
        temperature = round(entry["temp"], 1)
        col.metric(
            "Temp (F)", temperature, round(temperature - current_temperature, 1)
        )
        current_temperature = temperature
```

#### Jump Link Table

Using the app on mobile even with expander sections was too much scrolling.

I thought a Markdown table of links would be more straightforward, but I wound up doing a bunch of string mangling to get it running.

Having anchors on most commands such as `st.title()` is great for in-page navigation


```python
def get_mtn_anchor(mountain: str) -> str:
    anchor = mountain.lower().replace(" ", "-")
    return f"[{mountain}](#{anchor})"

mountains = load_metadata()

table = []

table.append("| Mountains |  |  |")
table.append("|---|---|---|")
for left, middle, right in zip(
    mountains.name[::3], mountains.name[1::3], mountains.name[2::3]
):
    table.append(
        f"| {get_mtn_anchor(left)} | {get_mtn_anchor(middle)} | {get_mtn_anchor(right)} |"
    )
# st.markdown("\n".join(table))
"\n".join(table)
```




    "| Mountains |  |  |\n|---|---|---|\n| [Bondcliff](#bondcliff) | [Cannon Mountain](#cannon-mountain) | [Carter Dome](#carter-dome) |\n| [East Peak Mount Osceola](#east-peak-mount-osceola) | [Galehead Mountain](#galehead-mountain) | [Middle Carter Mountain](#middle-carter-mountain) |\n| [Middle Tripyramid](#middle-tripyramid) | [Mount Adams](#mount-adams) | [Mount Bond](#mount-bond) |\n| [Mount Cabot](#mount-cabot) | [Mount Carrigain](#mount-carrigain) | [Mount Eisenhower](#mount-eisenhower) |\n| [Mount Field](#mount-field) | [Mount Flume](#mount-flume) | [Mount Garfield](#mount-garfield) |\n| [Mount Hale](#mount-hale) | [Mount Hancock](#mount-hancock) | [Mount Hancock](#mount-hancock) |\n| [Mount Isolation](#mount-isolation) | [Mount Jackson](#mount-jackson) | [Mount Jefferson](#mount-jefferson) |\n| [Mount Lafayette](#mount-lafayette) | [Mount Liberty](#mount-liberty) | [Mount Lincoln](#mount-lincoln) |\n| [Mount Madison](#mount-madison) | [Mount Monroe](#mount-monroe) | [Mount Moosilauke](#mount-moosilauke) |\n| [Mount Moriah](#mount-moriah) | [Mount Osceola](#mount-osceola) | [Mount Passaconaway](#mount-passaconaway) |\n| [Mount Pierce](#mount-pierce) | [Mount Tecumseh](#mount-tecumseh) | [Mount Tom](#mount-tom) |\n| [Mount Washington](#mount-washington) | [Mount Waumbek](#mount-waumbek) | [Mount Whiteface](#mount-whiteface) |\n| [Mount Willey](#mount-willey) | [Mount Zealand](#mount-zealand) | [North Kinsman Mountain](#north-kinsman-mountain) |\n| [North Tripyramid](#north-tripyramid) | [North Twin Mountain](#north-twin-mountain) | [Owl's Head (Franconia)](#owl's-head-(franconia)) |\n| [South Carter Mountain](#south-carter-mountain) | [South Kinsman Mountain](#south-kinsman-mountain) | [South Twin Mountain](#south-twin-mountain) |\n| [West Bond](#west-bond) | [Wildcat D Mountain](#wildcat-d-mountain) | [Wildcat Mountain](#wildcat-mountain) |"


