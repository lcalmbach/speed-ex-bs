import streamlit as st
import pandas as pd
import numpy as np
import database as db
from queries import qry
from datetime import datetime

f_int = '.0f'
f_dec = '.1f'
f_pct = '.1%'
f_dat = '%d.%m.%Y'

@st.experimental_memo()     
def get_violations(_conn):
    df, ok = db.execute_query(qry['all_violations'], _conn)
    df['timestamp'] = pd.to_datetime(df['timestamp'], format="%d.%m.%y %H:%M:%S")
    return df

# @st.experimental_memo()     
def get_stations(_conn):
    df, ok = db.execute_query(qry['all_stations'], _conn)
    df['messbeginn'] = pd.to_datetime(df['messbeginn'])
    df['messende'] = pd.to_datetime(df['messende'])
    df[['strasse','hausnummer']] = df[['strasse','hausnummer']].fillna ('').astype(str)
    return df

def get_lst_ort(stations):
    return stations['ort'].unique()

@st.experimental_memo() 
def get_dic_stations(stations): 
    stations['value'] = stations["strasse"].str.cat(stations['hausnummer'], sep=" ")
    stations['value'] = stations["value"].str.cat(stations['ort'], sep=", ")
    #stations = stations.sort_values('value')
    return dict(zip(stations['messung_id'], stations['value']))

def append_row(df, par, value, fmt):
    if isinstance(value, datetime):
        df = df.append({'Parameter':par, 'Wert':value.strftime(fmt)}, ignore_index=True)
    else:
        df = df.append({'Parameter':par, 'Wert':format(value,fmt)}, ignore_index=True)
    return df    

def summary_all(conn):
    df_table = pd.DataFrame(columns=['Parameter', 'Wert'])
    df_measurements= get_violations(conn)
    stations = get_stations(conn)
    x = len(stations['messung_id'].unique())
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
    return df_table

 
def station_stats(conn):
    def get_filter():
        dic_stations = get_dic_stations(stations)
        station_sel = st.sidebar.multiselect("Wähle eine oder mehrere Messstationen", dic_stations.keys(), format_func=lambda x: dic_stations[x])   
        return station_sel
    
    def get_station_stat(df, par):
        def percentile(n):
            def percentile_(x):
                return np.percentile(x, n)
            percentile_.__name__ = 'percentile_%s' % n
            return percentile_
            
        #group_by_fields = ['messung_id', 'strasse', 'hausnummer', 'ort', 'richtung']
        group_by_fields = ['messung_id']
        _stats = df.groupby(group_by_fields)[par].agg(['min','max','mean', 'std', 'count', percentile(5), percentile(25), percentile(50), percentile(75), percentile(90), percentile(95), percentile(99)]).reset_index()
        val_vars = _stats.drop(['messung_id'], axis=1).columns
        _stats = pd.melt(_stats, id_vars=['messung_id'], value_vars=val_vars)
        _stats = _stats.drop(['messung_id'], axis=1)
        return _stats

    df_measurements= get_violations(conn)
    stations = get_stations(conn)
    
    station_sel = get_filter()
    par = st.sidebar.selectbox('Wähle einen Parameter',['geschwindigkeit'])
    df_filtered = df_measurements.query("messung_id in @station_sel")
    for station in station_sel:
        df_filtered = df_measurements.query("messung_id==@station")
        st.write(get_dic_stations(stations)[station])
        st.write(get_station_stat(df_filtered, par))
    

def dummy():
    # df = pd.read_parquet('./violations.parquet')
    # st.write(df.head(100))
    st.info("noch nicht implementiert, kommt bald!")

def show_menu(texts, conn):    

    dic_menu = {'1': 'Allgemeine Kennzahlen', '2': 'Statistik nach Messstation', '3': 'Statistik nach Wochentag', '4': 'Statistik nach Tageszeit'}
    
    menu_item = st.sidebar.selectbox('Optionen', list(dic_menu.keys()),
        format_func=lambda x: dic_menu[x])   
    st.markdown(f"### {dic_menu[menu_item]}")
    if menu_item == '1':
        df = summary_all(conn)
        st.write(df)
    elif menu_item ==  '2':
        station_stats(conn)
    elif menu_item ==  '3':
        dummy()
    elif menu_item ==  '4':
        dummy()
    
                