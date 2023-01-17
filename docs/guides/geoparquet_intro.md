---
title: GeoParquet Intro
description: Exploring columnar + geospatial data.
links:
  - Prerequisites:
    - setup_python
---

See it Live: [https://geoparquet.streamlit.app/](https://geoparquet.streamlit.app/)

Repo: [https://github.com/gerardrbentley/explore-geoparquet](https://github.com/gerardrbentley/explore-geoparquet)

## Idea

Start with [World Bank country data](https://datacatalog.worldbank.org/search/dataset/0038272/World-Bank-Official-Boundaries) source.
Use GeoPandas to load the source GeoJSON into memory.
Use GeoPandas to write parquet and/or feather files.

Use GeoPandas to load parquet data in Streamlit application.
Display dataframe
Display spatial data with GeoPandas plotting + Folium

## Start

```sh
mkdir geoparquet
cd geoparquet 
touch streamlit_app.py requirements.txt convert_to_parquet.py
echo 'venv' > .gitignore
git init
python -m venv venv
. ./venv/bin/activate
python -m pip install geopandas pyarrow streamlit streamlit-folium
# dev
python -m pip install notebook
# for deploy
python -m pip install -r requirements.txt
```

## Conversion

Couldn't load zip off the bat on my local.
Unzipped spatial folder and that directory worked fine.

```py
import geopandas
import pyarrow

gdf = geopandas.read_file(SOURCE_SPATIAL_PATH)
gdf.to_parquet(PARQUET_PATH)
gdf.to_feather(FEATHER_PATH)
```

Timed loading from directory and parquet / feather.
Parquet and Feather were similarly faster, with feather being slightly smaller fil size.

## Data Display

Streamlit doesn't happily display geospatial data in dataframes out of the box.
So displaying the data table means we won't include geometry.

```py
import streamlit as st
import geopandas
import folium
import pyarrow
from streamlit_folium import st_folium


@st.experimental_singleton
def load_country_data(file_path: str) -> geopandas.GeoDataFrame:
    gdf = geopandas.read_parquet(file_path)
    return gdf

countries = load_country_data("countries.parquet")
cols = countries.columns
data_cols = cols[~cols.isin(["geometry"])]

st.dataframe(countries[data_cols])
```

That's all that's needed to the non-geospatial columns.

## Map Display

Streamlit folium helps to connect GeoPandas with leaflet and streamilt.

```py
m = folium.Map(location=[0, 0], zoom_start=2)

column_choice = st.selectbox("Column to Display", cols, cols.get_loc("POP_RANK"))
tooltip_columns = st.multiselect("Columns for Tooltip", cols, default_display_cols)

countries.explore(column_choice, cmap="Blues", m=m, tooltip=tooltip_columns)  

st_folium(m, returned_objects=[])
```

Passing in a list of `default_display_cols` makes the map a little less noisy when hovering.
