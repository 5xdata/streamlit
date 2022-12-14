import pandas as pd
import streamlit as st
import pydeck as pdk
import numpy as np

st.title('US Accounts')

acv_data = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vTUgpBzoRCnUYYA85IKII2TwgLHsPAlKoLvZ5LByqP5hSCPNzkMZYH2wVdKezUPXdmdpdU3FKF1hAtC/pub?gid=0&single=true&output=csv'

@st.cache
def load_data():
    data = pd.read_csv(acv_data)
    data.rename(columns = {'billing_latitude':'lat', 'billing_longitude':'lon'}, inplace = True)
    return data

data_load_state = st.text('Loading data...')
data = load_data()
data_load_state.text("Done by Naveen!!")

if st.checkbox('Show raw data'):
    st.subheader('Raw data')
    st.write(data)
    
st.subheader('Map of all US Accounts of WeVideo with active ACV')

viewState = pdk.ViewState(
    longitude=-112.8591427000004, latitude=36.365390013524475, zoom=3.50, bearing=0, pitch=0
)
mapStyle = 'mapbox://styles/wevideo/claavllul000m14qw11d227ne'

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

hexLayer = pdk.Layer(
    'HexagonLayer',
    data=data,
    get_position='[lon, lat]',
    radius='[active_acv]',
    elevation_scale=4,
    elevation_range=[0, 10000],
    pickable=True,
    extruded=True,
    )
        
toolTip = {
    "html": "<b>Account - My Wevideo Account</b><br><b>Billing Address - {billing_address}</b><br><b>Active ACV - {active_acv}</b>",
    "style": {"background": "grey", "color": "white", "font-family": '"Helvetica Neue", Arial', "z-index": "10000", "max-width": "25%"},
}

st.pydeck_chart(pdk.Deck(
    map_style=None,
    initial_view_state=viewState,
    layers=[hexLayer, scatterLayer],
    tooltip= toolTip
    ))
