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


acv_range = st.radio(
    'Choose the acv range'
    ,('< $500', '$500 - $3k', '$3k - $10k', '> $10k','All Accounts'))


if acv_range == '< $500':
    filtered_data = data.loc[(data['active_acv'] > 0) & (data['active_acv'] < 500)]
    acv_filter = '< $500'
elif acv_range =='$500 - $3k':
    filtered_data = data.loc[(data['active_acv'] >=500) & (data['active_acv'] < 3000)]
    acv_filter = '$500 - $3k'
elif acv_range == '$3k - $10k':
    filtered_data = data.loc[(data['active_acv'] >= 3000) & (data['active_acv'] < 10000)]
    acv_filter = '$3k - $10k'
elif acv_range == '> $10k':
    filtered_data = data.loc[(data['active_acv'] >= 10000)]
    acv_filter = '$3k - $10k'
else:
    filtered_data = data
    acv_filter = 'of any value'

filtered_data = pd.DataFrame(filtered_data, columns=['account_name','city','state','zip','lat','lon','active_acv'])   


state = st.multiselect(
    'Choose the states that you want to filter'
    ,sorted(set(filtered_data['state'].str.lower())))

dummy = filtered_data.loc[filtered_data['state'].str.lower().isin(state)]  
if dummy.empty:
    filtered = filtered_data
    state_filter = 'any state'
else:
    filtered = dummy
    
converted_list = [str(element) for element in state]
state_filter = ",".join(converted_list)
filtered_data = pd.DataFrame(filtered, columns=['account_name','city','state','zip','lat','lon','active_acv'])  

city = st.multiselect(
    'Choose the cities that you want to filter'
    ,sorted(set(filtered_data['city'].str.lower())))

dummy = filtered_data.loc[filtered_data['city'].str.lower().isin(city)]  
if dummy.empty:
    filtered = filtered_data
    city_filter = 'any city'
else:
    filtered = dummy
    
converted_list = [str(element) for element in city]
city_filter = ",".join(converted_list)
filtered_data = pd.DataFrame(filtered, columns=['account_name','city','state','zip','lat','lon','active_acv'])  

st.write("Total WeVideo Accounts with Active ACV",acv_filter,", in State(s)",state_filter"and in City(s)",city_filter,"is (are)",len(filtered_data)) 
st.dataframe(filtered_data, use_container_width = True)
scatterLayer = pdk.Layer(
    'ScatterplotLayer',      
    filtered_data,
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
