import streamlit as st
import database as db
from queries import qry

def show_menu(texts, conn):    
    df_violations, ok = db.execute_query(qry['year_violations'], conn)
    df_stations, ok = db.execute_query(qry['year_stations'], conn)
    df_min_max,ok = db.execute_query(qry['min_max_timestamp'], conn) 
    min_timestamp = df_min_max.iloc[0]['min_timestamp'][:8]
    max_timestamp = df_min_max.iloc[0]['max_timestamp'][:8]

    st.markdown("## Geschwindigkeitsübertretungen in Basel-Stadt")
    body = texts['intro'].format(min_timestamp, max_timestamp)
    st.markdown(body)
