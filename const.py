import os
import socket

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
PARAMETERS_DIC = {'uebertretungsquote':'Überteretungsquote'}

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