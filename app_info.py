import streamlit as st
import database as db
from queries import qry

def show_menu(texts, conn):    
    #df_violations, ok, err_msg = db.execute_query(qry['year_violations'], conn)
    #df_stations, ok, err_msg = db.execute_query(qry['year_stations'], conn)
    df_min_max, ok, err_msg = db.execute_query(qry['min_max_timestamp'], conn) 
    min_timestamp = df_min_max.iloc[0]['min_timestamp'].strftime('%d.%m.%y')
    max_timestamp = df_min_max.iloc[0]['max_timestamp'].strftime('%d.%m.%y')

    st.markdown("## Geschwindigkeitsübertretungen in Basel-Stadt")
    body = texts['intro'].format(min_timestamp, max_timestamp)
    parameters = texts['parameters'].format(min_timestamp, max_timestamp)
    st.markdown(body,unsafe_allow_html=True)
    with st.expander('Parameters'):
        st.markdown(parameters,unsafe_allow_html=True)
