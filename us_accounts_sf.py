import pandas as pd
import streamlit as st
import pydeck as pdk
import numpy as np
import snowflake.connector

# Initialize connection.
# Uses st.experimental_singleton to only run once.
@st.experimental_singleton
def init_connection():
    return snowflake.connector.connect(
        **st.secrets["snowflake"], client_session_keep_alive=True
    )

conn = init_connection()

# Perform query.
# Uses st.experimental_memo to only rerun when the query changes or after 10 min.
@st.experimental_memo(ttl=600)
def run_query(query):
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()

rows = run_query("SELECT substr(account_name,1,3) as account_name, split_part(billing_address,',',3) as city, split_part(billing_address,',',4) as state, split_part(billing_address,',',-1) as zip, billing_latitude, billing_longitude, sum(acv) as active_acv from wevideo_analytics.salesforce.active_acv where billing_latitude is not null and billing_longitude is not null and date = last_day(current_date) group by 1,2,3,4,5,6 order by 7 desc ;")

st.title('US Accounts')
# Print results.

@st.cache
def load_data():
    return pd.DataFrame(rows, columns=['account_name','city','state','zip','lat','lon','active_acv'])

data_load_state = st.text('Loading data...')
data = load_data()
data_load_state.text("Data refreshed and loaded !!")


if st.checkbox('Show raw data'):
    st.subheader('Raw data')
    st.checkbox("Full Screen", value=False, key="use_container_width")
    st.dataframe(data, use_container_width=st.session_state.use_container_width)
    
st.subheader('Map of all US Accounts of WeVideo with active ACV')

viewState = pdk.ViewState(
    longitude=-112.8591427000004, latitude=36.365390013524475, zoom=3.50, bearing=0, pitch=0
)
#mapStyle = 'mapbox://styles/wevideo/claavllul000m14qw11d227ne'

#acv_to_filter = st.slider('active_acv', 0, 20000, 1000)
#filtered_data = data[data['active_acv'] == acv_to_filter]

city = st.multiselect(
    'Choose the cities that you want to filter'
    ,sorted(set(data['city'].str.lower())))

state = st.multiselect(
    'Choose the states that you want to filter'
    ,sorted(set(data['state'].str.lower())))

filtered_data = data.loc[data['city'].str.lower().isin(city)]
filtered_data = data.loc[data['state'].str.lower().isin(state)]
st.dataframe(filtered_data, use_container_width = True)


scatterLayer = pdk.Layer(
    'ScatterplotLayer',      
    data,
    get_position='[lon, lat]',
    pickable=True,
    opacity=0.2,
    stroked=True,
    filled=True,
    radius_scale=6,
    radius_min_pixels=1,
    radius_max_pixels=10,
    line_width_min_pixels=1,
    get_radius='[active_acv]',
    get_fill_color=[255, 100, 80, 140],
    get_line_color=[0, 0, 0],
    )

toolTip = {
    "html": "<b>Account Name (3 charac) - {account_name}</b><br><b>City - {city}</b><br><b>State - {state}</b><br><b>Zip - {zip}</b><br><b>Active ACV - {active_acv}</b>",
    "style": {"background": "grey", "color": "white", "font-family": '"Helvetica Neue", Arial', "z-index": "10000", "max-width": "30%"},
}

st.pydeck_chart(pdk.Deck(
    map_style=None,
    initial_view_state=viewState,
    layers=[scatterLayer],
    tooltip= toolTip
    ))
