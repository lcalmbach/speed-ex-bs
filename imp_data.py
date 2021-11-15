# streamlit app to import new data. db update works as follows:
# 1. streamlit run imp_data.py
# 2. press Run button: new stations are discovered and imported together with measurements
# 3. backup local database
# 4. restore remote database with the the option clean first: there are fail warnings but 
#    all objects are up-to-date

import streamlit as st
from io import StringIO
import pandas as pd
import numpy as np
import sqlalchemy as sql
import requests 
from datetime import datetime
# import timeit

import database as db
import const as cn

conn = db.get_pg_connection()

def get_all_stations():
    # url to retrieve radar stations (100112) from data.bs    
    url = "https://data.bs.ch/explore/dataset/100112/download/?format=csv&timezone=Europe/Zurich&lang=de&use_labels_for_header=true&csv_separator=%3B"
    req = requests.get(url)
    # df = pd.read_csv("./import/100112.csv", sep=';')
    data = StringIO(req.text)
    df = pd.read_csv(data, sep=";")
    return df


def remove_existing_stations(df:pd.DataFrame):
        """
        Gets a dataframe with all stations, then finds the stations in the velox-database and removes
        those from the dataframe.

        Args:
            df ([pd.Dataframe]): dataframe holding all stations

        Returns:
            pd.Dataframe: dataframe holding only stations from data.bs not present in the local database
        """
        sql = "select site_id from station"
        df_existing,ok,err_msg = db.execute_query(sql,conn)
        df_new = None
        if ok:
            lst_existing = list(df_existing['site_id'])
            df_new = df[df['Messung-ID'].isin(lst_existing)==False]
        return df_new


def read_stations_from_url(new_stations_only:bool):
    """imports all new stations from a data.bs-url

    Args:
        new_stations_only (bool): True if only new stations are to be found, false if 
                                  all stations are imported
    """
    
    
    def split_directions(df:pd.DataFrame()):
        """
        Each messung-id represents the 2 directions for a given location. in database these are kept in 1 record
        in speed-ex-bs, these are considered 1 stations belonging to 1 site. this function splits the record into the 
        2 station record with each having its v50, v85.

        Args:
            df (pd.DataFrame): station dataframe having 1 record for the 2 directions

        Returns:
            pd.DataFrame: dataframe with 2 reocrds per site, new id is station_id, original Messung-ID field is kept
                          as site_id
            list:         list of fields in the database station table
        """
        
        def split_geopoint(df):
            df['latitude'] = df.apply(lambda x: x['Geopunkt'].split(",")[0], axis=1)
            df['longitude'] = df.apply(lambda x: x['Geopunkt'].split(",")[1], axis=1)
            return df

        df = split_geopoint(df)
        
        # split columns in 2 parts: direction 1 and 2 and paste them one bleow the other, this will make it easier to join with the 
        # the velocity table
        r1_fields = ['Messung-ID', 'Messbeginn', 'Messende', 'Strasse', 'Hausnummer', 'Ort',
        'Zone', 'Richtung 1', 'Fahrzeuge Richtung 1', 'V50 Richtung 1',
        'V85 Richtung 1', 'Übertretungsquote Richtung 1','latitude', 'longitude']
        r2_fields = ['Messung-ID', 'Messbeginn', 'Messende', 'Strasse', 'Hausnummer', 'Ort',
        'Zone', 'Richtung 2', 'Fahrzeuge Richtung 2', 'V50 Richtung 2', 
        'V85 Richtung 2','Übertretungsquote Richtung 2','latitude', 'longitude']
        
        db_fields =  ['site_id', 'start_date', 'end_date', 'street', 'house_number', 'location',
        'zone', 'direction_street', 'vehicles', 'v50', 
        'v85', 'exceedance_rate', 'latitude', 'longitude', 'direction']
        
        df_r1 = df[r1_fields] 
        df_r1['richtung'] = 1
        df_r1.columns = db_fields
        df_r1.set_index(['site_id', 'direction'])
        
        df_r2 = df[r2_fields]
        df_r2['richtung'] = 2
        df_r2.columns = db_fields
        df_r2.set_index(['site_id', 'direction'])
        df = pd.concat([df_r1, df_r2], keys = ['site_id', 'direction']).reset_index()
        return df, db_fields

    def append_rows(db_fields: list):
        """appends the content of the imp_velocity table to the velocity table

        Args:
            db_fields (list):   list of database fields without the id column, used to generate the 
                                sql insert statement.
        """
        to_fields = ",".join(db_fields)
        # convert date fields to the required types
        from_fields = to_fields.replace('start_date',"to_date(start_date,'YYYY-MM-DD')")
        from_fields = from_fields.replace('end_date',"to_date(end_date,'YYYY-MM-DD')")
        from_fields = from_fields.replace('latitude',"cast(latitude as double precision)")
        from_fields = from_fields.replace('longitude',"cast(longitude as double precision)")
        sql = f"insert into station({to_fields}) select {from_fields} from imp_station"
        ok = db.execute_non_query(sql, conn)
        if ok:
            st.info(f"{len(df)} stations have been saved to the station table")
        else:
            st.write(sql)
            st.warning("Ups, new stations could not be saved to the station table")

    def update_fields():
        sql = "update station set address = street || ' ' || coalesce(house_number,'')"
        ok = db.execute_non_query(sql, conn)
        return ok
    
    
    df = get_all_stations()
    st.info(f"{len(df)} stations read from url")
    if new_stations_only:
        df=remove_existing_stations(df)
    db_fields=[]
    if len(df) > 0:
        df, db_fields = split_directions(df)
        pg_conn, ok = db.get_pg_engine()
        ok = db.save_db_table('imp_station', df, db_fields, 'replace', pg_conn)
        if ok:
            st.info(f"{len(df)} stations have been saved to staging table")
        else:
            st.warning("Ups, new stations could not be saved to staging table")
        
        if ok:
            append_rows(db_fields)
            ok = update_fields()
        return list(df['site_id'])
    else:
        return []

def import_data_for_site(site_id: int):
    """
    import data by url: the dataset is huge, so I extract all data from the from/to month-year then only select 
    the data from for the specified site_id
    """

    def transfer_to_dwh():
        sql = """insert into velocity(date_time, station_id,site_id,direction_id,velocity_kmph,exceedance_kmph)
            select cast(t1.timestamp as timestamp without time zone), t2.id, t1.site_id,t1.direction, t1.velocity_kmph, t1.velocity_kmph - t2.zone
            from public.imp_velocity t1
            inner join public.station t2 on t2.site_id = t1.site_id and t2.direction = t1.direction
            where t1.velocity_kmph > t2.zone"""
        ok = db.execute_non_query(sql,conn)
        if ok:
            st.success(f"Data form site {site_id} was saved to table velocity")
        else:
            st.warning(f"Data form site {site_id} could not be saved to table velocity")
        
    def update_calculated_fields():
        sql = """insert into velocity(date_time, station_id,site_id,direction_id,velocity_kmph,exceedance_kmph)
            select cast(t1.timestamp as timestamp without time zone), t2.id, t1.site_id,t1.direction, t1.velocity_kmph, t1.velocity_kmph - t2.zone
            from public.imp_velocity t1
            inner join public.station t2 on t2.site_id = t1.site_id and t2.direction = t1.direction
            where t1.velocity_kmph > t2.zone"""
        ok = db.execute_non_query(sql,conn)
        if ok:
            st.success(f"Data form site {site_id} was saved to table velocity")
        else:
            st.warning(f"Data form site {site_id} could not be saved to table velocity")
    
    
    url = f"https://data.bs.ch/explore/dataset/100097/download/?format=csv&disjunctive.geschwindigkeit=true&disjunctive.zone=true&disjunctive.ort=true&disjunctive.v50=true&disjunctive.v85=true&disjunctive.strasse=true&disjunctive.fzg=true&refine.messung_id={site_id}&timezone=Europe/Zurich&lang=de&use_labels_for_header=true&csv_separator=%3B"
    table = 'imp_velocity' 
    lst_fields = ['Timestamp', 'Messung-ID', "Richtung ID", 'Geschwindigkeit']
    ok = True
    req = requests.get(url)
    data = StringIO(req.text)
    df = pd.read_csv(data, sep=";")
    st.write(df.head())
    if len(df)>0:
        df = df[lst_fields]
        df.columns = ['timestamp', 'site_id', "direction", 'velocity_kmph']
        pg_conn, ok = db.get_pg_engine()
        ok = db.save_db_table(table,df,[],'replace', pg_conn)
        transfer_to_dwh()
    return len(df), ok


def get_data_for_sites(lst):

    def get_directions(site_id):
        # finds the directions (stations) for a given site

        sql = f"select id from station where site_id = {site_id}"
        df, ok, err_msg = db.execute_query(sql,conn)
        if ok: 
            return list(df['id'])
        else:
            return None

    for site_id in lst:
        st.info(f"Importing site-id {site_id}")
        records, ok = import_data_for_site(site_id)
        lst_stations = get_directions(site_id)
        calculate_station_stats(lst_stations)
        st.success(f"{records} records were imported for site {site_id}")

    
def get_data(station, conn):
    sql = f"select station_id,velocity_kmph from velocity where station_id = {station}"
    df, ok, err_msg = db.execute_query(sql, conn)
    df['station_id'] = df['station_id'].astype(int)
    df['velocity_kmph'] = df['velocity_kmph'].astype(np.float64)
    return df


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
    # st.write(sql)
    ok = db.execute_non_query(sql, conn)
    return ok

def calculate_station_stats(stations):
    i=1
    for station in stations:
        st.write( f"Start calculating Station {station} ({i}/{len(stations)})")
        df_data = get_data(station, conn)
        if len(df_data) > 0:
            df_result = calc_precentiles(df_data, conn)
            ok = save_result(df_result,station,conn)
            st.success( f"End calculating Station {station}")
        else:
            st.warning( f"Station {station} has no records")
        i+=1        

def get_stations(lst:list):
    sql = "select * from station"
    df, ok, err_msg = db.execute_query(sql,conn)
    df = df[df['site_id'].isin(lst)]
    return df

def cleanup():
    sql = """
        truncate table public.imp_station;
        truncate table public.imp_velocity;"""
    ok = db.execute_non_query(sql,conn)

options = ["Find new stations", "Find and import new stations with data"]
sel_option = st.sidebar.selectbox("Select Option",options)

if sel_option == options[0]:
    df = get_all_stations()
    df = remove_existing_stations(df)
    st.info(f"{len(df)} new stations have been found")
    if len(df) > 0:
        st.write(df)
elif sel_option == options[1]:
    if st.sidebar.button("Run"):
        lst = read_stations_from_url(new_stations_only=True)
        #lst = [450]
        ok = get_data_for_sites(lst)
        cleanup()
st.sidebar.markdown(f"host: {cn.DB_HOST}\n\ndb: {cn.DB_DATABASE}")

    
    