import streamlit as st
import pandas as pd
import numpy as np
import database as db
from queries import qry
from datetime import datetime
import const as cn
import helper

f_int = '.0f'
f_dec = '.1f'
f_pct = '.1%'
f_dat = '%d.%m.%Y'

def convert_to_local_time(fld):
    fld = pd.to_datetime(fld, utc=True)

    return fld

@st.experimental_memo()     
def get_violation_count(_conn):
    df, ok, err_msg = db.execute_query(qry['exceedance_count'], _conn)
    return df.iloc[0]['count']

@st.experimental_memo()     
def get_violations(_conn):
    df, ok, err_msg = db.execute_query(qry['exceedance_count'], _conn)
    return df.iloc[0]['count']

@st.experimental_memo()     
def get_locations(_conn):
    """Each locations can have 1 or 2 directions, each location 1 direction is a station

    Args:
        none

    Returns:
        [pd.DataFrame]: table of locations
    """
    statfields =['messung_id','address','ort','start_date','end_date','zone','richtung_strasse','fahrzeuge','uebertretungsquote','v50','v85']
    df, ok, err_msg = db.execute_query(qry['all_stations'], _conn)
    df = helper.format_time_columns(df,('start_date','end_date'),cn.FORMAT_DMY)
    df['address'] = df['address'].astype(str)
    df['richtung_strasse'] = df['richtung_strasse'].astype(str)
    df['fahrzeuge'] = df['fahrzeuge'].astype(int)
    df['v50'] = df['v50'].astype(int)
    df['v85'] = df['v85'].astype(int)
    df = df[statfields]
    return df


@st.experimental_memo()     
def get_stations(_conn):
    statfields =['station_id','messung_id','address','ort','start_date','end_date','zone','richtung_strasse','richtung','fahrzeuge','uebertretungsquote','v50','v85']
    df, ok, err_msg = db.execute_query(qry['all_stations'], _conn)
    df['address'] = df['address'].astype(str)
    df['richtung_strasse'] = df['richtung_strasse'].astype(str)
    df['fahrzeuge'] = df['fahrzeuge'].astype(int)
    df['v50'] = df['v50'].astype(int)
    df['v85'] = df['v85'].astype(int)
    df = df[statfields]
    return df

def get_lst_ort(stations):
    return stations['ort'].unique()

@st.experimental_memo() 
def get_dic_stations(stations): 
    stations['value'] = stations["address"].str.cat([stations['ort'], stations['richtung_strasse']], sep=", ")
    stations = stations.sort_values('value')
    return dict(zip(stations['station_id'], stations['value']))

@st.experimental_memo() 
def get_dic_locations(locations): 
    locations['value'] = locations["address"].str.cat(locations['ort'], sep=", ")
    #stations = stations.sort_values('value')
    return dict(zip(locations['station_id'], locations['value']))

def append_row(df, par, value, fmt):
    if isinstance(value, datetime):
        df = df.append({'Parameter':par, 'Wert':value.strftime(fmt)}, ignore_index=True)
    else:
        df = df.append({'Parameter':par, 'Wert':format(value,fmt)}, ignore_index=True)
    return df    

def summary_all(conn):
    df_table = pd.DataFrame(columns=['Parameter', 'Wert'])
    exceedance_count= get_violation_count(conn)
    stations = get_stations(conn)
    x = len(stations['messung_id'].unique())
    x = len(pd.unique(stations[['messung_id', 'richtung']].values.ravel()))
    df_table = append_row(df_table, 'Anzahl Messstationen', x, f_int)
    df_table = append_row(df_table,'Anzahl Richtungen',len(stations), f_int)
    groupby_fields = ['messung_id', 'ort','address','start_date','end_date']
    df_table = append_row(df_table,'Erste Messung',stations['start_date'].min(), f_dat)
    df_table = append_row(df_table,'Letzte Messung',stations['end_date'].max(), f_dat)

    df_time = stations.groupby(groupby_fields)['fahrzeuge'].agg(['sum']).reset_index()
    df_time['num_of_days'] = (df_time['end_date'] - df_time['start_date']).astype('timedelta64[h]') / 24
    df_table = append_row(df_table,'Anzahl Tage total',df_time['num_of_days'].sum(),f_int)
    df_table = append_row(df_table,'Mittlere Anzahl Tage pro Messstation',df_time['num_of_days'].mean(),f_dec)
    df_table = append_row(df_table,'Anzahl Fahrzeuge',int(stations['fahrzeuge'].sum()),",d")
    df_table = append_row(df_table,'Anzahl Übertretungen',exceedance_count,",d")
    df_table = append_row(df_table,'Max. Übertretungsquote', stations['uebertretungsquote'].max()/100,f_pct)
    df_table = append_row(df_table,'Mittlere Übertretungsquote (Stationen)', stations['uebertretungsquote'].mean()/100,f_pct)
    
    q = exceedance_count / stations['fahrzeuge'].sum()  if exceedance_count > 0 else 0
    df_table = append_row(df_table,'Übertretungsquote (alle Messungen)', q,f_pct)
    return df_table

 
def station_stats(conn):
    def get_filter():
        dic_stations = get_dic_stations(stations)
        station_sel = st.sidebar.multiselect("Wähle eine oder mehrere Messstationen", dic_stations.keys(), format_func=lambda x: dic_stations[x])   
        return station_sel
    

    stations = get_stations(conn)
    station_sel = get_filter()
    df_filtered = stations.query("station_id in @station_sel") if len(station_sel) > 0 else stations
    df_filtered = df_filtered.drop(['station_id'], axis=1)
    return df_filtered


def weekday_stats(conn):
    def get_filter():
        dic_stations = get_dic_stations(stations)
        station_sel = st.sidebar.multiselect("Wähle eine oder mehrere Messstationen", dic_stations.keys(), format_func=lambda x: dic_stations[x])   
        return station_sel
    
    #@st.experimental_memo()     
    def get_exceedance_data():
        df, ok, err_msg = db.execute_query(qry['station_exceedances_weekday'], conn)
        return df

    def rename_columns(df):
        """Detects the weekday in the multiindex column title and generates a single index column name

        Args:
            df ([type]): [description]

        Returns:
            [type]: [description]
        """
        cols = []
        for c in df.columns:
            if c[0] == 'station_id':
                cols.append('station_id')
            elif c[1] == 'Montag':
                cols.append('Montag')
            elif c[1] == 'Dienstag':
                cols.append('Dienstag')
            elif c[1] == 'Mittwoch':
                cols.append('Mittwoch')
            elif c[1] == 'Donnerstag':
                cols.append('Donnerstag')
            elif c[1] == 'Freitag':
                cols.append('Freitag')
            elif c[1] == 'Samstag':
                cols.append('Samstag')
            else:
                cols.append('Sonntag')
        df.columns = cols
        df = df[['station_id','Montag','Dienstag','Mittwoch','Donnerstag','Freitag','Samstag','Sonntag']]
        return df


    stations = get_stations(conn)
    station_sel = get_filter()
    df_data = get_exceedance_data()
    df_filtered = df_data.query("station_id in @station_sel") if len(station_sel) > 0 else df_data
    df_filtered = helper.replace_day_ids(df_filtered, 'dow')

    df_unmelted =  df_filtered[['station_id','dow','count']].pivot(index=['station_id'], columns='dow').reset_index()
    df_unmelted = rename_columns(df_unmelted)
    df_unmelted = df_unmelted.replace({'station_id': get_dic_stations(stations)})
    df_unmelted = df_unmelted.rename(columns={'station_id': 'Messstation'})
    return df_unmelted


def hourly_stats(conn):
    def get_filter():
        dic_stations = get_dic_stations(stations)
        station_sel = st.sidebar.multiselect("Wähle eine oder mehrere Messstationen", dic_stations.keys(), format_func=lambda x: dic_stations[x])   
        return station_sel
    
    @st.experimental_memo()     
    def get_exceedance_data():
        df, ok, err_msg = db.execute_query(qry['station_exceedances_hour'], conn)
        return df

    def dissolve_multi_index(df):
        df.columns = ['station_id','00','01','02','03','04','05','06','07','08','09','10','11',
                                   '12','13','14','15','16','17','18','19','20','21','22','23']
        return df

    def get_description(df):
        text = "Hier fehlt noch eine Beschreibung dieser Tabelle"
        return text


    stations = get_stations(conn)
    station_sel = get_filter()
    df_data = get_exceedance_data()
    df_filtered = df_data.query("station_id in @station_sel") if len(station_sel) > 0 else df_data
    df_unmelted = helper.add_leading_zeros(df_filtered, 'hour',2)
    df_unmelted =  df_filtered[['station_id','hour','count']].pivot(index=['station_id'], columns='hour').reset_index()
    df_unmelted = dissolve_multi_index(df_unmelted)
    df_unmelted = df_unmelted.replace({'station_id': get_dic_stations(stations)})
    df_unmelted = df_unmelted.rename(columns={'station_id': 'Messstation'})
    text = get_description(df_unmelted)
    return df_unmelted, text
    

def show_menu(texts, conn):    

    menu = ['Allgemeine Kennzahlen', 'Statistik nach Messstation', 'Statistik nach Wochentag', 'Statistik nach Tageszeit']
    
    menu_item = st.sidebar.selectbox('Optionen', menu)
    st.markdown(f"### {menu_item}")
    text = "Hier fehlt noch eine Beschreibung dieser Tabelle"  # todo: implement
    if menu_item == menu[0]:
        df = summary_all(conn)
        helper.show_table(df,[])
    elif menu_item ==  menu[1]:
        df = station_stats(conn)
        helper.show_table(df,[])
    elif menu_item ==  menu[2]:
        df = weekday_stats(conn)
        helper.show_table(df,[])
    elif menu_item ==  menu[3]:
        df, text = hourly_stats(conn)
        helper.show_table(df,[])
    st.markdown(text,unsafe_allow_html=True)
    
                