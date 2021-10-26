import streamlit as st
import pandas as pd
import numpy as np
import database as db
from queries import qry
from datetime import datetime
import altair as alt
import const as cn
import helper

f_int = '.0f'
f_dec = '.1f'
f_pct = '.1%'
f_dat = '%d.%m.%Y'


def create_heatmap(df,settings):
    chart = alt.Chart(df).mark_rect().encode(
        x=settings['x'],
        y=settings['y'],
        color=settings['color'],
        tooltip=settings['tooltip'],
    ).properties(
        width=settings['width'],
        height=settings['height'],
    )
    return chart

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
    statfields =['site_id','location','start_date','end_date','zone','direction_street','vehicles','exceedance_rate','v50','v85']
    df, ok, err_msg = db.execute_query(qry['all_stations'], _conn)
    df = helper.format_time_columns(df,('start_date','end_date'),cn.FORMAT_DMY)
    df['location'] = df['location'].astype(str)
    df['direction_street'] = df['direction_street'].astype(str)
    df['vehicles'] = df['vehicles'].astype(int)
    df['v50'] = df['v50'].astype(int)
    df['v85'] = df['v85'].astype(int)
    df = df[statfields]
    return df


@st.experimental_memo()     
def get_stations(_conn):
    statfields =['station_id','site_id','location','start_date','end_date','zone','direction_street','direction','vehicles','exceedance_rate','v50','v85']
    df, ok, err_msg = db.execute_query(qry['all_stations'], _conn)
    df['location'] = df['location'].astype(str)
    df['direction_street'] = df['direction_street'].astype(str)
    df['vehicles'] = df['vehicles'].astype(int)
    df['v50'] = df['v50'].astype(int)
    df['v85'] = df['v85'].astype(int)
    df = df[statfields]
    return df

def get_lst_ort(stations):
    return stations['ort'].unique()

@st.experimental_memo() 
def get_dic_stations(stations): 
    stations['value'] = stations["location"].str.cat([stations['location'], stations['direction_street']], sep=", ")
    stations = stations.sort_values('value')
    return dict(zip(stations['station_id'], stations['value']))

@st.experimental_memo() 
def get_dic_locations(locations): 
    locations['value'] = locations["location"].str.cat(locations['location'], sep=", ")
    return dict(zip(locations['station_id'], locations['value']))

def append_row(df, par, value, fmt):
    if isinstance(value, datetime):
        df = df.append({'Parameter':par, 'Wert':value.strftime(fmt)}, ignore_index=True)
    else:
        df = df.append({'Parameter':par, 'Wert':format(value,fmt)}, ignore_index=True)
    return df    

def summary_all(conn, texts):
    def get_text(df, vals):
        """explains the summary table

        Args:
            df ([type]): datafr
            vals ([type]): [description]

        Returns:
            [type]: [description]
        """
        a = f"{vals['exeedance_quote_max']*100 :.1f}"
        return texts['instructions_summary'].format(
            a,
            vals['exeedance_quote_max_location'],
            vals['start_date'].strftime(cn.FORMAT_DMY), 
            vals['end_date'].strftime(cn.FORMAT_DMY))

    vals={}
    df_table = pd.DataFrame(columns=['Parameter', 'Wert'])
    vals['exceedance_count'] = get_violation_count(conn)
    stations = get_stations(conn)
    x = len(stations['site_id'].unique())
    vals['station_count'] = len(pd.unique(stations[['site_id', 'direction']].values.ravel()))
    vals['dir_count'] = len(stations)
    vals['start_date'] = stations['start_date'].min()
    vals['end_date'] = stations['end_date'].max()
    vals['vehicles']=int(stations['vehicles'].sum())
    vals['exceedance_quote_stations']=stations['exceedance_rate'].mean()/100
    vals['exeedance_quote_max']=stations['exceedance_rate'].max()/100
    vals['exeedance_quote_max_location']=stations.query(f"exceedance_rate=={stations['exceedance_rate'].max()}")
    vals['exeedance_quote_max_location'] = vals['exeedance_quote_max_location'].iloc[0]['location'] + ',' + vals['exeedance_quote_max_location'].iloc[0]['location']
    vals['exceedance_quote_all']= vals['exceedance_count'] / vals['vehicles'] if vals['exceedance_count'] > 0 else 0

    groupby_fields = ['site_id', 'location','start_date','end_date']
    df_table = append_row(df_table, 'Anzahl Messstationen', vals['station_count'], f_int)
    df_table = append_row(df_table,'Anzahl Richtungen',vals['dir_count'], f_int)
    df_table = append_row(df_table,'Erste Messung',vals['start_date'], f_dat)
    df_table = append_row(df_table,'Letzte Messung',stations['end_date'].max(), f_dat)

    df_time = stations.groupby(groupby_fields)['vehicles'].agg(['sum']).reset_index()
    df_time['num_of_days'] = (df_time['end_date'] - df_time['start_date']).astype('timedelta64[h]') / 24
    vals['num_of_days']=df_time['num_of_days'].sum()
    df_table = append_row(df_table,'Anzahl Tage total',vals['num_of_days'],f_int)
    vals['avg_num_days']=df_time['num_of_days'].mean()
    df_table = append_row(df_table,'Mittlere Anzahl Tage pro Messstation',vals['avg_num_days'],f_dec)
    
    df_table = append_row(df_table,'Anzahl Vehicles',vals['vehicles'],",d")
    df_table = append_row(df_table,'Anzahl Übertretungen',vals['exceedance_count'],",d")
    df_table = append_row(df_table,'Max. Übertretungsquote', vals['exeedance_quote_max'],f_pct)
    df_table = append_row(df_table,'Mittlere Übertretungsquote (Stationen)', vals['exceedance_quote_stations'],f_pct)
    df_table = append_row(df_table,'Übertretungsquote (alle Messungen)', vals['exceedance_quote_all'],f_pct)
    text = get_text(df_table, vals)
    return df_table, text

 
def station_stats(conn, texts):
    def get_filter():
        dic_stations = get_dic_stations(stations)
        station_sel = st.sidebar.multiselect("Wähle eine oder mehrere Messstationen", dic_stations.keys(), format_func=lambda x: dic_stations[x])   
        return station_sel
    
    def get_text(df_filtered, df_unfiltered):
        if len(df_filtered) == len(df_unfiltered):
            filter_expr = f" alle {len(df_unfiltered)} Messstationen (Richtungen)"
        else:
            filter_expr = f" {len(df_filtered)} selektierte Messstationen (Richtungen)"
        max_exc_quote = df_filtered['exceedance_rate'].max()
        max_exc_quote_location = df_filtered.query("exceedance_rate == @max_exc_quote")
        max_exc_quote_location = f"{max_exc_quote_location.iloc[0]['location']}, {max_exc_quote_location.iloc[0]['location']}"
        max_num = df_filtered['vehicles'].max()
        max_num_location = df_filtered.query("vehicles == @max_num")
        max_num_location = f"{max_num_location.iloc[0]['location']}, {max_num_location.iloc[0]['location']}"
        max_num = f"{max_num:,d}"
        text = texts['station_analysis'].format(
            filter_expr,
            max_exc_quote_location,
            max_exc_quote,
            max_num_location,
            max_num,
        )
        return text
    stations = get_stations(conn)
    station_sel = get_filter()
    df_filtered = stations.query("station_id in @station_sel") if len(station_sel) > 0 else stations
    df_filtered = df_filtered.drop(['station_id'], axis=1)
    return df_filtered, get_text(df_filtered, stations)


def weekday_stats(conn, texts):
    def get_heatmap(df):
        settings={}
        settings['x'] = alt.X('dow:N', axis=alt.Axis(title=''), sort=cn.WOCHE)
        settings['y'] = alt.Y('location:N', axis=alt.Axis(title=''))
        settings['color'] = alt.X('count:Q')
        settings['tooltip'] = alt.Tooltip(['count:Q'], title='Anzahl Überschreitungen')
        settings['width'] = 800
        settings['height'] = 100 + len(df['location'].unique()) * 20
        return create_heatmap(df, settings)

    def get_filter():
        dic_stations = get_dic_stations(stations)
        station_sel = st.sidebar.multiselect("Wähle eine oder mehrere Messstationen", dic_stations.keys(), format_func=lambda x: dic_stations[x])   
        return station_sel
    
    @st.experimental_memo()     
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

    def get_text(df, stations, station_sel):
        if len(station_sel)>0:
            station_sel =  [str (x) for x in station_sel]
            where_clause = " where station_id in (" + ",".join(station_sel) + ')'
            station_num = len(station_sel)
        else:
            where_clause = ''
            station_num = len(stations)
        sql = qry['exceedance_count_ranked_by_weekday'].format(where_clause)
        df_rank, ok, err_msg = db.execute_query(sql, conn)
        df_rank['dow'] = df_rank['dow'].astype(int)
        df_rank = df_rank.sort_values('first')
        most_frequent = (cn.WEEKDAY4ID[df_rank.iloc[6]['dow']],cn.WEEKDAY4ID[df_rank.iloc[5]['dow']])
        df_rank = df_rank.sort_values('last')
        least_frequent = (cn.WEEKDAY4ID[df_rank.iloc[6]['dow']],cn.WEEKDAY4ID[df_rank.iloc[5]['dow']])
        text = f"""Bei den selektierten {station_num} Messstationen wurden Geschwindigkeitsübertretungen am häufigsten am {most_frequent[0]} und {most_frequent[1]} verzeichnet. 
Am wenigsten Übertretungen wurden an den Wochentagen {least_frequent[0]} und {least_frequent[1]} begangen."""
        return text

    stations = get_stations(conn)
    station_sel = get_filter()
    cb_heatmap = st.sidebar.checkbox('Zeige Tabelle als Heatmap')
    df_data = get_exceedance_data()
    df_filtered = df_data.query("station_id in @station_sel") if len(station_sel) > 0 else df_data
    df_filtered = helper.replace_day_ids(df_filtered, 'dow')

    df_unmelted =  df_filtered[['station_id','dow','count']].pivot(index=['station_id'], columns='dow').reset_index()
    df_unmelted = rename_columns(df_unmelted)
    df_unmelted = df_unmelted.replace({'station_id': get_dic_stations(stations)})
    df_unmelted = df_unmelted.rename(columns={'station_id': 'Messstation'})
    chart = get_heatmap(df_filtered) if cb_heatmap else None
    text = get_text(df_unmelted, stations, station_sel)
    return df_unmelted, chart, text


def hourly_stats(conn, texts):
    def get_heatmap(df):
        settings={}
        settings['x'] = alt.X('hour:N', axis=alt.Axis(title=''), sort=cn.WOCHE)
        settings['y'] = alt.Y('location:N', axis=alt.Axis(title=''))
        settings['color'] = alt.X('sum(count):Q')
        settings['tooltip'] = alt.Tooltip(['count:Q'], title='Anzahl Überschreitungen')
        settings['width'] = 800
        settings['height'] = 100 + len(df['location'].unique()) * 20
        return create_heatmap(df, settings)

    def get_filter():
        dic_stations = get_dic_stations(stations)
        station_sel = st.sidebar.multiselect("Wähle eine oder mehrere Messstationen", dic_stations.keys(), format_func=lambda x: dic_stations[x])   
        return station_sel
    
    @st.experimental_memo()     
    def get_exceedance_data():
        df, ok, err_msg = db.execute_query(qry['station_exceedances_hour'], conn)
        return df

    def dissolve_multi_index(df):
        df.columns = ['station_id','00h','01h','02h','03h','04h','05h','06h','07h','08h','09h','10h','11h',
                                   '12h','13h','14h','15h','16h','17h','18h','19h','20h','21h','22h','23h']
        return df

    def get_text(df, stations, station_sel):
        def get_last_items(df):
             last_two = (str(int(df_rank.iloc[len(df) - 1]['hour'])),str(int(df_rank.iloc[len(df) - 2]['hour'])))
             return last_two

        if len(station_sel)>0:
            station_sel =  [str (x) for x in station_sel]
            where_clause = " where station_id in (" + ",".join(station_sel) + ')'
            station_num = len(station_sel)
        else:
            where_clause = ''
            station_num = len(stations)
        sql = qry['exceedance_count_ranked_by_hour'].format(where_clause)
        df_rank, ok, err_msg = db.execute_query(sql, conn)
        df_rank = df_rank.sort_values('first')
        most_frequent = get_last_items(df_rank)
        df_rank = df_rank.sort_values('last')
        least_frequent =  get_last_items(df_rank)
        text = f"""Bei den selektierten {station_num} Messstationen wurden Geschwindigkeitsübertretungen am häufigsten um {most_frequent[0]} und {most_frequent[1]} Uhr verzeichnet. 
Am wenigsten Übertretungen wurden um {least_frequent[0]} und {least_frequent[1]} Uhr begangen."""
        return text


    stations = get_stations(conn)
    station_sel = get_filter()
    cb_heatmap = st.sidebar.checkbox('Zeige Tabelle als Heatmap')
    df_data = get_exceedance_data()
    df_filtered = df_data.query("station_id in @station_sel") if len(station_sel) > 0 else df_data
    df_unmelted = helper.add_leading_zeros(df_filtered, 'hour',2)
    df_unmelted =  df_filtered[['station_id','hour','count']].pivot(index=['station_id'], columns='hour').reset_index()
    df_unmelted = dissolve_multi_index(df_unmelted)
    df_unmelted = df_unmelted.replace({'station_id': get_dic_stations(stations)})
    df_unmelted = df_unmelted.rename(columns={'station_id': 'Messstation'})
    heatmap = get_heatmap(df_filtered) if cb_heatmap else None
    text = get_text(df_unmelted, stations, station_sel)
    return df_unmelted, heatmap, text
    

def show_menu(texts, conn):    

    menu = texts['menu_options']

    menu_item = st.sidebar.selectbox('Optionen', menu)
    st.markdown(f"### {menu_item}")
    text = "Hier fehlt noch eine Beschreibung dieser Tabelle"  # todo: implement
    heatmap = None
    if menu_item == menu[0]:
        df, text = summary_all(conn, texts)
        helper.show_table(df,[])
    elif menu_item ==  menu[1]:
        df, text = station_stats(conn, texts)
        df.columns = [cn.PARAMETERS_DIC[x]['label'] for x in df.columns]
        helper.show_table(df,[])
    elif menu_item ==  menu[2]:
        df, heatmap, text = weekday_stats(conn, texts)
        helper.show_table(df,[])
    elif menu_item ==  menu[3]:
        df, heatmap, text = hourly_stats(conn, texts)
        helper.show_table(df,[])

    st.markdown(text,unsafe_allow_html=True)
    if heatmap:
        st.altair_chart(heatmap)
    
                