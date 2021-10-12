import streamlit as st
import pandas as pd
import numpy as np
import database as db
from queries import qry
from datetime import datetime


@st.experimental_memo()     
def get_violations(_conn):
    sql = qry['all_violations']
    df, ok = db.execute_query(qry['all_violations'], _conn)
    df['timestamp'] = pd.to_datetime(df['timestamp'], format="%d.%m.%y %H:%M:%S")
    return df

def get_stations(_conn):
    sql = qry['all_stations']
    df, ok = db.execute_query(qry['all_stations'], _conn)
    df['messbeginn'] = pd.to_datetime(df['messbeginn'])
    df['messende'] = pd.to_datetime(df['messende'])
    return df

def summary_all(conn):
    def append_row(df, par, value, fmt):
        if isinstance(value, datetime):
            df = df.append({'Parameter':par, 'Wert':value.strftime(fmt)}, ignore_index=True)
        else:
            df = df.append({'Parameter':par, 'Wert':format(value,fmt)}, ignore_index=True)
        return df    

    st.markdown('### Allgemeine Kennzahlen')
    df_table = pd.DataFrame(columns=['Parameter', 'Wert'])
    df_measurements= get_violations(conn)
    stations = get_stations(conn)
    x = len(stations['messung_id'].unique())
    f_int = '.0f'
    f_dec = '.1f'
    f_pct = '.1%'
    f_dat = '%d.%m.%Y'
    x = len(pd.unique(stations[['messung_id', 'richtung']].values.ravel()))
    df_table = append_row(df_table, 'Anzahl Messstationen', x, f_int)
    df_table = append_row(df_table,'Anzahl Richtungen',len(stations), f_int)
    groupby_fields_fields = ['messung_id', 'ort','strasse','hausnummer','messbeginn','messende']
    df_table = append_row(df_table,'Erste Messung',stations['messbeginn'].min(), f_dat)
    df_table = append_row(df_table,'Letzte Messung',stations['messende'].max(), f_dat)
    df_time = stations.groupby(groupby_fields_fields)['fahrzeuge'].agg(['sum']).reset_index()
    df_time['num_of_days'] = (df_time['messende'] - df_time['messbeginn']).astype('timedelta64[h]') / 24
    df_table = append_row(df_table,'Anzahl Tage total',df_time['num_of_days'].sum(),f_int)
    df_table = append_row(df_table,'Mittlere. Anzahl Tage pro Messstation',df_time['num_of_days'].mean(),f_dec)
    df_table = append_row(df_table,'Anzahl Fahrzeuge',stations['fahrzeuge'].sum(),f_int)
    df_table = append_row(df_table,'Anzahl Übertretungen',len(df_measurements),f_int)
    df_table = append_row(df_table,'Max. Übertretungsquote', stations['uebertretungsquote'].max()/100,f_pct)
    df_table = append_row(df_table,'Mittlere Übertretungsquote', stations['uebertretungsquote'].mean()/100,f_pct)
    
    st.write(df_table)


def dummy():
    # df = pd.read_parquet('./violations.parquet')
    # st.write(df.head(100))
    st.info("noch nicht implementiert, kommt bald!")

def show_menu(texts, conn):    

    dic_menu = {'1': 'Allgemeine Kennzahlen', '2': 'Statistik nach Messstation', '3': 'Statistik nach Wochentag', '4': 'Statistik nach Tageszeit'}
    menu_item = st.sidebar.selectbox('Optionen', list(dic_menu.keys()),
        format_func=lambda x: dic_menu[x])   
    if menu_item == '1':
        summary_all(conn)
    elif menu_item ==  '2':
        dummy()
    elif menu_item ==  '3':
        dummy()
    elif menu_item ==  '4':
        dummy()
                