# from sqlite3.dbapi2 import Timestamp
# from numpy.random.mtrand import random_integers
import streamlit as st
import altair as alt
import pandas as pd
import pydeck as pdk
import numpy as np
# import random
from queries import qry

import const as cn
import database as db
import helper

lst_group_fields = ['uebertretungsquote', 'diff_v50_perc', 'diff_v85_perc', 'anz', 'fahrzeuge']

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

    @st.experimental_memo()   
    def prepare_data(_conn):    
        df_stations, ok, err_msg = db.execute_query(qry['all_stations'], _conn)
        df_stations['start_date'] = pd.to_datetime(df_stations['start_date'])
        df_stations['end_date'] = pd.to_datetime(df_stations['start_date'])
        return df_stations, ok
    
    def get_tooltip_html()->str:

        text = """
            <b>Messung-id:</b> {messung_id}<br/>           
            <b>Adresse:</b> {address}<br/>
            <b>Messbeginn:</b> {start_date}<br/>
            <b>Messende:</b> {end_date}<br/>
            <b>Zone:</b> {zone}<br/>  
            <b>Länge:</b> {longitude}<br/>
            <b>Breite:</b> {latitude}<br/>
        """
        return text

    df, ok = prepare_data(conn)
    min_year = int(df['jahr'].min())
    max_year = int(df['jahr'].max())
    all_expression = '<alle>'
    lst_years = [all_expression] + list(range(min_year, max_year + 1))
    lst_zones = [all_expression] + list(df['zone'].unique())
    zone = st.sidebar.selectbox("Wähle eine Zone", lst_zones)
    year = st.sidebar.selectbox("Wähle ein Jahr", lst_years)
    df_filtered = df.query('jahr == @year') if year != all_expression else df
    df_filtered = df.query('zone == @zone') if zone != all_expression else df_filtered
    df_filtered = df_filtered[['longitude','latitude','messung_id', 'address','zone','start_date','end_date']]
    
    df_filtered['start_date'] = df_filtered['start_date'].apply(lambda x: x.strftime('%d.%m.%Y'))
    df_filtered['end_date'] = df_filtered['end_date'].apply(lambda x: x.strftime('%d.%m.%Y'))
    midpoint = (np.average(df_filtered['latitude']), np.average(df_filtered['longitude']))
    settings = {'midpoint': midpoint, 'layer_type': 'IconLayer', 'tooltip_html': get_tooltip_html()}
    chart = plot_map(df_filtered, settings)
    st.pydeck_chart(chart)
    st.markdown(texts['instructions'].format(min_year, max_year))    


def plot_barchart(df,settings):
    chart = alt.Chart(df).mark_bar().encode(
        x=settings['x'],
        y=settings['y'],
        tooltip=['hour','sum(anz)']
    ).properties(
        width=settings['width'],
        height=settings['height'],
    )
    return chart


def plot_linechart(df,settings):
    chart = alt.Chart(df).mark_line().encode(
        x=settings['x'],
        y=settings['y'],
        tooltip=['zeit','anz']
    ).properties(
        width=settings['width'],
        height=settings['height']
    )
    return chart

@st.experimental_memo()   
def get_station_list(df:pd.DataFrame)->list:
    """
    the stations must be ranked again, since the original dataframe is aggregated by direction, so each station
    can appear twice with a different ranking. therefore the df has to be aggregated without direction, then ranked again.
    """
    groupby_fields_fields = ['messung_id', 'address','ort']
    df = df.groupby(groupby_fields_fields)['uebertretungsquote'].agg(['mean']).reset_index()
    df['rang'] = df['mean'].rank(method='min').astype('int')
    df = df.sort_values('rang', ascending=False)
    ids = list(df['messung_id'])
    vals = list(df['rang'].astype('string') + ') ' + df['address'] + ' ' + df['ort']) 
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
            <b>Messung-id:</b> {messung_id}<br/>
            <b>Länge:</b> {longitude}<br/>
            <b>Breite:</b> {latitude}<br/>
            <b>Adresse:</b> {address}<br/>
            <b>Richtung:</b> {richtung_strasse}<br/>
            <b>Messbeginn:</b> {start_date}<br/>
            <b>Messende:</b> {end_date}<br/>
            <b>Übertretungsquote:</b> {uebertretungsquote}<br/>
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
            df['date_time'] = pd.to_datetime(df['date_time'], format="%d.%m.%y %H:%M:%S")
            df['latitude']=df['latitude'].astype('float')
            df['longitude']=df['longitude'].astype('float')
            df['woche'] = df['date_time'].dt.isocalendar().week
            df['jahr'] = df['date_time'].dt.year      
            groupby_fields_fields = ['messung_id', 'richtung','richtung_strasse','jahr','woche','zone','latitude','longitude','v50','v85','fahrzeuge','uebertretungsquote','messbeginn','messende']
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
    df_filtered = df.query(f"(woche == @week) & (jahr == @year) & (richtung == {settings['direction']})")
    df_filtered = get_radius(df_filtered, settings)
    df_filtered = get_colors(df_filtered, settings)

    # st.write(df_filtered)
    if len(df_filtered) > 0:
        chart = plot_map(df_filtered, settings)
        map_placeholder.pydeck_chart(chart)
        text_placeholder.markdown(get_figure_text(df_filtered,settings,year,week),unsafe_allow_html=True)


def show_ranking(conn):
    def explain(df_filtered,settingsm, rank):
        if len(df_filtered) > 0:
            dic = df_filtered.iloc[0].to_dict()
            return f"""Die Karte zeigt die Position von Messtation {dic['messung_id']} mit Rang {rank[0]} bis {rank[0]}. Die Rangliste erfolgt nach Parameter {settings['rank_param']}. 
*{settings['rank_param']}* variiert in der Rangauswahl von {df_filtered.iloc[0][settings['rank_param']]} bis {df_filtered.iloc[-1][settings['rank_param']]}. Die Definition des Parameters *{settings['rank_param']}* findest du auf der Infoseite. 
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
            df = df.rename(columns = {'max': 'max_velocity', 'count':'anz'})
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
            <b>Messung-id:</b> {messung_id}<br/>
            
            <b>Adresse:</b> {address}<br/>
            <b>Richtung:</b> {richtung_strasse}<br/>
            <b>Messbeginn:</b> {start_date}<br/>
            <b>Messende:</b> {end_date}<br/>
            <b>Übertretungsquote:</b> {uebertretungsquote}<br/>
            <b>Zone:</b> {zone}<br/>  
            <b>V50:</b> {v50}<br/>
            <b>V85:</b> {v85}<br/>
            <b>V50 - Zone:</b> {diff_v50}<br/>
            <b>V85 - Zone:</b> {diff_v85}<br/>
            <b>V50 - Zone%:</b> {diff_v50_perc}<br/>
            <b>V85 - Zone%:</b> {diff_v85_perc}<br/>
            <b>Länge:</b> {longitude}<br/>
            <b>Breite:</b> {latitude}<br/>
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
    
    # start
    settings = init_settings()
    df, ok = prepare_map_data(conn, settings)
    df['rang'] = df[settings['rank_param']].rank(method='min').astype('int')
    df = df.sort_values('rang')

    settings['midpoint'] = (np.average(df['latitude']), np.average(df['longitude']))
    max_rank = int(df['rang'].max())
    rank = st.sidebar.slider('Rang', 1,max_rank,(1,10))
    df_filtered = df.query(f"(rang >= @rank[0]) & (rang <= @rank[1])")
    if len(df_filtered) > 0:
        chart = plot_map(df_filtered, settings)
        st.pydeck_chart(chart)
        st.markdown(explain(df_filtered,settings,rank),unsafe_allow_html=True)


def show_station_analysis(conn):
    def explain(df_filtered,settings):
        if len(df_filtered) == 1:
            dic = df_filtered.iloc[0].to_dict()
            return f"""Die Karte zeigt die Position von Messtation {dic['messung_id']} mit Rang {dic['rang']} Die Rangliste erfolgt nach Parameter {settings['rank_param']}. 
Die Definition des Parameters *{settings['rank_param']}* findest du auf der Infoseite. 
            """
        else:
            return ''

    @st.experimental_memo(suppress_st_warning=True)   
    def prepare_map_data(_conn):
        def add_calculated_fields(df):
            df['date_time'] = pd.to_datetime(df['date_time'], format="%d.%m.%y %H")
            df['latitude']=df['latitude'].astype('float')
            df['longitude']=df['longitude'].astype('float')
            
            groupby_fields_fields = ['messung_id', 'ort', 'address', 'richtung','richtung_strasse','zone','latitude','longitude','v50','v85','fahrzeuge','uebertretungsquote','start_date','end_date']
            df = df.groupby(groupby_fields_fields)['velocity_kmph'].agg(['max','count']).reset_index()
            df = df.rename(columns = {'max': 'max_velocity', 'count':'anz'})
            df['diff_v50'] = ( df['v50'] - df['zone']) 
            df['diff_v85'] = ( df['v85'] - df['zone']) 
            df['diff_v50_perc'] = df['diff_v50'] / 100
            df['diff_v85_perc'] = df['diff_v85'] / df['zone'] * 100
            return df

        def group_by_hour(_df):
            """
            aggregates all violations to hourly values used to drawthe time series 
            """
            _df['hour'] = _df['date_time'].dt.hour  
            groupby_fields_fields = ['messung_id', 'richtung','richtung_strasse','date_time','hour','zone','latitude','longitude','v50','v85','fahrzeuge','uebertretungsquote','start_date','end_date']
            _df = _df.groupby(groupby_fields_fields)['velocity_kmph'].agg(['max','count']).reset_index()
            _df = _df.rename(columns = {'max': 'max_velocity', 'count':'anz', 'date_time':'zeit'})
            return _df

        df, ok = db.execute_query(qry['all_violations'], _conn)
        df = add_calculated_fields(df)   
        
        return df, ok        

    def get_tooltip_html():
        return ""

    def init_settings():
        settings = {'layer_type':'IconLayer', 
        'tooltip_html':get_tooltip_html(), 
        }

        settings['rank_param'] = st.sidebar.selectbox('Wähle Parameter für die Rangliste', lst_group_fields)
        settings['width'] = 400
        settings['height'] = 400
        
        return settings

    def show_plots(richtung, station):
        df = df_all_violations.query('(messung_id==@station) & (richtung==@richtung)')
        
        if len(df) > 0:
            settings['x'] = alt.X("zeit:T")
            settings['y'] = alt.Y("anz:Q")
            rec = df_filtered.query('richtung == @richtung').iloc[0].to_dict()
            st.write(f"Richtung {rec['richtung']}, {rec['richtung_strasse']}")
            st.write('Zeitlicher Verlauf, Anzahl Geschwindkeitsüberschreitungen')
            chart = plot_linechart(df,settings)
            st.altair_chart(chart)
            
            st.write('Anzahl Geschwindkeitsüberschreitungen aggregiert nach Tageszeit über Messperiode')
            settings['x'] = alt.X("hour:O")
            settings['y'] = alt.Y("sum(anz):Q")
            chart = plot_barchart(df,settings)
            st.altair_chart(chart)
        else:
            st.write(f'keine Daten für Richtung {richtung}')

    def get_station_title():
        x = df_filtered.iloc[0].to_dict()
        return f"### Messtation {x['messung_id']} {x['address']}, von: {x['start_date']} bis: {x['end_date']}"
    
    settings = init_settings()
    df, ok = prepare_map_data(conn)
    # st.write(df.head())
    df['rang'] = df[settings['rank_param']].rank(method='min').astype('int')

    station_dic =  get_station_list(df)
    station = st.sidebar.selectbox('Wähle Messstation', list(station_dic.keys()),
        format_func=lambda x: station_dic[x])   
    settings['midpoint'] = (np.average(df['latitude']), np.average(df['longitude']))
    
    df_filtered = df.query(f"messung_id == @station")
    st.markdown(get_station_title())
    if len(df_filtered) > 0:
        chart = plot_map(df_filtered, settings)
        st.pydeck_chart(chart)
        col1, col2 = st.columns(2)
        with col1:
            show_plots(1, station)
        with col2:
            show_plots(2,station)
                
        st.markdown(explain(df_filtered,settings),unsafe_allow_html=True)

def show_menu(texts, conn):    
    menu_item = st.sidebar.selectbox('Optionen', texts['menu_options'])
    if menu_item == texts['menu_options'][0]:
        show_summary(conn, texts)
    elif menu_item ==  texts['menu_options'][1]:
        show_ranking(conn)
    elif menu_item ==  texts['menu_options'][2]:
        st.info("Habe etwas Geduld, das wird bald auch funktionieren 🚀")
        # show_station_analysis(conn)
                
