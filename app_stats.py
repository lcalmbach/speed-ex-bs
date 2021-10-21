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

# @st.experimental_memo()     
def get_stations(_conn):
    statfields =['messung_id','address','ort','start_date','end_date','zone','richtung_strasse','richtung','fahrzeuge','uebertretungsquote','v50','v85']
    df, ok, err_msg = db.execute_query(qry['all_stations'], _conn)
    df = helper.format_time_columns(df,('start_date','end_date'),cn.FORMAT_DMY)
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
    stations['value'] = stations["address"].str.cat(stations['ort'], sep=", ")
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

    stations = get_stations(conn)
    station_sel = get_filter()
    df_filtered = stations.query("messung_id in @station_sel") if len(station_sel) > 0 else stations
    return df_filtered
    

def dummy():
    # df = pd.read_parquet('./violations.parquet')
    # st.write(df.head(100))
    st.info("noch nicht implementiert, kommt bald!")

def show_menu(texts, conn):    

    menu = ['Allgemeine Kennzahlen', 'Statistik nach Messstation', 'Statistik nach Wochentag', 'Statistik nach Tageszeit']
    
    menu_item = st.sidebar.selectbox('Optionen', menu)
    st.markdown(f"### {menu_item}")
    if menu_item == menu[0]:
        df = summary_all(conn)
        st.write(df)
    elif menu_item ==  menu[1]:
        df = station_stats(conn)
        helper.show_table(df,[])
    elif menu_item ==  menu[2]:
        dummy()
    elif menu_item ==  menu[3]:
        dummy()
    
                