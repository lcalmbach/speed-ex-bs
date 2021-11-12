import os
import socket

MENU = ['Info','Karte','Statistik']
# parameters

PARAMETERS_DIC = {
    'exceedance_rate': {'label': 'Übertretungsquote', 'unit': '%', 'type': 'float'},
    'v50': {'label': 'V50', 'unit': 'km/h', 'type': 'float'},
    'v85': {'label': 'V85', 'unit': 'km/h', 'type': 'float'},
    'vehicles': {'label': 'Fahrzeuge', 'unit': '', 'type': 'int'},
    'site_id': {'label': 'Messung_ID', 'unit': '', 'type': 'int'},    
    'address': {'label': 'Adresse', 'unit': '', 'type': 'str'},  
    'location': {'label': 'Ort', 'unit': '', 'type': 'str'},  
    'zone': {'label': 'Zone', 'unit': '', 'type': 'str'},  
    'direction': {'label': 'Richtung', 'unit': '', 'type': 'int'},  
    'direction_street': {'label': 'Richtung-Strasse', 'unit': '', 'type': 'str'},  
    'start_date': {'label': 'Messbeginn', 'unit': '', 'type': 'date'},  
    'end_date': {'label': 'Messende', 'unit': '', 'type': 'date'},  
    'hour': {'label': 'Tageszeit', 'unit': '', 'type': 'str'},  
    'weekday': {'label': 'Wochentag', 'unit': '', 'type': 'str'},  
    'year': {'label': 'Jahr', 'unit': '', 'type': 'int'},  
    'count_exc': {'label': 'Anzahl Übertretungen', 'unit': '', 'type': 'int'},  
    'latitude': {'label': 'Länge', 'unit': '', 'type': 'float'},  
    'longitude': {'label': 'Breite', 'unit': '', 'type': 'float'},  
    'diff_v50': {'label': 'Diff-V50', 'unit': '', 'type': 'float'},  
    'diff_v85': {'label': 'Diff-V85', 'unit': '', 'type': 'float'},  
    'diff_v50_perc': {'label': 'Diff-V50%', 'unit': '%', 'type': 'float'},  
    'diff_v85_perc': {'label': 'Diff-V50%', 'unit': '%', 'type': 'float'},  
    'station_id': {'label': 'Station-ID', 'unit': '', 'type': 'int'},  
}
# files
TEXTS = './texts.json'
QUERIES = './queries.json'

# pydeck chart settings
MAP_LEGEND_SYMBOL_SIZE: int = 10
MAPBOX_STYLE: str = "mapbox://styles/mapbox/light-v10"
GRADIENT: str = 'blue-green'
TOOLTIP_FONTSIZE = 'x-small'
TOOLTIP_BACKCOLOR = 'white'
TOOLTIP_FORECOLOR = 'black'
ICON_DATA = {"url": "https://img.icons8.com/plasticine/100/000000/marker.png","width": 128,"height": 128,"anchorY": 128}
#ICON_DATA = {"url": "https://img.icons8.com/material-outlined/24/000000/camera--v2.png","width": 128,"height": 128,"anchorY": 128}

# database settings on heroku
DEV_MACHINES = ('liestal')
if socket.gethostname().lower() in DEV_MACHINES:
    DB_USER = "postgres"
    DB_PASS = 'password'
    DB_HOST = 'localhost' 
    DB_DATABASE = 'velox'
    DB_PORT = "5432"
else:
    DB_USER = "dxkqwxlfbaffnk"
    DB_PASS = os.environ.get('DB_PASS') # read from system variables when on heroku
    DB_HOST = 'ec2-54-216-17-9.eu-west-1.compute.amazonaws.com'
    DB_DATABASE = 'd3f49ft1g3uc8t'
    DB_PORT = "5432"

FORMAT_DMY = '%d.%m.%Y'
FORMAT_DBY = '%d. %b %Y'
WOCHE = ['Montag','Dienstag','Mittwoch','Donnerstag','Freitag','Samstag','Sonntag']
WEEKDAY4ID = ['Sonntag','Montag','Dienstag','Mittwoch','Donnerstag','Freitag','Samstag']
ALL_EXPRESSION = '<alle>'