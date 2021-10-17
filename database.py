import pandas as pd
import sqlalchemy as sql
import sqlite3
import db_config as dbcn
from sqlalchemy import create_engine   
import streamlit as st
import psycopg2
conn = ''


def get_pg_connection():
    """Reads the connection string and sets the sql_engine attribute."""

    conn = psycopg2.connect(
        host = dbcn.DB_HOST,
        database=dbcn.DB_DATABASE,
        user=dbcn.DB_USER,
        password=dbcn.DB_PASS)

    return conn

# with sqlalchemy
def get_pg_engine():
    """Reads the connection string and sets the sql_engine attribute."""
    ok=True
    sql_engine = {}
    try:
        connect_string = f'postgresql+psycopg2://{dbcn.DB_USER}:{dbcn.DB_PASS}@{dbcn.DB_HOST}:{dbcn.DB_PORT}/{dbcn.DB_DATABASE}'
        sql_engine = create_engine(connect_string, pool_recycle=3600)
    except Exception as ex:
        print(ex)
        ok=False
    return sql_engine, ok

def get_sqlite_connection(db_file):
    """
    Connect to an SQlite database, if db file does not exist it will be created
    :param db_file: absolute or relative path of db file
    :return: sqlite3 connection
    """
    ok = True
    sqlite3_conn = None
    
    try:
        #sqlite3_conn = sqlite3.connect(db_file)
        engine = create_engine(f"sqlite:///{db_file}")
        return engine, ok
    except Exception as ex:
        return None, ok 

def execute_non_query(cmd: str, cn)-> bool:
    """
    Executes a stored procedure, without a return value. it can only be applied to 
    the local database
    """

    ok = False
    _cursor = cn.cursor()
    try:
        _cursor.execute(cmd)
        cn.commit()
        ok = True
    except Exception as ex:
        print(ex)
    return ok
    
    
def execute_query(query: str, cn) -> pd.DataFrame:
    """
    Executes a query and returns a dataframe with the results
    """

    ok= False
    err_msg = ''
    result = None
    try:
        result = pd.read_sql_query(query, cn)
        ok = True
    except Exception as ex:
        print(ex)
        err_msg = ex

    return result, ok, err_msg


def get_single_value(qry, conn, col) -> str:
    df = execute_query(qry, conn)
    return(df[col][0])

def get_distinct_values(column_name, table_name, dataset_id, criteria):
    """
    Returns a list of unique values from a defined code column.
    """
    criteria = (' AND ' if criteria > '' else '') + criteria
    query = f"SELECT {column_name} FROM {table_name} where dataset_id = {dataset_id} {criteria} group by {column_name} order by {column_name}"
    result = execute_query(query, conn)
    result = result[column_name].tolist()
    return result

def save_db_table(table_name: str, df: pd.DataFrame, fields: list, if_exists: str, engine):
    ok = False
    err_msg = ''
    try:
        if len(fields) > 0:
            df = df[fields]
        df.to_sql(table_name, engine, if_exists=if_exists, chunksize=20000, index=False)
        ok = True
    except ValueError as vx:
        err_msg = vx
    except Exception as ex:
        err_msg = ex
    finally:
        return ok, err_msg