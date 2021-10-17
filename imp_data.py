# script initializes data from a csv file containing all data upto now. the data is aggregated as daily values and saved in the parquet format
# for fast retrievel into pandas. in the app, this local data is read first, if it contains the data from yesterday, it is used as is, otherwise, 
# new data is fetched from data.bs and added to the pq, which then is uptodate for the next user.
import streamlit as st
from io import StringIO
import pandas as pd
import numpy as np
import sqlalchemy as sql
import requests 
from datetime import datetime
import timeit
import database as db


def read_velocities_from_from_url():
    url_template = "https://data.bs.ch/explore/dataset/100097/download/?format=csv&refine.timestamp={}%2F{}&timezone=Europe/Zurich&lang=de&use_labels_for_header=true&csv_separator=%3B"
    #when inititializing, create with first fetch
    # if_exists = 'replace'
    if_exists = 'append'
    table = 'velocity' 
    lst_fields = ['Timestamp', 'Messung-ID', "Richtung ID", 'Geschwindigkeit']
    ok = True
    for year in range(2017,2022):
        for month in range(1,13):
            if ok:
                m = "{:02d}".format(month)
                url = url_template.format(year,m)
                req = requests.get(url)
                data = StringIO(req.text)
                df = pd.read_csv(data, sep=";")
                if len(df)>0:
                    df = df[lst_fields]
                    df.columns = ['timestamp', 'station_id', "direction_id", 'velocity_kmph']
                    ok = db.save_db_table(table,df,[],if_exists)
                    print(len(df), year, month, datetime.today())
                    if_exists = 'append'
    return ok

            
def read_velocities_from_file():
    ok = True
    df = pd.read_csv("./import/100097.csv", sep=';')
    df = df.query('Geschwindigkeit > Zone')
    print(df.columns)
    lst_fields = ['Messung-ID', 'Richtung ID', 'Datum und Zeit', 'Geschwindigkeit']
    df = df[lst_fields]
    df.columns = ['messung_id','richtung_id', 'timestamp', 'geschwindigkeit']
    df['timestamp'] = df['timestamp'].str[:11]
    df['hour'] = df['timestamp'].str[9:11].astype(int)
    #pd.to_datetime(df['timestamp'], format=)
    print(df.head())
    df.to_parquet('violations.parquet')
    ok = db.save_db_table('violation',df, [])
    return ok


def read_stations_from_url():
    ok=True
    url = "https://data.bs.ch/explore/dataset/100112/download/?format=csv&timezone=Europe/Zurich&lang=de&use_labels_for_header=true&csv_separator=%3B"
    req = requests.get(url)
    # df = pd.read_csv("./import/100112.csv", sep=';')
    data = StringIO(req.text)
    df = pd.read_csv(data, sep=";")
    
    #split Geopunkt field into lat/long
    df['latitude'] = df.apply(lambda x: x['Geopunkt'].split(",")[0], axis=1)
    df['longitude'] = df.apply(lambda x: x['Geopunkt'].split(",")[1], axis=1)
    # split columns in 2 parts: direction 1 and 2 and paste them one bleow the other, this will make it easier to join with the 
    # the velocity table
    r1_fields = ['Messung-ID', 'Messbeginn', 'Messende', 'Strasse', 'Hausnummer', 'Ort',
       'Zone', 'Richtung 1', 'Fahrzeuge Richtung 1', 'V50 Richtung 1',
       'V85 Richtung 1', 'Übertretungsquote Richtung 1','latitude', 'longitude']
    r2_fields = ['Messung-ID', 'Messbeginn', 'Messende', 'Strasse', 'Hausnummer', 'Ort',
       'Zone', 'Richtung 2', 'Fahrzeuge Richtung 2', 'V50 Richtung 2', 
       'V85 Richtung 2','Übertretungsquote Richtung 2','latitude', 'longitude']
    db_fields =  ['messung_id', 'messbeginn', 'messende', 'strasse', 'hausnummer', 'ort',
       'zone', 'richtung_strasse', 'fahrzeuge', 'V50', 'V85', 'uebertretungsquote',
       'latitude', 'longitude', 'richtung']
    
    df_r1 = df[r1_fields] 
    df_r1['richtung'] = 1
    df_r1.columns = db_fields
    df_r1.set_index(['messung_id', 'richtung'])
    
    df_r2 = df[r2_fields]
    df_r2['richtung'] = 2
    df_r2.columns = db_fields
    df_r2.set_index(['messung_id', 'richtung'])

    df = pd.concat([df_r1, df_r2], keys = ['messung_id', 'richtung']).reset_index()
    #df.to_parquet('stations.parquet')
    sqlite_conn, ok = db.get_sqlite_connection('velocity_all.sqlite3')
    ok = db.save_db_table('station',df, db_fields,'replace', sqlite_conn)
    st.info(f"{len(df)} stations have been read")
    return ok


def transfer_to_pg():
    def import_stations():
        sql = "select * from station"
        df,ok, err_msg = db.execute_query(sql, sqlite_conn)
        st.write(df.head())
        ok, err_msg = db.save_db_table('station',df, [],'replace', pg_conn)
        if ok:
            st.success(f"{len(df)} station records have been imported")
        else:
            st.warning(f"error: {err_msg}")
    
    def import_velocities():
        sql = "select * from velocity"
        df,ok, err_msg = db.execute_query(sql, sqlite_conn)
        st.write(df.head())
        ok, err_msg = db.save_db_table('velocity',df, [],'replace', pg_conn)
        if ok:
            st.success(f"{len(df)} velocity records have been imported")
        else:
            st.warning(f"error: {err_msg}")

    sqlite_conn, ok = db.get_sqlite_connection('velocity_all.sqlite3')
    pg_conn, ok = db.get_pg_engine()
    # import_stations()
    import_velocities()
    

def get_data(station, conn):
    sql = f"select station_id,velocity_kmph from velocity where station_id = {station}"
    df, ok, err_msg = db.execute_query(sql, conn)
    df['station_id'] = df['station_id'].astype(int)
    df['velocity_kmph'] = df['velocity_kmph'].astype(np.float64)
    return df


def get_stations(conn):
    sql = "select id from station"
    df, ok, err_msg = db.execute_query(sql, conn)
    return list(df['id'])


def calc_precentiles(df, conn):
    def percentile(n):
        def percentile_(x):
            return np.percentile(x, n)
        percentile_.__name__ = 'percentile_%s' % n
        return percentile_
    
    df_stats = df.groupby(['station_id'])[['velocity_kmph']].agg(['max','mean', 'std', 'count', 
        percentile(5), percentile(10), percentile(25), percentile(50), percentile(75), 
        percentile(85), percentile(90), percentile(95)]).reset_index()
    columns = ['station_id', 'v_max','v_mean', 'v_std', 'v_count', 'v_percentile05', 'v_percentile10', 'v_percentile25', 'v_percentile50', 'v_percentile75', 
        'v_percentile85', 'v_percentile90', 'v_percentile95']
    df_stats.columns = columns
    return df_stats


def save_result(df,station, conn):
    ok = True
    rec = df.iloc[0].to_dict()
    sql = f"""Update station set 
    vehicle_count = {rec['v_count']},
    velocity_mean = {rec['v_mean']},
    velocity_std = {rec['v_std']},
    velocity_p05 = {rec['v_percentile05']},
    velocity_p10 = {rec['v_percentile10']},
    velocity_p25 = {rec['v_percentile25']},
    velocity_p50 = {rec['v_percentile50']},
    velocity_p75 = {rec['v_percentile75']},
    velocity_p85 = {rec['v_percentile85']},
    velocity_p90 = {rec['v_percentile90']},
    velocity_p95 = {rec['v_percentile95']}
    where id = {station}"""
    st.write(sql)
    ok = db.execute_non_query(sql, conn)
    return ok

def calculate_station_stats():
    conn = db.get_pg_connection()
    stations = get_stations(conn)
    text_placeholder = st.empty()
    i=1
    #to set stations explicitely
    #stations = [2,33,89]
    for station in stations:
        st.write( f"Start calculating Station {station} ({i}/{len(stations)})")
        df_data = get_data(station, conn)
        if len(df_data) > 0:
            df_result = calc_precentiles(df_data, conn)
            ok = save_result(df_result,station,conn)
            st.write( f"End calculating Station {station}")
        else:
            st.write( f"Station {station} has no records")
        i+=1        


options = ["Read velocities from url", "Read Stations from url", "Transfer data from sqlite to pg", "calculate Station Stats"]
option = st.sidebar.selectbox("Select Option",options)
if st.sidebar.button("Run"):
    if option == options[0]:
        read_velocities_from_from_url()
    elif option == options[1]:
        read_stations_from_url()
    elif option == options[2]:
        transfer_to_pg()
    elif option == options[3]:
        calculate_station_stats()

