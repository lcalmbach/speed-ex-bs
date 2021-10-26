# from sqlite3.dbapi2 import Timestamp
# from numpy.random.mtrand import random_integers
import streamlit as st
import altair as alt
import pandas as pd
import pydeck as pdk
import numpy as np
# import random
from datetime import datetime, time
from queries import qry

import const as cn
import database as db
import helper

lst_group_fields = ['exceedance_rate', 'diff_v50_perc', 'diff_v85_perc', 'vehicles']


def plot_map(df: pd.DataFrame, settings: object):
    """
    Generates a map plot

    :param value_col: column holding parameter to be plotted
    :param layer_type: HexagonLayer or ScatterplotLayer
    :param title: title of plot
    :param df: dataframe with data to be plotted
    :return:
    """
    if df.shape[0] > 0:
        if settings['layer_type'] == 'ColumnLayer':
            layer = pdk.Layer(
                type=settings['layer_type'],
                data=df,
                get_position="[longitude, latitude]",
                auto_highlight=True,
                elevation_scale=settings['elevation_scale'],
                pickable=True,
                elevation_range=settings['elevation_range'],
                coverage=1,
                radius = settings['radius'],
                get_fill_color=settings['color'],
            )
        elif settings['layer_type'] == 'ScatterplotLayer':
            layer = pdk.Layer(
                type='ScatterplotLayer',
                data=df,
                pickable=True,
                get_position="[longitude, latitude]",
                radius_scale=10,
                radius_min_pixels=settings['min_rad'],
                radius_max_pixels=settings['max_rad'],
                line_width_min_pixels=1,
                get_radius=settings['get_radius'],
                get_fill_color=settings['get_fill_color'],  # [color_r, color_g, color_b]",
                get_line_color=[0, 0, 0],
            )
        elif settings['layer_type'] == 'IconLayer':
            df['icon_data'] = None
            for i in df.index:
                df['icon_data'][i] = cn.ICON_DATA
            layer = pdk.Layer(
                type="IconLayer",
                data=df,
                get_icon="icon_data",
                get_size=2,
                size_scale=15,
                get_position=["longitude", "latitude"],
                pickable=True,
            )
        view_state = pdk.ViewState(
            longitude=settings['midpoint'][1], latitude=settings['midpoint'][0], zoom=12, min_zoom=5, max_zoom=20, pitch=0, bearing=-27.36
        )
        
        r = pdk.Deck(
            map_style=cn.MAPBOX_STYLE,
            layers=[layer],
            initial_view_state=view_state,
            tooltip={
                "html": settings['tooltip_html'],
                "style": {'fontSize': cn.TOOLTIP_FONTSIZE,
                    "backgroundColor": cn.TOOLTIP_BACKCOLOR,
                    "color": cn.TOOLTIP_FORECOLOR}
            }
        )
        return r


def show_summary(conn, texts):
    def get_title():
        pass
    
    def get_filter_expression():
        pass


    @st.experimental_memo()   
    def prepare_data(_conn):    
        df_stations, ok, err_msg = db.execute_query(qry['all_stations'], _conn)
        df_stations['start_date'] = pd.to_datetime(df_stations['start_date'])
        df_stations['end_date'] = pd.to_datetime(df_stations['start_date'])
        return df_stations, ok
    
    def get_tooltip_html()->str:

        text = """
            <b>Messung-id:</b> {site_id}<br/>           
            <b>Adresse:</b> {location}<br/>
            <b>Messbeginn:</b> {start_date}<br/>
            <b>Messende:</b> {end_date}<br/>
            <b>Zone:</b> {zone}<br/>  
        """
        return text

    def get_filter_expression():
        if (zone != '<alle>') & (year  != '<alle>'):
            return f"die Messstandorte für Geschwindigkeitsmessungen im Jahr {year} in der Zone {zone}"
        elif (zone != '<alle>'):
            return f"die Messstandorte für Geschwindigkeitsmessungen in den Jahren {min_year} bis {max_year} in der Zone {zone}"
        elif (year  != '<alle>'):
            return f"die Messstandorte für Geschwindigkeitsmessungen im Jahr {year} in allen Zonen"
        else:
            return f"die Messstandorte für Geschwindigkeitsmessungen in den Jahren {min_year} bis {max_year} in allen Zonen"

        

    st.markdown("### Übersicht über die Messsationen")
    df, ok = prepare_data(conn)
    min_year = int(df['jahr'].min())
    max_year = int(df['jahr'].max())
    lst_years = [cn.ALL_EXPRESSION] + list(range(min_year, max_year + 1))
    lst_zones = helper.get_code_list(df,'zone',True,True)
    zone = st.sidebar.selectbox("Wähle eine Zone", lst_zones)
    year = st.sidebar.selectbox("Wähle ein Jahr", lst_years)
    df_filtered = df.query('jahr == @year') if year != cn.ALL_EXPRESSION else df
    df_filtered = df_filtered.query('zone == @zone') if zone != cn.ALL_EXPRESSION else df_filtered
    df_filtered = df_filtered[['longitude','latitude','site_id', 'location','zone','start_date','end_date']]
    
    df_filtered['start_date'] = df_filtered['start_date'].apply(lambda x: x.strftime ('%d.%m.%Y'))
    df_filtered['end_date'] = df_filtered['end_date'].apply(lambda x: x.strftime ('%d.%m.%Y'))
    midpoint = (np.average(df_filtered['latitude']), np.average(df_filtered['longitude']))
    settings = {'midpoint': midpoint, 'layer_type': 'IconLayer', 'tooltip_html': get_tooltip_html()}
    chart = plot_map(df_filtered, settings)
    st.pydeck_chart(chart)
    st.markdown(texts['instructions'].format(get_filter_expression()))    


def plot_barchart(df,settings):
    chart = alt.Chart(df).mark_bar().encode(
        x=settings['x'],
        y=settings['y'],
        tooltip=['hour','sum(count)']
    ).properties(
        width=settings['width'],
        height=settings['height'],
    )
    return chart


def plot_linechart(df,settings):
    chart = alt.Chart(df).mark_line().encode(
        x=settings['x'],
        y=settings['y'],
        tooltip=['hour','count']
    ).properties(
        width=settings['width'],
        height=settings['height']
    )
    return chart

@st.experimental_memo()   
def get_location_list(df:pd.DataFrame)->list:
    """
    the stations must be ranked again, since the original dataframe is aggregated by direction, so each station
    can appear twice with a different ranking. therefore the df has to be aggregated without direction, then ranked again.
    """
    groupby_fields_fields = ['site_id', 'location']
    df = df.groupby(groupby_fields_fields)['exceedance_rate'].agg(['mean']).reset_index()
    df = df.sort_values(by = 'location')
    ids = list(df['site_id'])
    vals = list(df['location'])
    return dict(zip(ids, vals))

@st.experimental_memo()   
def get_station_list(df:pd.DataFrame)->list:
    """
    the stations must be ranked again, since the original dataframe is aggregated by direction, so each station
    can appear twice with a different ranking. therefore the df has to be aggregated without direction, then ranked again.
    """
    groupby_fields_fields = ['site_id', 'location']
    df = df.groupby(groupby_fields_fields)['exceedance_rate'].agg(['mean']).reset_index()
    df['rang'] = df['mean'].rank(method='min').astype('int')
    df = df.sort_values('rang', ascending=False)
    ids = list(df['site_id'])
    vals = list(df['rang'].astype('string') + ') ' + df['location']) 
    return dict(zip(ids, vals))


def show_timemachine(conn):
    def get_figure_text(df_filtered,settings,year,week):
        return f"""Die Karte zeigt alle Messstationen mit Richtung {settings['direction']} welche in der Woche {week}, {year} Messungen ausführten. Die Grösse des Radius wird bestimmt durch den 
Parameter *{settings['rad_field']}*. Ein grosser Radius bedeutet, dass der Parameter einen Wert von {settings['max_rad_val']: .1f} und mehr hat. 
Die Farbwahl ist wie folgt definiert: 
- <span style="color:green">grün</span>: Der Wert von *{settings['rad_field']}* ist tiefer als {settings['max4green']: .1f}
- <span style="color:orange">orange</span>: Der Wert von {settings['rad_field']} liegt zwischen {settings['max4green'] :.1f} und {settings['max4orange'] :.1f}
- <span style="color:red">rot</span>: Der Wert von {settings['rad_field']} ist höher als {settings['max4orange'] :.1f}

Die Definition des Parameters *{settings['rad_field']}* findest du auf der Infoseite. Du kannst die Grenzen für die Bestimmung des Radius oder der Farben in der Seitenleiste selbst festlegen. 
"""
    
    def get_colors(df,settings):
        def calc_rgb_color(clr, value):
            fld = settings['color_field']
            settings['max4green'] = df[fld].mean() 
            settings['max4orange'] = df[fld].mean() + 2 * df[fld].std()
            result = 0
            if (clr == 'red') & (value > settings['max4green']):
                result = 255
            elif clr == 'green':
                if value <= settings['max4green']:
                    result = 255
                elif value <= settings['max4orange']:
                    result = 153
            return result

        for clr in ['red','green']:
            df[clr] = df.apply(lambda x: calc_rgb_color(clr,x[settings['color_field']]), axis=1)

        return df

    def get_tooltip_html():
        return """
            <b>Messung-id:</b> {site_id}<br/>
            <b>Adresse:</b> {location}<br/>
            <b>Richtung:</b> {direction_street}<br/>
            <b>Messbeginn:</b> {start_date}<br/>
            <b>Messende:</b> {end_date}<br/>
            <b>Übertretungsquote:</b> {exceedance_rate}<br/>
            <b>Zone:</b> {zone}<br/>  
            <b>V50:</b> {v50}<br/>
            <b>V85:</b> {v85}<br/>
            <b>V50 - Zone:</b> {diff_v50}<br/>
            <b>V85 - Zone:</b> {diff_v85}<br/>
            <b>V50 - Zone%:</b> {diff_v50_perc}<br/>
            <b>V85 - Zone%:</b> {diff_v85_perc}<br/>
        """

    def get_radius(df, settings):
        fld = settings['rad_field']
        settings['max_rad_val'] = df[fld].mean() + 2 * df[fld].std()
        df['radius'] = df[fld] / settings['max_rad_val'] * settings['max_rad']
        df['radius'] = df.apply(lambda x: x['radius'] if x['radius'] <= settings['max_rad'] else settings['max_rad'], axis=1)
        df['radius'] = df.apply(lambda x: x['radius'] if x['radius'] > settings['min_rad'] else settings['min_rad'], axis=1)
        return df

    @st.experimental_memo()          
    def prepare_map_data(_conn, settings):
        def add_calculated_fields(df):
            df['latitude']=df['latitude'].astype('float')
            df['longitude']=df['longitude'].astype('float')
            df['woche'] = df['date_time'].dt.isocalendar().week
            df['jahr'] = df['date_time'].dt.year      
            groupby_fields_fields = ['site_id', 'direction','direction_street','jahr','woche','zone','latitude','longitude','v50','v85','vehicles','exceedance_rate','messbeginn','messende']
            df = df.groupby(groupby_fields_fields)['velocity'].agg(['max','count']).reset_index()
            df = df.rename(columns = {'max': 'max_velocity', 'count':'anz'})
            df['diff_v50'] = ( df['v50'] - df['zone']) 
            df['diff_v85'] = ( df['v85'] - df['zone']) 
            df['diff_v50_perc'] = df['diff_v50'] / 100
            df['diff_v85_perc'] = df['diff_v85'] / df['zone'] * 100
            df['red'] = 0
            df['green'] = 0
            df['blue'] = 0

            return df

        df, ok = db.execute_query(qry['all_violations'], _conn)
        if ok:
            df = add_calculated_fields(df)
            if 'rank_param' in settings:
                df['rang'] = df[settings['rank_param']].rank(method='min').astype('int')

        return df, ok        
    

    def init_settings():
        settings = {'layer_type':'ScatterplotLayer', 
        'tooltip_html':get_tooltip_html(), 
        'min_rad':4, 
        'max_rad':30, 
        'get_radius':'radius',
        'get_fill_color':'[red, green, blue, 80]'}

        settings['direction'] = st.sidebar.selectbox("Richtung:", [1,2])
        settings['rad_field'] = st.sidebar.selectbox("Symbole mit Grösse proportional zu Feld:", lst_group_fields)
        settings['color_field'] = st.sidebar.selectbox("Symbole mit Farbe bestimmt durch Feld:", lst_group_fields)
        return settings

    settings = init_settings()
    df, ok = prepare_map_data(conn, settings)
    map_placeholder = st.empty()
    slider_placeholder = st.empty()
    text_placeholder = st.empty()

    settings['midpoint'] = (np.average(df['latitude']), np.average(df['longitude']))
    
    df_year_week = df[['woche','jahr']].drop_duplicates()
    df_year_week['label'] = df["jahr"].apply(str) + "-" + df["woche"].apply(str)
    df_year_week = df_year_week.set_index('label').sort_index()
    time = slider_placeholder.select_slider('Wähle Woche und Jahr', options=list(df_year_week.index))
    week = df_year_week.loc[time]['woche']
    year = df_year_week.loc[time]['jahr']
    df_filtered = df.query(f"(woche == @week) & (jahr == @year) & (direction == {settings['direction']})")
    df_filtered = get_radius(df_filtered, settings)
    df_filtered = get_colors(df_filtered, settings)

    # st.write(df_filtered)
    if len(df_filtered) > 0:
        chart = plot_map(df_filtered, settings)
        map_placeholder.pydeck_chart(chart)
        text_placeholder.markdown(get_figure_text(df_filtered,settings,year,week),unsafe_allow_html=True)


def show_ranking(conn):
    def explain(df_filtered,settingsm, ranks):
        if len(df_filtered) > 0:
            par = cn.PARAMETERS_DIC[settings['rank_param']]['label']
            val_from = df_filtered.iloc[0][settings['rank_param']]
            val_to = df_filtered.iloc[-1][settings['rank_param']]
            unit = cn.PARAMETERS_DIC[settings['rank_param']]['unit']
            return f"""Die Karte zeigt die Position aller Messstationen mit den Rängen {ranks[0]} bis {ranks[-1]}. Die Rangliste erfolgt nach Parameter *{par}*. 
Dieser variiert in der Rangauswahl von {val_from:.1f} bis {val_to:.1f}{unit}. Rang 1 entspricht 
der Messstation mit dem tiefsten Wert für Parameter *{par}*. Du findest die Definition aller Parameter auf der Infoseite. 
            """
        else:
            return ''

    @st.experimental_memo()   
    def prepare_map_data(_conn, settings):
        def add_calculated_fields(df):
            """[summary]

            Args:
                df ([type]): [description]

            Returns:
                [type]: [description]
            """   
            
            df = helper.set_column_types(df)
            df = helper.format_time_columns(df, ('start_date', 'end_date'), '%d.%b %Y')
            # df = df.rename(columns = {'max': 'max_velocity'})
            df['diff_v50'] = ( df['v50'] - df['zone']) 
            df['diff_v85'] = ( df['v85'] - df['zone']) 
            df['diff_v50_perc'] = df['diff_v50'] / 100
            df['diff_v85_perc'] = df['diff_v85'] / df['zone'] * 100
            return df

        df, ok, err_msg = db.execute_query(qry['velocity_by_station'], _conn)     
        df = add_calculated_fields(df)   
        return df, ok        

    def get_tooltip_html():
        return """
            <b>Messung-id:</b> {site_id}<br/>
            <b>Adresse:</b> {address}<br/>
            <b>Richtung:</b> {direction_street}<br/>
            <b>Messbeginn:</b> {start_date}<br/>
            <b>Messende:</b> {end_date}<br/>
            <b>Übertretungsquote:</b> {exceedance_rate}<br/>
            <b>Zone:</b> {zone}<br/>  
            <b>V50:</b> {v50}<br/>
            <b>V85:</b> {v85}<br/>
            <b>V50 - Zone:</b> {diff_v50}<br/>
            <b>V85 - Zone:</b> {diff_v85}<br/>
            <b>V50 - Zone%:</b> {diff_v50_perc}<br/>
            <b>V85 - Zone%:</b> {diff_v85_perc}<br/>
        """

    def init_settings():
        """[summary]

        Returns:
            [type]: [description]
        """        """"""
        settings = {'layer_type':'IconLayer', 
        'tooltip_html':get_tooltip_html(), 
        }

        settings['rank_param'] = st.sidebar.selectbox('Wähle Parameter für die Rangliste', lst_group_fields)
        return settings

    def get_title(df,settings, ranks):
        par = cn.PARAMETERS_DIC[settings['rank_param']]['label']
        text = f"#### Messstationen geordnet nach Parameter *{par}*\n Ränge {ranks[0]} bis {ranks[1]}" 
        return text

    # start
    settings = init_settings()
    df_station, ok = prepare_map_data(conn, settings)
    df_station = helper.set_column_types(df_station)
    df_station = helper.format_time_columns(df_station, ('start_date', 'end_date'), cn.FORMAT_DMY)
    df_station['rang'] = df_station[settings['rank_param']].rank(method='min').astype('int')
    df_station = df_station.sort_values('rang')
    settings['midpoint'] = (np.average(df_station['latitude']), np.average(df_station['longitude']))
    max_rank = int(df_station['rang'].max())
    ranks = st.sidebar.slider('Rang', 1,max_rank,(1,10))
    df_filtered = df_station.query(f"(rang >= @ranks[0]) & (rang <= @ranks[1])")
    if len(df_filtered) > 0:
        st.markdown(get_title(df_filtered, settings, ranks),unsafe_allow_html=True)
        chart = plot_map(df_filtered, settings)
        st.pydeck_chart(chart)
        st.markdown(explain(df_filtered,settings,ranks),unsafe_allow_html=True)


def show_station_analysis(conn):
    @st.experimental_memo(suppress_st_warning=True)   
    def prepare_map_data(_conn):
        sql = qry['all_stations']
        df, ok, err_msg = db.execute_query(sql, _conn)
        df = helper.add_calculated_fields(df)
        df = helper.set_column_types(df)
        df = helper.format_time_columns(df, ('start_date', 'end_date'), '%d.%b %Y')
        return df, ok     

    def get_velocity_data(site_id, _conn):
        sql = qry['station_velocities'].format(site_id)
        df, ok, err_msg = db.execute_query(sql, _conn)
        return df, ok           

    def get_tooltip_html():
        return ""

    def init_settings():
        settings = {'layer_type':'IconLayer', 
        'tooltip_html':get_tooltip_html(), 
        }

        settings['width'] = 400
        settings['height'] = 400
        
        return settings

    def show_plots(df_velocities, dic_station):
        if len(df_velocities) > 0:
            settings['x'] = alt.X("date_time:T", axis=alt.Axis(title='', format = ("%d.%m %y")))
            settings['y'] = alt.Y("count:Q", axis=alt.Axis(title='Übertretungen/h'))
            #station_id = dic_station['id']
            st.write(f"Richtung {dic_station['direction']}: {dic_station['direction_street']}")
            st.write('Zeitlicher Verlauf, Anzahl Geschwindigkeitsüberschreitungen (pro Stunde)')
            chart = plot_linechart(df_velocities,settings)
            st.altair_chart(chart)

            st.write('Anzahl Geschwindigkeitsüberschreitungen aggregiert nach Tageszeit')
            settings['x'] = alt.X("hour:O", axis=alt.Axis(title=cn.PARAMETERS_DIC['hour']['label']))
            settings['y'] = alt.Y("sum(count):Q", axis=alt.Axis(title=cn.PARAMETERS_DIC['count_exc']['label']))
            chart = plot_barchart(df_velocities,settings)
            st.altair_chart(chart)

            df_velocities = helper.replace_day_ids(df_velocities, 'dow')
            st.write('Anzahl Geschwindigkeitsüberschreitungen aggregiert nach Wochentag')
            settings['x'] = alt.X("dow:O", axis=alt.Axis(title=''), sort=cn.WOCHE)
            settings['y'] = alt.Y("sum(count):Q", axis=alt.Axis(title=cn.PARAMETERS_DIC['count_exc']['label']))
            chart = plot_barchart(df_velocities,settings)
            st.altair_chart(chart)
        else:
            st.write(f"keine Daten für Richtung {dic_station['direction']}")

    def get_station_title(df_station):
        x = df_station.iloc[0].to_dict()
        return f"### Messtation {x['site_id']} {x['location']} \nvon {x['start_date']} bis {x['end_date']}"
    
    title_placeholder = st.empty()
    settings = init_settings()
    df_stations, ok = prepare_map_data(conn)
    location_dic =  get_location_list(df_stations)
    site_id = st.selectbox('Wähle Messstation', list(location_dic.keys()),
        format_func=lambda x: location_dic[x])   
    settings['midpoint'] = (np.average(df_stations['latitude']), np.average(df_stations['longitude']))
    df_station = df_stations.query('site_id == @site_id')
    df_velocities, ok = get_velocity_data(site_id, conn)

    title_placeholder.markdown(get_station_title(df_station))
    if len(df_station) > 0:
        chart = plot_map(df_station, settings)
        st.pydeck_chart(chart)
        col1, col2 = st.columns(2)
        with col1:
            dic_station = df_station.query('(site_id == @site_id) & (direction == 1)')
            if len(dic_station) > 0:
                dic_station = dic_station.iloc[0].to_dict()
                df_filtered = df_velocities.query(f"station_id == {dic_station['station_id']}")
                show_plots(df_filtered, dic_station)
        with col2:
            dic_station = df_station.query('(site_id == @site_id) & (direction == 2)')
            if len(dic_station)>0:
                dic_station = dic_station.iloc[0].to_dict()
                df_filtered = df_velocities.query(f"station_id == {dic_station['station_id']}")
                show_plots(df_velocities, dic_station)

def show_menu(texts, conn):    
    menu_item = st.sidebar.selectbox('Optionen', texts['menu_options'])
    if menu_item == texts['menu_options'][0]:
        show_summary(conn, texts)
    elif menu_item ==  texts['menu_options'][1]:
        show_ranking(conn)
    elif menu_item ==  texts['menu_options'][2]:
        show_station_analysis(conn)
                
