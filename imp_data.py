# script initializes data from a csv file containing all data upto now. the data is aggregated as daily values and saved in the parquet format
# for fast retrievel into pandas. in the app, this local data is read first, if it contains the data from yesterday, it is used as is, otherwise, 
# new data is fetched from data.bs and added to the pq, which then is uptodate for the next user.

import pandas as pd
import sqlalchemy as sql
import requests 


def save_db_table(table_name: str, df: pd.DataFrame, fields: list):
    ok = False
    connect_string = 'sqlite:///velocity.sqlite3'
    try:
        sql_engine = sql.create_engine(connect_string, pool_recycle=3600)
        db_connection = sql_engine.connect()
    except Exception as ex:
        print(ex)

    print(db_connection)
    try:
        if len(fields) > 0:
            df = df[fields]
        df.to_sql(table_name, db_connection, if_exists='replace', chunksize=20000, index=False)
        ok = True
    except ValueError as vx:
        print(vx)
    except Exception as ex:
        print(ex)
    finally:
        db_connection.close()
        return ok

def read_velocities():
    df = pd.read_csv("./import/100097.csv", sep=';')
    df = df.query('Geschwindigkeit > Zone')
    print(df.columns)
    lst_fields = ['Messung-ID', 'Richtung ID', 'Datum und Zeit', 'Geschwindigkeit']
    df = df[lst_fields]
    df.columns = ['Messung-ID','Richtung-ID', 'Timestamp', 'Geschwindigkeit']
    print(df.head())
    df.to_parquet('violation.parquet')
    #df.to_csv('violation.csv',sep = ";")
    ok = save_db_table('violation',df, [])
    return ok

def read_stations():
    ok=True
    df = pd.read_csv("./import/100112.csv", sep=';')
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
    
    df_r1 = df[r1_fields].copy() 
    df_r1['richtung'] = 1
    df_r1.columns = db_fields
    df_r1.set_index(['messung_id', 'richtung'])
    
    df_r2 = df[r2_fields].copy() 
    df_r2['richtung'] = 2
    df_r2.columns = db_fields
    df_r2.set_index(['messung_id', 'richtung'])

    df = pd.concat([df_r1, df_r2], keys = ['messung_id', 'richtung']).reset_index()

    ok = save_db_table('station',df,[])
    return ok

# print(read_velocities())
print (read_stations())
